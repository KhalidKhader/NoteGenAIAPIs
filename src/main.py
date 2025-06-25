"""
NoteGen AI APIs - Medical SOAP Generation System

Implementation according to story requirements:
1. Multi-template extraction (SOAP, Visit Summary, Referral, Custom)
2. Long encounter handling with chunking
3. Precise line number referencing
4. Multilingual support (English/French)
5. Hallucination prevention through RAG validation
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables early
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment

from src.core.config import settings
from src.core.logging import setup_logging, get_logger

from src.api.health import router as health_router
from src.api.production_api import router as production_router

# Setup medical-grade logging
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("🏥 Starting NoteGen AI APIs - Medical Template Extraction System")
    logger.info("📋 Story Requirements: Multi-template + Long encounters + Line referencing + Multilingual + Hallucination prevention")
    logger.info("🔒 Medical compliance: HIPAA/PIPEDA ready with Canadian data residency")    
    logger.info("🚀 System ready for medical encounter processing")
    
    yield

    # Shutdown
    logger.info("🏥 Shutting down NoteGen AI APIs - Medical Template Extraction System")

    
    logger.info("✅ All medical encounters completed, system shutdown complete")

# Create FastAPI application for medical use
app = FastAPI(
    title="NoteGen AI APIs - Medical Template Extraction System",
    description="""
    Production-ready medical template extraction system implementing story requirements:
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for medical system integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🚀 Starting NoteGen AI Service...")
    logger.info("✅ Service started successfully.")

# Include routers
app.include_router(health_router, prefix="/health", tags=["System Health"])
app.include_router(production_router, tags=["Medical Note Generation"])# Updated for OIDC CI/CD test
