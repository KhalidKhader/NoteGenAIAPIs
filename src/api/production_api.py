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
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks

from src.core.logging import get_logger, create_medical_logger
from src.core.observability import get_observability_service
from src.models.api_models import (
    EncounterRequestModel,
    JobAcknowledgementResponse,
    GeneratedSection
)
from src.services.conversation_rag import ConversationRAGService, get_conversation_rag_service
from src.services.snomed_rag import SNOMEDRAGService, get_snomed_rag_service
from src.services.section_generator import MedicalSectionGenerator, get_soap_generator_service
from src.services.pattern_learning import PatternLearningService, get_pattern_learning_service

router = APIRouter()
logger = get_logger(__name__)

# In-memory job tracking
production_jobs: Dict[str, Dict[str, Any]] = {}

@router.post(
    "/process-encounter",
    response_model=JobAcknowledgementResponse,
    summary="Process Complete Encounter for Multi-Template Extraction",
    description="""
    This production-ready endpoint orchestrates the entire asynchronous workflow 
    for processing a medical encounter and generating multiple template-based sections.
    """
)
async def process_encounter(
    request: EncounterRequestModel,
    background_tasks: BackgroundTasks
) -> JobAcknowledgementResponse:
    """
    Accepts an encounter, starts a background job for processing, and returns an immediate acknowledgement.
    """
    job_id = f"job_{request.encounterId}_{uuid.uuid4().hex[:8]}"
    logger.info(f"Accepted job {job_id} for encounter {request.encounterId}.")

    production_jobs[job_id] = {
        "status": "QUEUED",
        "started_at": datetime.utcnow().isoformat(),
        "encounter_id": request.encounterId,
        "total_sections": len(request.sections)
    }

    background_tasks.add_task(
        _run_encounter_processing_pipeline,
        request=request,
        job_id=job_id,
    )
    
    return JobAcknowledgementResponse(
        job_id=job_id,
        status="QUEUED",
        message="Encounter processing has been queued.",
        encounter_id=request.encounterId
    )

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
    
    obs_service = await get_observability_service()
    trace = obs_service.start_medical_encounter_trace(
        conversation_id=encounter_id,
        doctor_id=request.doctorId,
        language=request.language,
        metadata={"job_id": job_id}
    )

    try:
        medical_logger.log(f"🚀 Starting processing pipeline for job {job_id}", "INFO", details={"trace_id": trace.id if trace else 'N/A'})

        # STEP 1 & 2: Get service instances
        convo_rag: ConversationRAGService = await get_conversation_rag_service()
        snomed_rag: SNOMEDRAGService = await get_snomed_rag_service()
        section_generator: MedicalSectionGenerator = await get_soap_generator_service()
        # pattern_service: PatternLearningService = await get_pattern_learning_service() # For future use

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
            full_transcript_text, request.language, medical_logger
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
                        medical_logger=medical_logger
                    )
                    
                    if not generated_content.content.startswith("Error:"):
                        medical_logger.log(f"✅ Successfully generated and saved section '{section_name}' on attempt {attempt + 1}.", "INFO")
                        generated_sections_context.append(f"Section: {section_name}\\nContent: {generated_content.content}")
                        if trace:
                            trace.update(metadata={**trace.metadata, f"section_{section_name}_status": "Success"})
                    else:
                        medical_logger.log(f"❌ Generation resulted in an error for section '{section_name}'.", "ERROR", details={"error_content": generated_content.content})
                        if trace:
                            trace.update(metadata={**trace.metadata, f"section_{section_name}_status": "Failed"})

                    # Save the generated section to a file
                    section_output_path = sections_dir / f"{section_name.replace(' ', '_')}.json"
                    with open(section_output_path, 'w', encoding='utf-8') as f:
                        json.dump(generated_content.model_dump(), f, indent=2, ensure_ascii=False)
                    
                    # If successful, break the retry loop
                    if not generated_content.content.startswith("Error:"):
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
        if trace:
            obs_service.finish_medical_encounter_trace(encounter_id, success=True, final_status="COMPLETED")

    except Exception as e:
        production_jobs[job_id]['status'] = 'FAILED'
        error_message = f"Encounter processing pipeline failed: {str(e)}"
        medical_logger.log(f"🔥 {error_message}", "ERROR", details={"error_type": type(e).__name__})
        logger.error(error_message, exc_info=True)
        if trace:
            obs_service.finish_medical_encounter_trace(encounter_id, success=False, final_status="FAILED")

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