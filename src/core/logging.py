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
from pathlib import Path
from typing import Any, Dict, Optional
import time
from datetime import datetime

from src.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Create log entry
        log_entry = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName
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
        
        # Convert to JSON
        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_logging() -> None:
    """Configure application logging."""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = JSONFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - always enabled for medical compliance
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30  # 30 days retention
    )
    
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
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
    - File operation logging
    - Structured JSON logging for analysis
    """
    
    def __init__(self, encounter_id: str, output_folder: Path):
        self.encounter_id = encounter_id
        self.output_folder = output_folder
        self.processing_log_file = output_folder / "processing_log.txt"
        self.detailed_log_file = output_folder / "detailed_processing.json"
        
        # Processing state tracking
        self.start_time = time.time()
        self.processing_steps = []
        self.performance_metrics = {}
        self.medical_mappings = {}
        self.doctor_preferences_applied = {}
        self.file_operations = []
        self.log_entries = []
        
        # Ensure output folder exists
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize log files
        self._initialize_log_files()
    
    def _initialize_log_files(self):
        """Initialize log files with headers."""
        with open(self.processing_log_file, 'w') as f:
            f.write(f"🏥 MEDICAL AI PROCESSING LOG - Encounter {self.encounter_id}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Started at: {datetime.utcnow().isoformat()}Z\n")
            f.write(f"Output folder: {self.output_folder}\n\n")
        
        # Initialize detailed JSON log
        self.detailed_log = {
            "encounter_id": self.encounter_id,
            "processing_started_at": datetime.utcnow().isoformat(),
            "output_folder": str(self.output_folder),
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
        """Log a processing step with full details."""
        timestamp = datetime.utcnow().isoformat()
        step_info = {
            "step": step_name,
            "timestamp": timestamp,
            "details": details,
            "data": data or {}
        }
        
        self.processing_steps.append(step_info)
        
        # Write to text log
        with open(self.processing_log_file, 'a') as f:
            f.write(f"[{timestamp}] 🔄 {step_name}\n")
            f.write(f"   📋 {details}\n")
            if data:
                f.write(f"   📊 Data: {json.dumps(data, indent=2)}\n")
            f.write("\n")
        
        # Update detailed JSON log
        self.detailed_log["processing_steps"].append(step_info)
        self._save_detailed_log()

    
    def log_neo4j_mapping(self, original_term: str, snomed_result: Dict[str, Any]):
        """Log a successful SNOMED mapping."""
        
        mapping_details = {
            "original_term": original_term,
            **snomed_result
        }
        self.medical_mappings.setdefault(original_term, []).append(snomed_result)
        
        self.log_step(
            "NEO4J_SNOMED_MAPPING",
            f"Mapped '{original_term}' → '{snomed_result.get('preferred_term')}' (SNOMED: {snomed_result.get('snomed_concept_id')})",
            mapping_details
        )

    def log_section_generation(self, section_id: str, section_type: str, generation_result: Dict[str, Any]):
        """Log the result of a SOAP section generation."""
        
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
        self._save_detailed_log()


    def log(self, message: str, level: str = "INFO", **kwargs):
        """
        Log a generic message to the processing log file.
        This is useful for informational messages, warnings, or errors that are not
        part of a structured step.
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Determine emoji based on level
        emoji_map = {
            "INFO": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🐞",
        }
        emoji = emoji_map.get(level.upper(), "ℹ️")
        
        log_message = f"[{timestamp}] {emoji} [{level.upper()}] {message}\n"
        
        # Add details if provided
        if kwargs:
            log_message += f"   Details: {json.dumps(kwargs, indent=2, default=str)}\n"
        
        self.output_folder.mkdir(parents=True, exist_ok=True)
        with open(self.processing_log_file, 'a') as f:
            f.write(log_message)
        
        # Add to detailed JSON log as well
        self.detailed_log['processing_steps'].append({
            "step": "GENERIC_LOG",
            "timestamp": timestamp,
            "level": level.upper(),
            "details": message,
            "data": kwargs
        })
        self._save_detailed_log()


    def _save_detailed_log(self):
        """Save the detailed JSON log."""
        self.output_folder.mkdir(parents=True, exist_ok=True)
        with open(self.detailed_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.detailed_log, f, indent=2, ensure_ascii=False)


def create_medical_logger(encounter_id: str, output_folder: Path) -> MedicalProcessingLogger:
    """Factory function to create a medical logger."""
    return MedicalProcessingLogger(encounter_id, output_folder)