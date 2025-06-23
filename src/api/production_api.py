"""
Production API for NoteGen AI APIs - COMPLETE 6-STEP WORKFLOW.

🎯 PRODUCTION-READY endpoints for medical conversation processing:
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
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks

from src.core.logging import get_logger, create_medical_logger
from src.core.observability import get_langfuse_handler
from src.core.config import settings
from src.models.api_models import (
    EncounterRequestModel,
    JobAcknowledgementResponse,
    GeneratedSection
)
from src.services.conversation_rag import ConversationRAGService, get_conversation_rag_service
from src.services.snomed_rag import SNOMEDRAGService, get_snomed_rag_service
from src.services.section_generator import MedicalSectionGenerator, get_soap_generator_service
from src.services.nestjs_integration import NestJSIntegrationService, get_nestjs_integration_service

router = APIRouter()
logger = get_logger(__name__)

# In-memory job tracking
production_jobs: Dict[str, Dict[str, Any]] = {}

async def _run_encounter_processing_pipeline(
    request: EncounterRequestModel,
    job_id: str,
):
    """
    The main processing pipeline that runs in the background.
    """
    encounter_id = request.encounterId
    output_dir = Path("generated_notes") / encounter_id
    sections_dir = output_dir / "sections"
    
    sections_dir.mkdir(parents=True, exist_ok=True)

    medical_logger = create_medical_logger(encounter_id, output_dir)
    production_jobs[job_id]['status'] = 'PROCESSING'
    
    # Create a single handler for the entire pipeline.
    # This handler will be flushed at the end to ensure all data is sent.
    langfuse_handler = get_langfuse_handler(encounter_id)
    
    try:
        medical_logger.log(f"🚀 Starting processing pipeline for job {job_id}", "INFO", details={"encounter_id": encounter_id})

        # STEP 1 & 2: Get service instances
        convo_rag: ConversationRAGService = await get_conversation_rag_service()
        snomed_rag: SNOMEDRAGService = await get_snomed_rag_service()
        section_generator: MedicalSectionGenerator = await get_soap_generator_service()
        nestjs_service: NestJSIntegrationService = await get_nestjs_integration_service()

        # STEP 3: Store conversation and get chunk IDs
        medical_logger.log("Storing and chunking conversation.", "INFO")
        await convo_rag.store_and_chunk_conversation(
            encounterTranscript=request.encounterTranscript,
            conversation_id=encounter_id,
            doctor_id=request.doctorId,
            language=request.language,
            medical_logger=medical_logger
        )

        # STEP 4: Extract all medical terms from the full conversation once
        medical_logger.log("Extracting all medical terms from full transcript for SNOMED mapping.", "INFO")
        
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
            medical_logger,
            langfuse_handler=langfuse_handler
        )
        
        # STEP 5: Get comprehensive SNOMED context once
        snomed_context = await snomed_rag.get_snomed_mappings_for_terms(
            all_medical_terms, request.language, medical_logger
        )
        medical_logger.log(f"Retrieved {len(snomed_context)} SNOMED codes for the entire encounter.", "INFO")

        # STEP 6: Check for doctor preferences and log them
        doctor_preferences = request.doctor_preferences
        if doctor_preferences:
            medical_logger.log(
                f"Found {len(doctor_preferences)} preferences for doctor {request.doctorId}.",
                "INFO",
                details=doctor_preferences
            )
        else:
            medical_logger.log(f"No specific preferences found for doctor {request.doctorId}.", "INFO")

        # STEP 7: Process each section
        generated_sections_context = []
        for i, section_to_generate in enumerate(request.sections):
            section_name = section_to_generate.name
            medical_logger.log(f"Starting generation for section {i+1}/{len(request.sections)}: '{section_name}'", "INFO")

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # A. Retrieve relevant context from conversation RAG
                    retrieval_query = f"Information for {section_name}: {section_to_generate.prompt}"
                    context_chunks = await convo_rag.retrieve_relevant_chunks(encounter_id, retrieval_query)
                    context_text = "\\n".join([chunk['content'] for chunk in context_chunks])
                    medical_logger.log(f"Attempt {attempt + 1}: Retrieved {len(context_chunks)} chunks for '{section_name}'.", "DEBUG")

                    # D. Generate the section
                    # NOTE: We pass the original, structured encounterTranscript to the generator
                    # so it can construct proper line references.
                    generated_content: GeneratedSection = await section_generator.generate_section_with_context(
                        template_id=section_to_generate.templateId,
                        section_name=section_name,
                        section_prompt=section_to_generate.prompt,
                        language=request.language,
                        conversation_context_text=context_text,
                        snomed_context=snomed_context,
                        doctor_preferences=doctor_preferences,
                        full_transcript=request.encounterTranscript,
                        previous_sections_context="\\n---\\n".join(generated_sections_context),
                        medical_logger=medical_logger,
                        langfuse_handler=langfuse_handler
                    )
                    
                    if not generated_content.content.startswith("Error:"):
                        medical_logger.log(f"✅ Successfully generated and saved section '{section_name}' on attempt {attempt + 1}.", "INFO")
                        generated_sections_context.append(f"Section: {section_name}\\nContent: {generated_content.content}")

                    # Save the generated section to a file
                    section_output_path = sections_dir / f"{section_name.replace(' ', '_')}.json"
                    with open(section_output_path, 'w', encoding='utf-8') as f:
                        json.dump(generated_content.model_dump(), f, indent=2, ensure_ascii=False)
                    
                    # Send to NestJS immediately after successful generation
                    if not generated_content.content.startswith("Error:"):
                        medical_logger.log(f"🚀 Sending section '{section_name}' to NestJS", "INFO")
                        
                        # Send the section to NestJS
                        nestjs_response = await nestjs_service.send_generated_section(
                            encounter_id=encounter_id,
                            section_id=section_to_generate.id,
                            note_content=generated_content.content,
                            clinic_id=request.clinicId,
                            job_id=job_id,
                            medical_logger=medical_logger
                        )
                        
                        if nestjs_response.get("success"):
                            medical_logger.log(
                                f"✅ Successfully sent section '{section_name}' to NestJS",
                                "INFO",
                                details=nestjs_response
                            )
                        else:
                            medical_logger.log(
                                f"❌ Failed to send section '{section_name}' to NestJS: {nestjs_response.get('error')}",
                                "ERROR",
                                details=nestjs_response
                            )
                        
                        break
                
                except Exception as e:
                    medical_logger.log(
                        f"Attempt {attempt + 1}/{max_retries} to generate section '{section_name}' failed: {e}",
                        "WARNING",
                        details={"error": str(e)}
                    )
                    if attempt + 1 == max_retries:
                        medical_logger.log(f"💀 All {max_retries} attempts failed for section '{section_name}'.", "ERROR")
                        # Propagate the exception to fail the job
                        raise e

        production_jobs[job_id]['status'] = 'COMPLETED'
        medical_logger.log("✅ Encounter processing pipeline completed successfully.", "INFO")
        
    except Exception as e:
        production_jobs[job_id]['status'] = 'FAILED'
        error_message = f"Encounter processing pipeline failed: {str(e)}"
        medical_logger.log(f"🔥 {error_message}", "ERROR", details={"error_type": type(e).__name__})
        logger.error(error_message, exc_info=True)
        
    finally:
        # Ensure the handler is flushed to send all buffered data.
        if langfuse_handler:
            logger.info(f"Flushing Langfuse handler for encounter {encounter_id}")
            langfuse_handler.flush()

@router.post(
    "/generate-notes",
    response_model=JobAcknowledgementResponse,
    summary="Generate Notes from NestJS (Main Endpoint)",
    description="""
    This is the main endpoint that NestJS calls to generate medical notes.
    It processes the encounter and sends sections back to NestJS as they're completed.
    All LLM requests are automatically traced with Langfuse for observability.
    """
)
async def generate_notes(
    request: EncounterRequestModel,
    background_tasks: BackgroundTasks
) -> JobAcknowledgementResponse:
    """
    Main endpoint for NestJS integration. Generates notes and sends them back to NestJS.
    This endpoint matches the expected flow from the story requirements.
    
    Features:
    - Full Langfuse observability for all LLM requests
    - Real-time section delivery to NestJS
    - Comprehensive medical logging and tracing
    - SNOMED validation and doctor preferences
    """
    job_id = f"notes_{request.encounterId}_{str(uuid.uuid4())[:8]}"
    
    logger.info(f"🚀 Starting notes generation job {job_id} for encounter {request.encounterId}")

    production_jobs[job_id] = {"status": "QUEUED"}
    
    background_tasks.add_task(
        _run_encounter_processing_pipeline,
        request=request,
        job_id=job_id,
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