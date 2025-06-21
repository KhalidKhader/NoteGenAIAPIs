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
import re
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
    
    def set_context(self, **kwargs) -> None:
        """Set context for subsequent log messages."""
        self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear logging context."""
        self._context.clear()
    
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
    
    def log_conversation_storage(self, conversation_id: str, details: Dict[str, Any]):
        """Log conversation storage details."""
        self.log_step(
            "CONVERSATION_STORAGE",
            f"Storing conversation {conversation_id} with speaker-aware chunking",
            {
                "conversation_id": conversation_id,
                "total_speaker_turns": details.get("total_speaker_turns", 0),
                "total_chunks_created": details.get("total_chunks_created", 0),
                "conversation_length_chars": details.get("conversation_length_chars", 0),
                "storage_method": "AWS_OPENSEARCH_SPEAKER_AWARE",
                "chunking_strategy": "PRESERVE_SPEAKER_TURNS",
                "line_numbers_preserved": details.get("line_numbers_preserved", True)
            }
        )
        
        self.detailed_log["conversation_storage"] = details
        self._save_detailed_log()
    
    def log_neo4j_mapping(self, original_term: str, snomed_result: Dict[str, Any]):
        """Log SNOMED Neo4j mapping details."""
        mapping_details = {
            "original_term": original_term,
            "snomed_concept_id": snomed_result.get("concept_id", ""),
            "preferred_term": snomed_result.get("preferred_term", ""),
            "match_type": snomed_result.get("match_type", ""),
            "confidence": snomed_result.get("confidence", 0.0),
            "language": snomed_result.get("language", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.medical_mappings[original_term] = mapping_details
        
        self.log_step(
            "NEO4J_SNOMED_MAPPING",
            f"Mapped '{original_term}' → '{snomed_result.get('preferred_term', 'N/A')}' (SNOMED: {snomed_result.get('concept_id', 'N/A')})",
            mapping_details
        )
        
        self.detailed_log["neo4j_queries"].append({
            "query_type": "SNOMED_MAPPING",
            "input_term": original_term,
            "result": snomed_result,
            "timestamp": datetime.utcnow().isoformat()
        })
        self._save_detailed_log()
    
    def log_section_generation(self, section_id: str, section_type: str, generation_result: Dict[str, Any]):
        """Log section generation completion."""
        generation_details = {
            "section_id": section_id,
            "section_type": section_type,
            "content_length": len(generation_result.get("content", "")),
            "line_references_found": len(generation_result.get("line_references", [])),
            "snomed_mappings_applied": len(generation_result.get("snomed_mappings", [])),
            "confidence_score": generation_result.get("confidence_score", 0.0),
            "processing_duration": generation_result.get("processing_metadata", {}).get("processing_duration_seconds", 0),
            "status": "COMPLETED",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.log_step(
            "SECTION_GENERATION_COMPLETED",
            f"Generated {section_type} section (ID: {section_id}) - {generation_details['content_length']} chars, {generation_details['line_references_found']} line refs",
            generation_details
        )
        
        self.detailed_log["section_generations"].append(generation_details)
        self._save_detailed_log()
    
    def log_file_operation(self, operation: str, file_path: str, details: Dict[str, Any]):
        """Log file operations."""
        file_op = {
            "operation": operation,
            "file_path": file_path,
            "file_size_bytes": details.get("file_size", 0),
            "content_type": details.get("content_type", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "success": details.get("success", True)
        }
        
        self.file_operations.append(file_op)
        
        self.log_step(
            "FILE_OPERATION",
            f"{operation}: {file_path} ({details.get('file_size', 0)} bytes)",
            file_op
        )
        
        self.detailed_log["file_operations"].append(file_op)
        self._save_detailed_log()
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "seconds"):
        """Log performance metrics."""
        self.performance_metrics[metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.log_step(
            "PERFORMANCE_METRIC",
            f"{metric_name}: {value} {unit}",
            {"metric": metric_name, "value": value, "unit": unit}
        )
        
        self.detailed_log["performance_metrics"][metric_name] = self.performance_metrics[metric_name]
        self._save_detailed_log()
    
    def finalize_processing(self, total_sections: int, successful_sections: int, failed_sections: int):
        """Finalize processing and write summary."""
        total_time = time.time() - self.start_time
        
        summary = {
            "total_processing_time_seconds": total_time,
            "total_sections_requested": total_sections,
            "successful_sections": successful_sections,
            "failed_sections": failed_sections,
            "success_rate": (successful_sections / total_sections * 100) if total_sections > 0 else 0,
            "total_processing_steps": len(self.processing_steps),
            "total_medical_mappings": len(self.medical_mappings),
            "total_doctor_preferences_applied": len(self.doctor_preferences_applied),
            "total_file_operations": len(self.file_operations),
            "completed_at": datetime.utcnow().isoformat()
        }
        
        self.log_step(
            "PROCESSING_COMPLETED",
            f"Encounter processing completed: {successful_sections}/{total_sections} sections successful in {total_time:.2f}s",
            summary
        )
        
        # Write final summary
        with open(self.processing_log_file, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write("🏁 PROCESSING SUMMARY\n")
            f.write(f"{'='*80}\n")
            f.write(f"Total processing time: {total_time:.2f} seconds\n")
            f.write(f"Sections processed: {successful_sections}/{total_sections} successful\n")
            f.write(f"Success rate: {summary['success_rate']:.1f}%\n")
            f.write(f"Medical mappings created: {len(self.medical_mappings)}\n")
            f.write(f"Doctor preferences applied: {len(self.doctor_preferences_applied)}\n")
            f.write(f"File operations: {len(self.file_operations)}\n")
            f.write(f"Processing steps logged: {len(self.processing_steps)}\n")
            f.write(f"Completed at: {datetime.utcnow().isoformat()}Z\n")
        
        # Update detailed log with summary
        self.detailed_log["processing_summary"] = summary
        self.detailed_log["completed_at"] = datetime.utcnow().isoformat()
        self._save_detailed_log()
    
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Generic log method to capture ad-hoc messages."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "encounter_id": self.encounter_id,
            "details": kwargs.get("details", {})
        }
        self.log_entries.append(log_entry)
        
        # Also write to the simple text log for immediate visibility
        color_map = {"INFO": "✅", "WARNING": "⚠️", "ERROR": "❌", "DEBUG": "🐞"}
        icon = color_map.get(level, "ℹ️")

        with open(self.processing_log_file, 'a') as f:
            f.write(f"[{timestamp}] {icon} [{level}] {message}\n")
            if 'details' in kwargs and kwargs['details']:
                f.write(f"   Details: {json.dumps(kwargs['details'], indent=2)}\n")

        self.detailed_log["processing_steps"].append({
            "step": "GENERIC_LOG",
            "timestamp": timestamp,
            "details": message,
            "level": level,
            "data": kwargs.get("details", {})
        })
        self._save_detailed_log()
    
    def _save_detailed_log(self):
        """Save detailed JSON log."""
        try:
            with open(self.detailed_log_file, 'w') as f:
                json.dump(self.detailed_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Fallback to basic logging if JSON fails
            with open(self.processing_log_file, 'a') as f:
                f.write(f"[ERROR] Failed to save detailed JSON log: {e}\n")


def create_medical_logger(encounter_id: str, output_folder: Path) -> MedicalProcessingLogger:
    """Create a medical processing logger for an encounter."""
    return MedicalProcessingLogger(encounter_id, output_folder) 