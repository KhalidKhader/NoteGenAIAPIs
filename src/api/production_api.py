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

import json
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks

from src.core.logging import logger
from src.core.observability import get_langfuse_handler, flush_langfuse_data
from src.core.config import settings
from src.models.api_models import (
    EncounterRequestModel,
    JobAcknowledgementResponse,
)
from src.services.opensearch_rag import ConversationRAGService, get_conversation_rag_service
from src.services.neo4j_snomed_rag import SNOMEDRAGService, get_snomed_rag_service
from src.services.azure_openai import MedicalSectionGenerator, get_soap_generator_service
from src.services.notegen_api import NotegenAPIService, get_notegen_api_service
from src.services.patient_info import PatientInfoService, get_patient_info_service

router = APIRouter()

# In-memory job tracking
production_jobs: Dict[str, Dict[str, Any]] = {}

async def _run_encounter_processing_pipeline(
    request: EncounterRequestModel,
    job_id: str,
    logger
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
        
        # Get patient info service if needed
        patient_info_service: PatientInfoService = None
        if request.patientInfo:
            patient_info_service = await get_patient_info_service()

        # STEP 3: Store conversation and get chunk IDs
        logger.info("Storing and chunking conversation.")
        await convo_rag.store_and_chunk_conversation(
            encounterTranscript=request.encounterTranscript,
            conversation_id=encounter_id,
            doctor_id=request.doctorId,
            language=request.language,
            logger=logger
        )
        
        # STEP 3.1: Extract and send patient info if requested
        if request.patientInfo and patient_info_service:
            logger.info("Extracting patient information.")
            patient_info_result = await patient_info_service.extract_and_send_patient_info(
                encounter_id=encounter_id,
                encounter_transcript=request.encounterTranscript,
                language=request.language,
                clinic_id=request.clinicId,
                logger=logger,
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
        
        all_medical_terms = await section_generator.extract_medical_terms_with_llm(
            full_transcript_text, 
            request.language, 
            logger,
            langfuse_handler=langfuse_handler,
            conversation_id=encounter_id
        )
        
        # STEP 5: Get comprehensive SNOMED context once
        snomed_context = await snomed_rag.get_snomed_mappings_for_terms(
            all_medical_terms, request.language, logger
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
            retrieval_query = f"Information for {section_name}: {section_to_generate.prompt}"
            context_chunks = await convo_rag.retrieve_relevant_chunks(encounter_id, retrieval_query)
            context_text = "\\n".join([chunk['content'] for chunk in context_chunks])
            logger.warning(f"Retrieved {len(context_chunks)} chunks for '{section_name}'.")

            # B. Generate the section with built-in retry logic
            generation_result = await section_generator.generate_section_with_retry(
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
                logger=logger,
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
                logger=logger
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
                            "confidence_score": generation_result.confidence_score,
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

@router.post(
    "/generate-notes",
    response_model=JobAcknowledgementResponse,
    summary="Generate Notes from NoteGen API (Main Endpoint)",
    description="""
    This is the main endpoint that the NoteGen API backend calls to generate medical notes.
    It processes the encounter and sends sections back to the NoteGen API backend as they're completed.
    All LLM requests are automatically traced with Langfuse for observability.
    """
)
async def generate_notes(
    request: EncounterRequestModel,
    background_tasks: BackgroundTasks
) -> JobAcknowledgementResponse:
    """
    Main endpoint for NoteGen API backend integration. Generates notes and sends them back to the backend.
    This endpoint matches the expected flow from the story requirements.
    
    Features:
    - Full Langfuse observability for all LLM requests
    - Real-time section delivery to NoteGen API backend
    - Comprehensive medical logging and tracing
    - SNOMED validation and doctor preferences
    """
    job_id = f"notes_{request.encounterId}_{str(uuid.uuid4())[:8]}"
    
    logger.info(f"Starting notes generation job {job_id} for encounter {request.encounterId}")

    production_jobs[job_id] = {"status": "QUEUED"}
    
    background_tasks.add_task(
        _run_encounter_processing_pipeline,
        request=request,
        job_id=job_id,
        logger=logger
    )
    
    return JobAcknowledgementResponse(
        job_id=job_id,
        status="QUEUED",
        encounter_id=request.encounterId,
        message="Encounter processing has been queued."
    )

@router.get(
    "/extract/jobs/{job_id}/status",
    summary="Get Encounter Processing Job Status",
    description="Get the status of a background encounter processing job."
)
async def get_job_status(job_id: str):
    """
    Retrieves the current status of a given processing job.
    """
    job = production_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job