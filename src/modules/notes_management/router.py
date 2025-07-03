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

from fastapi import APIRouter, HTTPException, BackgroundTasks

from src.core.settings.logging import logger
from src.core.settings.observability import get_langfuse_handler, flush_langfuse_data
from src.core.settings.config import settings
from .schema import (
    EncounterRequestModel,
    JobAcknowledgementResponse,
)
from .handlers import _run_encounter_processing_pipeline, production_jobs
router = APIRouter()

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

