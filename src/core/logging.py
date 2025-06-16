"""Logging configuration for NoteGen AI APIs.

This module provides structured logging with security features, PII masking,
and proper formatting for the medical SOAP generation microservice.
"""

import json
import logging
import logging.handlers
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.config import settings


class PIIMaskingFormatter(logging.Formatter):
    """Custom formatter that masks PII in log messages."""
    
    # Patterns for PII detection
    PII_PATTERNS = {
        'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
        'phone': re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'),
        'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
        'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
        'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
        'patient_id': re.compile(r'\b[Pp]atient[-_\s]*[Ii][Dd]?:?\s*([A-Z0-9-]+)\b'),
        'mrn': re.compile(r'\b[Mm][Rr][Nn]:?\s*([A-Z0-9-]+)\b'),
    }
    
    def __init__(self, mask_pii: bool = True, *args, **kwargs):
        """Initialize PII masking formatter."""
        super().__init__(*args, **kwargs)
        self.mask_pii = mask_pii
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with PII masking."""
        # Format the record normally first
        formatted = super().format(record)
        
        # Apply PII masking if enabled
        if self.mask_pii and settings.mask_pii:
            formatted = self._mask_pii(formatted)
        
        return formatted
    
    def _mask_pii(self, text: str) -> str:
        """Mask PII in text using defined patterns."""
        for pii_type, pattern in self.PII_PATTERNS.items():
            if pii_type == 'email':
                text = pattern.sub(lambda m: f"***@{m.group().split('@')[1]}", text)
            elif pii_type in ['phone', 'ssn', 'credit_card']:
                text = pattern.sub("***-**-****", text)
            elif pii_type == 'ip_address':
                text = pattern.sub("***.***.***.***", text)
            elif pii_type in ['patient_id', 'mrn']:
                text = pattern.sub(lambda m: f"{m.group().split(':')[0]}:***", text)
        
        return text


class JSONFormatter(PIIMaskingFormatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_data[key] = value
        
        # Convert to JSON and apply PII masking
        json_str = json.dumps(log_data, default=str, ensure_ascii=False)
        
        if self.mask_pii and settings.mask_pii:
            json_str = self._mask_pii(json_str)
        
        return json_str


class AuditLogger:
    """Specialized logger for audit events."""
    
    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Create audit log handler
        if settings.audit_logging_enabled:
            audit_log_path = Path("logs/audit.log")
            audit_log_path.parent.mkdir(exist_ok=True)
            
            handler = logging.handlers.RotatingFileHandler(
                audit_log_path,
                maxBytes=50 * 1024 * 1024,  # 50MB
                backupCount=10
            )
            
            formatter = JSONFormatter(mask_pii=False)  # Don't mask audit logs
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_patient_data_access(
        self,
        user_id: str,
        action: str,
        patient_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log patient data access for compliance."""
        self.logger.info(
            "Patient data access",
            extra={
                'event_type': 'patient_data_access',
                'user_id': user_id,
                'action': action,
                'patient_id': patient_id,
                'conversation_id': conversation_id,
                'metadata': metadata or {},
                'compliance': True
            }
        )
    
    def log_soap_generation(
        self,
        user_id: str,
        conversation_id: str,
        section_type: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log SOAP generation events."""
        self.logger.info(
            "SOAP generation event",
            extra={
                'event_type': 'soap_generation',
                'user_id': user_id,
                'conversation_id': conversation_id,
                'section_type': section_type,
                'success': success,
                'metadata': metadata or {}
            }
        )
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security events."""
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                'event_type': 'security_event',
                'security_event_type': event_type,
                'user_id': user_id,
                'ip_address': ip_address,
                'details': details or {},
                'security': True
            }
        )


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
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.log_format.lower() == "json":
        console_formatter = JSONFormatter()
    else:
        console_formatter = PIIMaskingFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if settings.log_file_enabled:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log_file_path,
            maxBytes=_parse_size(settings.log_rotation_size),
            backupCount=settings.log_retention_days
        )
        
        file_formatter = JSONFormatter() if settings.log_format.lower() == "json" else PIIMaskingFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
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
    
    # Set audit logger level
    if settings.audit_logging_enabled:
        logging.getLogger("audit").setLevel(logging.INFO)


def _parse_size(size_str: str) -> int:
    """Parse size string to bytes."""
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


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


# Global audit logger instance
audit_logger = AuditLogger()

# Factory function for contextual loggers
def get_logger(name: str) -> ContextualLogger:
    """Get a contextual logger instance."""
    return ContextualLogger(name) 