"""Main FastAPI application for NoteGen AI APIs.

This is the entry point for the medical SOAP note generation microservice.
It sets up the FastAPI application with all necessary middleware, security,
and API routes.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

from src.core.config import settings
from src.core.logging import setup_logging, get_logger, audit_logger
from src.core.security import security_middleware, jwt_bearer_optional
from src.models.api_models import HealthCheckResponse, ErrorResponse
from src.api.endpoints import soap, conversation, health

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'notegen_requests_total', 
    'Total requests', 
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'notegen_request_duration_seconds', 
    'Request duration', 
    ['method', 'endpoint']
)
SOAP_GENERATION_COUNT = Counter(
    'notegen_soap_generations_total',
    'Total SOAP generations',
    ['section_type', 'status']
)

# Application startup time
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting NoteGen AI APIs microservice...")
    
    try:
        # Initialize services here if needed
        # await initialize_services()
        
        logger.info("✓ NoteGen AI APIs startup completed successfully")
        audit_logger.log_security_event(
            "application_startup",
            details={"version": settings.app_version, "environment": settings.environment}
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down NoteGen AI APIs microservice...")
    audit_logger.log_security_event(
        "application_shutdown",
        details={"uptime_seconds": time.time() - app_start_time}
    )


# Create FastAPI application
app = FastAPI(
    title="NoteGen AI APIs",
    description="Medical SOAP note generation microservice using AI and RAG systems",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    """Security middleware for request validation and rate limiting."""
    start_time = time.time()
    
    try:
        # Skip security validation for health check and metrics endpoints
        if request.url.path in ["/health", "/metrics"]:
            response = await call_next(request)
            return response
        
        # Validate request security
        security_context = await security_middleware.validate_request(request)
        
        # Add security context to request state
        request.state.security_context = security_context
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        return response
        
    except HTTPException as e:
        # Log security violations
        if e.status_code in [401, 403, 429]:
            audit_logger.log_security_event(
                "request_blocked",
                ip_address=security_middleware._get_client_ip(request),
                details={
                    "status_code": e.status_code,
                    "detail": e.detail,
                    "path": str(request.url.path)
                }
            )
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=e.status_code
        ).inc()
        
        return JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(
                error="SecurityError" if e.status_code in [401, 403] else "RateLimitError",
                message=e.detail,
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in security middleware: {str(e)}")
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP{exc.status_code}",
            message=exc.detail,
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred" if not settings.debug else str(exc),
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic API information."""
    return {
        "service": "NoteGen AI APIs",
        "version": settings.app_version,
        "description": "Medical SOAP note generation microservice",
        "status": "healthy",
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health"
    }


# Health check endpoint (no authentication required)
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.app_version,
            "uptime_seconds": time.time() - app_start_time,
            "services": {
                "application": "healthy",
                # Add actual service checks here
                "azure_openai": "healthy",  # Would check actual connection
                "neo4j": "healthy",         # Would check actual connection
                "vector_db": "healthy",     # Would check actual connection
            }
        }
        
        return HealthCheckResponse(**health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.prometheus_enabled:
        raise HTTPException(status_code=404, detail="Metrics not enabled")
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include API routers
app.include_router(
    soap.router,
    prefix="/api/v1/soap",
    tags=["SOAP Generation"],
    dependencies=[Depends(jwt_bearer_optional)]
)

app.include_router(
    conversation.router,
    prefix="/api/v1/conversation",
    tags=["Conversation Management"],
    dependencies=[Depends(jwt_bearer_optional)]
)

app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health & Monitoring"]
)


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=settings.api_workers if not settings.debug else 1,
        log_level=settings.log_level.lower(),
        access_log=True
    ) 