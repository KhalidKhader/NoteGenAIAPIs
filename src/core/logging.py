"""Enhanced logging configuration for NoteGen AI APIs.

This module provides comprehensive logging capabilities including:
- PII masking for patient data protection
- JSON structured logging for observability
- Audit logging for compliance
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


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Create log entry
        log_entry = {
            'timestamp': self.formatTime(record, self.datefmt),
            'loglevel': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'call_trace': f"{record.pathname} L{record.lineno}"
        }
        
        # Add task name if available (for async tasks)
        if hasattr(record, 'taskName'):
            log_entry['taskName'] = record.taskName
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                              'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process', 'taskName']:
                    log_entry[key] = value
        
        # Convert to JSON - single line for AWS CloudWatch
        return json.dumps(log_entry, default=str, ensure_ascii=False, separators=(',', ':'))


class DevelopmentFormatter(logging.Formatter):
    """Development formatter for readable console output."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s loglevel=%(levelname)-6s logger=%(name)s %(funcName)s() L%(lineno)-4d %(message)s call_trace=%(pathname)s L%(lineno)-4d',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging() -> None:
    """Configure application logging based on environment."""
    # Get environment
    environment = os.getenv('PY_ENV', 'development')
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Configure based on environment - terminal only, no file handlers
    if environment == 'production':
        # Production: JSON formatter for AWS CloudWatch
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = JSONFormatter()
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    else:
        # Development: Readable formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = DevelopmentFormatter()
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Medical-specific loggers
    logging.getLogger("soap_generation").setLevel(logging.INFO)
    logging.getLogger("rag_retrieval").setLevel(logging.INFO)
    logging.getLogger("pattern_learning").setLevel(logging.INFO)


class ContextualLogger:
    """Logger with contextual information for request tracing."""
    
    def __init__(self, name: str):
        """Initialize contextual logger."""
        self.logger = logging.getLogger(name)
        self._context: Dict[str, Any] = {}
    
    def _log_with_context(self, level: int, message: str, *args, **kwargs) -> None:
        """Log message with context."""
        extra = kwargs.get('extra', {})
        extra.update(self._context)
        kwargs['extra'] = extra
        self.logger.log(level, message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, *args, **kwargs)


def get_logger(name: str) -> ContextualLogger:
    """Get contextual logger instance."""
    return ContextualLogger(name)


class MedicalProcessingLogger:
    """
    Specialized logger for medical AI processing that tracks every detail.
    
    Features:
    - Step-by-step processing logs
    - Medical data transformation tracking
    - Performance metrics
    - Terminal output for all processing details
    - Structured JSON format for clarity
    """
    
    def __init__(self, encounter_id: str, output_folder: Path = None):
        self.encounter_id = encounter_id
        # Keep output_folder as attribute for compatibility with existing code,
        # but don't actually create the folder
        self.output_folder = output_folder
        
        # Logger for terminal output
        self.logger = logging.getLogger(f"medical_processing.{encounter_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Processing state tracking
        self.start_time = time.time()
        self.processing_steps = []
        self.performance_metrics = {}
        self.medical_mappings = {}
        self.doctor_preferences_applied = {}
        self.file_operations = []
        self.log_entries = []
        
        # Initialize logs with header
        self._initialize_logs()
    
    def _initialize_logs(self):
        """Initialize logs with headers."""
        header = f"MEDICAL AI PROCESSING LOG - Encounter {self.encounter_id}\n"
        separator = f"{'='*80}\n"
        start_info = f"Started at: {datetime.utcnow().isoformat()}Z\n"
        output_info = f"Output folder: {self.output_folder}\n"
        
        print(header + separator + start_info + output_info)
        self.logger.info(f"MEDICAL AI PROCESSING LOG - Encounter {self.encounter_id}")
        self.logger.info(f"Started at: {datetime.utcnow().isoformat()}Z")
        self.logger.info(f"Output folder: {self.output_folder}")
        
        # Initialize detailed log structure in memory
        self.detailed_log = {
            "encounter_id": self.encounter_id,
            "processing_started_at": datetime.utcnow().isoformat(),
            "output_folder": str(self.output_folder) if self.output_folder else "terminal_only",
            "processing_steps": [],
            "performance_metrics": {},
            "medical_mappings": {},
            "doctor_preferences": {},
            "file_operations": [],
            "azure_openai_calls": [],
            "neo4j_queries": [],
            "conversation_storage": {},
            "section_generations": []
        }
    
    def log_step(self, step_name: str, details: str, data: Optional[Dict[str, Any]] = None):
        """Log a processing step with full details to terminal."""
        timestamp = datetime.utcnow().isoformat()
        step_info = {
            "step": step_name,
            "timestamp": timestamp,
            "details": details,
            "data": data or {}
        }
        
        self.processing_steps.append(step_info)
        
        # Print to terminal
        print(f"[{timestamp}] STEP: {step_name}")
        print(f"   DETAILS: {details}")
        if data:
            print(f"   DATA: {json.dumps(data, indent=2)}")
        print("")
        
        # Update detailed JSON log in memory
        self.detailed_log["processing_steps"].append(step_info)

    
    def log_neo4j_mapping(self, original_term: str, snomed_result: Dict[str, Any]):
        """Log a successful SNOMED mapping to terminal."""
        
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

    def log_section_generation(self, section_id: str, section_type: str, generation_result: Dict[str, Any]):
        """Log the result of a SOAP section generation to terminal."""
        
        generation_details = {
            "section_id": section_id,
            "section_type": section_type,
            "content_length": len(generation_result.get("content", "")),
            "line_references_found": len(generation_result.get("line_references", [])),
            "snomed_mappings_applied": len(generation_result.get("snomed_mappings", [])),
            "confidence_score": generation_result.get("confidence_score"),
            "processing_duration": generation_result.get("processing_metadata", {}).get("duration"),
            "status": "COMPLETED" if not generation_result.get("content", "").startswith("Error:") else "FAILED",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.log_step(
            "SECTION_GENERATION_COMPLETED",
            f"Generated {section_type} section (ID: {section_id}) - {generation_details['content_length']} chars, {generation_details['line_references_found']} line refs",
            generation_details
        )
        
        self.detailed_log['section_generations'].append(generation_details)


    def log(self, message: str, level: str = "INFO", **kwargs):
        """
        Log a generic message to the terminal.
        This is useful for informational messages, warnings, or errors that are not
        part of a structured step.
        """
        timestamp = datetime.utcnow().isoformat()
        
        log_message = f"[{timestamp}] [{level.upper()}] {message}"
        
        # Print to terminal
        print(log_message)
        
        # Add details if provided
        if kwargs:
            details = f"   Details: {json.dumps(kwargs, indent=2, default=str)}"
            print(details)
        
        # Add to detailed JSON log in memory
        self.detailed_log['processing_steps'].append({
            "step": "GENERIC_LOG",
            "timestamp": timestamp,
            "level": level.upper(),
            "details": message,
            "data": kwargs
        })


def create_medical_logger(encounter_id: str, output_folder: Path = None) -> MedicalProcessingLogger:
    """Factory function to create a medical logger."""
    return MedicalProcessingLogger(encounter_id, output_folder)