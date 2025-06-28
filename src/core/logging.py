"""Enhanced logging configuration for NoteGen AI APIs.

This module provides comprehensive logging capabilities including:
- JSON structured logging for CloudWatch in production
- Human-readable console logging for development
- Contextual logging for request tracing
"""

import json
import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Any, Dict, Optional
import time
from datetime import datetime

from src.core.config import settings


class CloudWatchJSONFormatter(logging.Formatter):
    """JSON formatter specifically designed for AWS CloudWatch."""
    
    def format(self, record):
        """Format log record as a single-line JSON object for CloudWatch."""
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "path": record.pathname,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_object['exception'] = self.formatException(record.exc_info)
        
        # Add any extra attributes from the LogRecord
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 
                          'filename', 'funcName', 'id', 'levelname', 'levelno', 
                          'lineno', 'module', 'msecs', 'message', 'msg', 'name', 
                          'pathname', 'process', 'processName', 'relativeCreated', 
                          'stack_info', 'thread', 'threadName']:
                log_object[key] = value
        
        # Return a single line JSON string
        return json.dumps(log_object, default=str)


class DevelopmentFormatter(logging.Formatter):
    """Human-readable formatter for development environment."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s loglevel=%(levelname)-6s logger=%(name)s %(funcName)s() L%(lineno)-4d %(message)s call_trace=%(pathname)s L%(lineno)-4d',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging():
    """Configure application logging based on environment."""
    # Get environment
    environment = os.getenv('PY_ENV', 'development')
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Configure formatter based on environment
    if environment == 'production':
        # Use JSON formatter for CloudWatch in production
        formatter = CloudWatchJSONFormatter()
    else:
        # Use human-readable formatter for development
        formatter = DevelopmentFormatter()
    
    # Set formatter and add handler
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Ensure all loggers use our handler in production
    if environment == 'production':
        for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", 
                           "fastapi", "opensearch", "httpx"]:
            logger = logging.getLogger(logger_name)
            # Remove any existing handlers
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            # Use our JSON formatter
            logger.addHandler(console_handler)
            # Don't propagate to avoid duplicate logs
            logger.propagate = False


def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name)


class MedicalProcessingLogger:
    """
    Specialized logger for medical AI processing that tracks every detail.
    
    Features:
    - Step-by-step processing logs
    - Medical data transformation tracking
    - Performance metrics
    - Terminal output for all processing details
    - JSON format for CloudWatch in production
    """
    
    def __init__(self, encounter_id, output_folder=None):
        self.encounter_id = encounter_id
        self.output_folder = output_folder  # Kept for compatibility
        self.logger = logging.getLogger(f"medical_processing.{encounter_id}")
        self.start_time = time.time()
        
        # In-memory storage for processing data
        self.processing_steps = []
        self.medical_mappings = {}
        self.detailed_log = {
            "encounter_id": encounter_id,
            "processing_started_at": datetime.utcnow().isoformat(),
            "steps": []
        }
        
        # Log initialization
        self._log_initialization()
    
    def _log_initialization(self):
        """Log initialization message."""
        environment = os.getenv('PY_ENV', 'development')
        
        if environment == 'production':
            # JSON format for CloudWatch
            log_data = {
                "event_type": "PROCESSING_START",
                "encounter_id": self.encounter_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Starting medical processing for encounter {self.encounter_id}"
            }
            print(json.dumps(log_data))
        else:
            # Human-readable format for development
            print(f"\n{'='*80}")
            print(f"MEDICAL PROCESSING: Encounter {self.encounter_id}")
            print(f"Started at: {datetime.utcnow().isoformat()}")
            print(f"{'='*80}\n")
        
        # Also log through standard logger
        self.logger.info(f"Starting medical processing for encounter {self.encounter_id}")
    
    def log_step(self, step_name, details, data=None):
        """Log a processing step."""
        timestamp = datetime.utcnow().isoformat()
        environment = os.getenv('PY_ENV', 'development')
        
        # Store step info
        step_info = {
            "step": step_name,
            "timestamp": timestamp,
            "details": details,
            "data": data or {}
        }
        self.processing_steps.append(step_info)
        self.detailed_log["steps"].append(step_info)
        
        if environment == 'production':
            # JSON format for CloudWatch
            log_data = {
                "event_type": "PROCESSING_STEP",
                "step": step_name,
                "encounter_id": self.encounter_id,
                "timestamp": timestamp,
                "message": details
            }
            if data:
                log_data["data"] = data
            print(json.dumps(log_data, default=str))
        else:
            # Human-readable format for development
            print(f"[{timestamp}] STEP: {step_name}")
            print(f"   DETAILS: {details}")
            if data:
                print(f"   DATA: {json.dumps(data, indent=2)}")
            print("")
        
        # Also log through standard logger
        self.logger.info(f"{step_name}: {details}")
    
    def log_neo4j_mapping(self, original_term, snomed_result):
        """Log a successful SNOMED mapping."""
        mapping_details = {
            "original_term": original_term,
            **snomed_result
        }
        self.medical_mappings.setdefault(original_term, []).append(snomed_result)
        
        self.log_step(
            "NEO4J_SNOMED_MAPPING",
            f"Mapped '{original_term}' -> '{snomed_result.get('preferred_term')}' (SNOMED: {snomed_result.get('snomed_concept_id')})",
            mapping_details
        )
    
    def log_section_generation(self, section_id, section_type, generation_result):
        """Log the result of a section generation."""
        generation_details = {
            "section_id": section_id,
            "section_type": section_type,
            "content_length": len(generation_result.get("content", "")),
            "line_references_found": len(generation_result.get("line_references", [])),
            "snomed_mappings_applied": len(generation_result.get("snomed_mappings", [])),
            "confidence_score": generation_result.get("confidence_score"),
            "processing_duration": generation_result.get("processing_metadata", {}).get("duration"),
            "status": "COMPLETED" if not generation_result.get("content", "").startswith("Error:") else "FAILED"
        }
        
        self.log_step(
            "SECTION_GENERATION_COMPLETED",
            f"Generated {section_type} section (ID: {section_id}) - {generation_details['content_length']} chars, {generation_details['line_references_found']} line refs",
            generation_details
        )
    
    def log(self, message, level="INFO", **kwargs):
        """Log a generic message."""
        timestamp = datetime.utcnow().isoformat()
        environment = os.getenv('PY_ENV', 'development')
        
        if environment == 'production':
            # JSON format for CloudWatch
            log_data = {
                "event_type": "LOG_MESSAGE",
                "level": level.upper(),
                "encounter_id": self.encounter_id,
                "timestamp": timestamp,
                "message": message
            }
            if kwargs:
                log_data["details"] = kwargs
            print(json.dumps(log_data, default=str))
        else:
            # Human-readable format for development
            print(f"[{timestamp}] [{level.upper()}] {message}")
            if kwargs:
                print(f"   Details: {json.dumps(kwargs, indent=2, default=str)}")
        
        # Also log through standard logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra=kwargs)


def create_medical_logger(encounter_id, output_folder=None):
    """Factory function to create a medical logger."""
    return MedicalProcessingLogger(encounter_id, output_folder)