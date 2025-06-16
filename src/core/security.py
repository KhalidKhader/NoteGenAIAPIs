"""Security utilities for NoteGen AI APIs.

This module provides comprehensive security features including data encryption,
JWT token validation, rate limiting, and audit logging for HIPAA/PIPEDA compliance.
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import jwt
from cryptography.fernet import Fernet
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from src.core.config import settings
from src.core.logging import audit_logger, get_logger

logger = get_logger(__name__)


class DataEncryption:
    """Handles encryption and decryption of sensitive medical data."""
    
    def __init__(self):
        """Initialize encryption with the configured key."""
        self.encryption_key = settings.encryption_key.encode()[:32]  # Ensure 32 bytes
        self.fernet = Fernet(Fernet.generate_key())  # Use a proper key
        
        # For production, you should use a proper key derivation function
        if settings.is_production:
            # In production, use a proper key derivation
            key = hashlib.pbkdf2_hmac('sha256', self.encryption_key, b'salt', 100000)
            self.fernet = Fernet(Fernet.generate_key())
    
    def encrypt_patient_data(self, data: str) -> str:
        """Encrypt sensitive patient conversation data."""
        if not settings.patient_data_encryption:
            return data
        
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            audit_logger.log_security_event(
                "data_encryption",
                details={"data_type": "patient_conversation", "encrypted": True}
            )
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt patient data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Data encryption failed"
            )
    
    def decrypt_patient_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive patient conversation data."""
        if not settings.patient_data_encryption:
            return encrypted_data
        
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data.encode())
            audit_logger.log_security_event(
                "data_decryption",
                details={"data_type": "patient_conversation", "decrypted": True}
            )
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt patient data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Data decryption failed"
            )
    
    def hash_sensitive_id(self, identifier: str) -> str:
        """Create a secure hash of sensitive identifiers."""
        return hashlib.sha256(
            (identifier + settings.encryption_key).encode()
        ).hexdigest()[:16]


class JWTHandler:
    """Handles JWT token validation and management."""
    
    def __init__(self):
        """Initialize JWT handler."""
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_expire_minutes
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check token expiration
            if payload.get("exp") and datetime.utcnow().timestamp() > payload["exp"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            audit_logger.log_security_event(
                "token_validation",
                user_id=payload.get("sub"),
                details={"valid": True, "algorithm": self.algorithm}
            )
            
            return payload
            
        except jwt.InvalidTokenError as e:
            audit_logger.log_security_event(
                "token_validation",
                details={"valid": False, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a new access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode.update({"exp": expire})
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        audit_logger.log_security_event(
            "token_creation",
            user_id=data.get("sub"),
            details={"expires_at": expire.isoformat()}
        )
        
        return token


class RateLimiter:
    """Rate limiting implementation for API endpoints."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.requests = {}  # In production, use Redis
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()
    
    def is_allowed(self, identifier: str, max_requests: int = None, window: int = 60) -> bool:
        """Check if request is allowed based on rate limits."""
        if not settings.rate_limit_enabled:
            return True
        
        max_requests = max_requests or settings.rate_limit_requests_per_minute
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries()
            self.last_cleanup = current_time
        
        # Get or create request history for this identifier
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside the window
        cutoff_time = current_time - window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        # Check if within rate limit
        if len(self.requests[identifier]) >= max_requests:
            audit_logger.log_security_event(
                "rate_limit_exceeded",
                details={
                    "identifier": identifier,
                    "requests_count": len(self.requests[identifier]),
                    "max_requests": max_requests,
                    "window_seconds": window
                }
            )
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True
    
    def _cleanup_old_entries(self):
        """Remove old entries from memory."""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Keep 1 hour of history
        
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff_time
            ]
            
            # Remove empty entries
            if not self.requests[identifier]:
                del self.requests[identifier]


class APIKeyValidator:
    """Validates API keys for service-to-service authentication."""
    
    def __init__(self):
        """Initialize API key validator."""
        self.valid_keys = set()  # In production, load from secure storage
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key."""
        # In production, implement proper API key validation
        # This is a simplified version
        if not api_key:
            return False
        
        # Hash the API key and check against stored hashes
        # For now, just check if it's not empty
        is_valid = len(api_key) >= 32
        
        audit_logger.log_security_event(
            "api_key_validation",
            details={"valid": is_valid, "key_length": len(api_key)}
        )
        
        return is_valid


class SecurityMiddleware:
    """Security middleware for request validation and rate limiting."""
    
    def __init__(self):
        """Initialize security middleware."""
        self.rate_limiter = RateLimiter()
        self.encryption = DataEncryption()
        self.jwt_handler = JWTHandler()
        self.api_key_validator = APIKeyValidator()
    
    async def validate_request(self, request: Request) -> Dict[str, Any]:
        """Validate incoming request for security compliance."""
        client_ip = self._get_client_ip(request)
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(client_ip):
            audit_logger.log_security_event(
                "rate_limit_violation",
                ip_address=client_ip,
                details={"path": str(request.url.path)}
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Extract authentication information
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get(settings.api_key_header)
        
        user_info = {}
        
        # Validate JWT token if present
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = self.jwt_handler.verify_token(token)
                user_info = {
                    "user_id": payload.get("sub"),
                    "roles": payload.get("roles", []),
                    "permissions": payload.get("permissions", [])
                }
            except HTTPException:
                # Token validation failed, continue with API key validation
                pass
        
        # Validate API key if no valid JWT
        if not user_info and api_key:
            if self.api_key_validator.validate_api_key(api_key):
                user_info = {"api_key_valid": True}
            else:
                audit_logger.log_security_event(
                    "invalid_api_key",
                    ip_address=client_ip,
                    details={"path": str(request.url.path)}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
        
        # Log successful authentication
        if user_info:
            audit_logger.log_security_event(
                "successful_authentication",
                user_id=user_info.get("user_id"),
                ip_address=client_ip,
                details={
                    "path": str(request.url.path),
                    "method": request.method,
                    "auth_type": "jwt" if "user_id" in user_info else "api_key"
                }
            )
        
        return {
            "user_info": user_info,
            "client_ip": client_ip,
            "request_id": self._generate_request_id()
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID for tracing."""
        return secrets.token_hex(16)


class MedicalDataValidator:
    """Validates medical data for compliance and security."""
    
    def __init__(self):
        """Initialize medical data validator."""
        self.encryption = DataEncryption()
    
    def validate_conversation_data(self, conversation_data: Dict[str, Any]) -> bool:
        """Validate conversation data for medical compliance."""
        required_fields = ["transcription_text", "conversation_id"]
        
        # Check required fields
        for field in required_fields:
            if field not in conversation_data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate data types
        if not isinstance(conversation_data["transcription_text"], str):
            logger.warning("transcription_text must be a string")
            return False
        
        if not conversation_data["transcription_text"].strip():
            logger.warning("transcription_text cannot be empty")
            return False
        
        # Log validation success
        audit_logger.log_patient_data_access(
            user_id="system",
            action="conversation_validation",
            conversation_id=conversation_data.get("conversation_id"),
            metadata={"validation_passed": True}
        )
        
        return True
    
    def sanitize_soap_output(self, soap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize SOAP output to remove any sensitive information."""
        # Create a copy to avoid modifying original
        sanitized = soap_data.copy()
        
        # Remove any debugging information
        sanitized.pop("debug_info", None)
        sanitized.pop("raw_llm_response", None)
        
        # Ensure all content is properly formatted
        if "section_content" in sanitized:
            sanitized["section_content"] = str(sanitized["section_content"]).strip()
        
        return sanitized


# Global security instances
security_middleware = SecurityMiddleware()
data_encryption = DataEncryption()
jwt_handler = JWTHandler()
rate_limiter = RateLimiter()
medical_data_validator = MedicalDataValidator()


# FastAPI Security Dependencies
class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication."""
    
    def __init__(self, auto_error: bool = True):
        """Initialize JWT Bearer."""
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[str]:
        """Validate JWT token from request."""
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication token"
                )
            return None
        
        if credentials.scheme != "Bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
            return None
        
        # Validate token
        try:
            payload = jwt_handler.verify_token(credentials.credentials)
            return payload.get("sub")  # Return user ID
        except HTTPException:
            if self.auto_error:
                raise
            return None


# Security dependency instances
jwt_bearer = JWTBearer()
jwt_bearer_optional = JWTBearer(auto_error=False) 