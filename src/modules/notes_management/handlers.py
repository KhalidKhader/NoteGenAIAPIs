"""
Production API for NoteGen AI APIs - COMPLETE 6-STEP WORKFLOW.

PRODUCTION-READY endpoints for medical conversation processing:
1. Store full conversation into OpenSearch AWS vector DB (no manipulation)
2. Map medical terms into Neo4j RAG graph DB  
3. Check doctor preferences and apply to prompts
4. Generate medical sections based on prompts array (DYNAMIC - any section type)
5. Save sections in generated_notes folder with comprehensive logging
6. Complete workflow with final summary and logging

Handles ANY section type dynamically based on prompts array - not just SOAP!
"""

import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from src.core.settings.logging import logger
from src.core.settings.observability import get_langfuse_handler, flush_langfuse_data
from src.core.settings.config import settings
from .schema import (
    EncounterRequestModel,
    JobAcknowledgementResponse,
)
from .services import get_snomed_rag_service, SNOMEDRAGService, get_soap_generator_service, MedicalSectionGenerator, get_conversation_rag_service, ConversationRAGService
from src.services.notegen import get_notegen_api_service, NotegenAPIService, get_patient_info_service, PatientInfoService
from src.core.azure_openai.generate_section import generate_section
from src.core.aws.set_current_collection import set_current_collection
from src.core.aws.retrieve_relevant_chunks import retrieve_relevant_chunks
from src.core.aws.store_and_chunk_conversation import store_and_chunk_conversation
from src.core.neo4j.get_snomed_mappings_for_terms import get_snomed_mappings_for_terms

router = APIRouter()

# In-memory job tracking - shared between router and handlers
production_jobs: Dict[str, Dict[str, Any]] = {}

async def _run_encounter_processing_pipeline(
    request: EncounterRequestModel,
    job_id: str,
):
    """
    The main processing pipeline that runs in the background.
    """
    encounter_id = request.encounterId
    
    # Create medical logger without folder creation
    
    production_jobs[job_id]['status'] = 'PROCESSING'
    
    # Create enhanced handler for the entire pipeline with medical context.
    # This handler will be flushed at the end to ensure all data is sent.
    langfuse_handler = get_langfuse_handler(
        conversation_id=encounter_id,
        user_id=request.doctorId,
        session_id=encounter_id,
        metadata={
            "clinic_id": request.clinicId,
            "language": request.language,
            "sections_count": len(request.sections),
            "pipeline_type": "encounter_processing",
            "encounter_length": len(request.encounterTranscript),
            "model": settings.azure_openai_model,
            "deployment": settings.azure_openai_deployment_name
        }
    )
    
    try:
        logger.info(f"Starting processing pipeline for job {job_id} , encounter_id = {encounter_id}")

        # STEP 1 & 2: Get service instances
        convo_rag: ConversationRAGService = await get_conversation_rag_service()
        snomed_rag: SNOMEDRAGService = await get_snomed_rag_service()
        section_generator: MedicalSectionGenerator = await get_soap_generator_service()
        notegen_api_service: NotegenAPIService = await get_notegen_api_service()
        
        # Set the current collection for the tenant
        try:
            await set_current_collection(convo_rag, request.collection_name)
            logger.info(f"Set current collection to: {request.collection_name}")
        except Exception as e:
            error_msg = f"Failed to set collection {request.collection_name}. Please ensure a valid clinic collection name is provided. Error: {str(e)}"
            logger.error(error_msg)
            production_jobs[job_id]['status'] = 'FAILED'
            production_jobs[job_id]['error'] = error_msg
            raise HTTPException(status_code=404, detail=error_msg)

        # Get patient info service if needed
        patient_info_service: PatientInfoService = None
        if request.patientInfo:
            patient_info_service = await get_patient_info_service()

        # STEP 3: Store conversation and get chunk IDs
        logger.info("Storing and chunking conversation.")
        await store_and_chunk_conversation(
            encounterTranscript=request.encounterTranscript,
            conversation_id=encounter_id,
            doctor_id=request.doctorId,
            language=request.language,
        )
        
        # STEP 3.1: Extract and send patient info if requested
        if request.patientInfo and patient_info_service:
            logger.info("Extracting patient information.")
            patient_info_result = await patient_info_service.extract_and_send_patient_info(
                encounter_id=encounter_id,
                encounter_transcript=request.encounterTranscript,
                language=request.language,
                clinic_id=request.clinicId,
                langfuse_handler=langfuse_handler
            )
            
            if patient_info_result.get("success"):
                details={
                        "encounter_id": encounter_id,
                        "extracted_fields": list(patient_info_result.get("patient_info", {}).keys()),
                        "api_response_status": patient_info_result.get("api_response", {}).get("success"),
                        "nestjs_endpoint": "internal/encounters/patient"
                        }
                logger.info(f"Patient information extraction workflow completed successfully {details}")
            else:
                details={
                        "encounter_id": encounter_id,
                        "error": patient_info_result.get('error'),
                        "nestjs_endpoint": "internal/encounters/patient"
                        }
                
                logger.error(f"Patient information extraction workflow failed: {patient_info_result.get('error')} details = {details}")

        # STEP 4: Extract all medical terms from the full conversation once
        logger.info("Extracting all medical terms from full transcript for SNOMED mapping.")
        
        # Correctly parse the speaker-aware transcript into a simple string for term extraction
        transcript_lines = []
        for i, line_dict in enumerate(request.encounterTranscript):
            # The key is the speaker, the value is the text
            for speaker, text in line_dict.items():
                transcript_lines.append(f"Line {i+1} ({speaker}): {text}")
        
        full_transcript_text = "\\n".join(transcript_lines)
        from src.modules.ai_agents.medical_terms_extraction_agent.agent import extract_medical_terms_with_llm
        all_medical_terms = await extract_medical_terms_with_llm(
            full_transcript_text, 
            request.language, 
            langfuse_handler=langfuse_handler,
        )
        
        # STEP 5: Get comprehensive SNOMED context once
        snomed_context = await get_snomed_mappings_for_terms(
            all_medical_terms, request.language
        )
        logger.info(f"Retrieved {len(snomed_context)} SNOMED codes for the entire encounter.")

        # STEP 6: Check for doctor preferences and log them
        doctor_preferences = request.doctor_preferences
        if doctor_preferences:
            logger.info(
                f"Found {len(doctor_preferences)} preferences for doctor {request.doctorId}. details={doctor_preferences}")
        else:
            logger.warning(f"No specific preferences found for doctor {request.doctorId}.")

        # STEP 7: Process each section with retry logic
        generated_sections_context = []
        for i, section_to_generate in enumerate(request.sections):
            section_name = section_to_generate.name
            logger.info(f"Starting generation for section {i+1}/{len(request.sections)}: '{section_name}'")

            # A. Retrieve relevant context from conversation RAG
            # For medical conversations, we need comprehensive context to ensure all relevant
            # information is captured for accurate SOAP note generation
            retrieval_query = f"Information for {section_name}: {section_to_generate.prompt}"
            # Use higher k value for medical conversations to get maximum relevant context
            context_chunks = await retrieve_relevant_chunks(
                encounter_id, 
                retrieval_query, 
                k=settings.max_retrieval_chunks  # Use maximum chunks for comprehensive context
            )
            context_text = "\\n".join([chunk['content'] for chunk in context_chunks])
            logger.info(f"Retrieved {len(context_chunks)} chunks for '{section_name}' (max: {settings.max_retrieval_chunks}).")

            # B. Generate the section with built-in retry logic
            generation_result = await generate_section(
                section_id=section_to_generate.id,
                template_id=section_to_generate.templateId,
                section_name=section_name,
                section_prompt=section_to_generate.prompt,
                language=request.language,
                conversation_context_text=context_text,
                snomed_context=snomed_context,
                doctor_preferences=doctor_preferences,
                full_transcript=request.encounterTranscript,
                previous_sections_context="\\n---\\n".join(generated_sections_context),
                langfuse_handler=langfuse_handler,
                conversation_id=encounter_id,
                doctor_id=request.doctorId,
                max_attempts=3
            )
            # C. Send to NoteGen API backend with status and content
            # Determine if this is the last section
            is_last_section = (i == len(request.sections) - 1)
            
            # Send the section result (success or failure) to NoteGen API backend
            api_response = await notegen_api_service.send_section_result(
                encounter_id=encounter_id,
                section_id=section_to_generate.id,
                section_result=generation_result,
                clinic_id=request.clinicId,
                job_id=job_id,
                is_last_section=is_last_section,
            )
            
            if generation_result.status == "SUCCESS":
                # Add to context for next sections
                generated_sections_context.append(f"Section: {section_name}\\nContent: {generation_result.content}")
                
                if api_response.get("success"):
                    details={
                            "section_id": section_to_generate.id,
                            "status": "SUCCESS",
                            "attempt_count": generation_result.attempt_count,
                            "processing_time": generation_result.processing_time,
                            "is_last_section": is_last_section,
                            "api_response": api_response
                        }
                    logger.info(f"Successfully sent section '{section_name}' to NoteGen API backend details= {details}")
                else:
                    logger.error(f"Failed to send successful section '{section_name}' to NoteGen API backend: {api_response.get('error')} details={api_response}")
            else:
                details={
                        "section_id": section_to_generate.id,
                        "status": "FAILED",
                        "attempt_count": generation_result.attempt_count,
                        "processing_time": generation_result.processing_time,
                        "error_message": generation_result.errorMessage,
                        "error_trace": generation_result.error_trace,
                        "is_last_section": is_last_section,
                        "api_response": api_response
                    }
                # Section generation failed
                logger.error(f"Section '{section_name}' generation failed after {generation_result.attempt_count} attempts, details={details}")
                
                # Continue processing other sections instead of failing the entire job

        production_jobs[job_id]['status'] = 'COMPLETED'
        logger.info("Encounter processing pipeline completed successfully.")
        
    except Exception as e:
        production_jobs[job_id]['status'] = 'FAILED'
        error_message = f"Encounter processing pipeline failed: {str(e)}"
        logger.error(error_message)
        
    finally:
        # Ensure the handler is flushed to send all buffered data.
        if langfuse_handler:
            logger.info(f"Flushing Langfuse handler for encounter {encounter_id}")
            flush_langfuse_data(langfuse_handler)