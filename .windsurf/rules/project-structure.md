---
trigger: always_on
description: Project structure and organization guidelines
globs: *.py,*.toml,Makefile
---

# NoteGen AI APIs Project Structure

This document outlines the project structure and organization for the medical SOAP note generation system using LangChain, Azure OpenAI, and Neo4j.

## System Architecture Overview

### Core Components
- **NestJS Backend** (pre-built): API Gateway that sends SOAP templates, prompts, and transcription data
- **Python AI Service**: Processes SOAP generation using LangChain and Azure OpenAI
- **Conversation RAG**: Vector database for storing conversation chunks
- **SNOMED RAG**: Neo4j knowledge graph with SNOMED Canadian edition (pre-existing)
- **Pattern Learning**: Doctor preference adaptation system

### Data Flow
```
NestJS Backend → Python AI Service → RAG Systems → Azure OpenAI → Generated SOAP Sections → NestJS Backend
```

## Project Directory Structure

```
notegen-ai-apis/
├── pyproject.toml              # Poetry configuration and dependencies
├── Makefile                    # Development automation commands
├── README.md                   # Project documentation
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── docker-compose.yml         # Docker services (optional vector DB)
│
├── src/                       # Main application source code
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   │
│   ├── api/                  # API endpoints and routes
│   │   ├── __init__.py
│   │   ├── health.py         # Health check endpoints
│   │   ├── soap.py           # SOAP generation endpoints
│   │   └── dependencies.py   # API dependencies and middleware
│   │
│   ├── services/             # Business logic services
│   │   ├── __init__.py
│   │   ├── soap_generator.py      # Main SOAP generation service
│   │   ├── conversation_rag.py    # Conversation RAG service
│   │   ├── snomed_rag.py          # SNOMED knowledge graph service
│   │   ├── pattern_learning.py    # Doctor preference learning
│   │   ├── langchain_service.py   # LangChain integration service
│   │   └── chunking_service.py    # Conversation chunking service
│   │
│   ├── models/               # Pydantic models and schemas
│   │   ├── __init__.py
│   │   ├── soap_models.py    # SOAP note data models
│   │   ├── conversation_models.py # Conversation data models
│   │   ├── rag_models.py     # RAG query/response models
│   │   └── api_models.py     # API request/response models
│   │
│   ├── config/               # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py       # Application settings
│   │   ├── logging.py        # Logging configuration
│   │   └── security.py       # Security configuration
│   │
│   ├── utils/                # Utility functions and helpers
│   │   ├── __init__.py
│   │   ├── text_processing.py # Text processing utilities
│   │   ├── medical_utils.py   # Medical data processing
│   │   ├── encryption.py      # Data encryption utilities
│   │   └── audit_logger.py    # Audit logging utilities
│   │
│   ├── prompts/              # LangChain prompt templates
│   │   ├── __init__.py
│   │   ├── soap_prompts.py   # SOAP section prompts
│   │   ├── rag_prompts.py    # RAG query prompts
│   │   └── system_prompts.py # System-level prompts
│   │
│   └── exceptions/           # Custom exception classes
│       ├── __init__.py
│       ├── soap_exceptions.py # SOAP generation exceptions
│       ├── rag_exceptions.py  # RAG system exceptions
│       └── api_exceptions.py  # API-specific exceptions
│
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration and fixtures
│   │
│   ├── unit/                # Unit tests
│   │   ├── __init__.py
│   │   ├── test_soap_generator.py
│   │   ├── test_conversation_rag.py
│   │   ├── test_snomed_rag.py
│   │   ├── test_pattern_learning.py
│   │   └── test_chunking_service.py
│   │
│   ├── integration/         # Integration tests
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_rag_integration.py
│   │   └── test_langchain_integration.py
│   │
│   └── fixtures/            # Test data and fixtures
│       ├── sample_conversations.json
│       ├── sample_soap_notes.json
│       └── mock_responses.json
│
├── logs/                    # Application logs (created at runtime)
├── conversation_rag_db/     # Vector database storage (created at runtime)
└── docs/                    # Additional documentation
    ├── api_documentation.md
    ├── deployment_guide.md
    └── architecture_diagrams/
```

### DONT:
!!! DONT: create new codes without cleaning the old codes !!!
!!! DONT: create .sh files, use make files instead !!!
!!! DONT: use the base .env, use poetry !!!

## Core Service Implementations

### 1. SOAP Generator Service
```python
# src/services/soap_generator.py
from typing import Dict, List, Any
from langchain_openai import AzureChatOpenAI
from src.services.conversation_rag import ConversationRAGService
from src.services.snomed_rag import SNOMEDRAGService
from src.services.pattern_learning import PatternLearningService

class SOAPGeneratorService:
    """Main service for generating SOAP notes from medical conversations"""
    
    def __init__(
        self,
        llm: AzureChatOpenAI,
        conversation_rag: ConversationRAGService,
        snomed_rag: SNOMEDRAGService,
        pattern_learning: PatternLearningService
    ):
        self.llm = llm
        self.conversation_rag = conversation_rag
        self.snomed_rag = snomed_rag
        self.pattern_learning = pattern_learning
    
    async def generate_soap_section(
        self,
        section_type: str,
        section_prompt: str,
        transcription_text: str,
        soap_template: Dict[str, Any],
        custom_instructions: str = "",
        doctor_id: str = None
    ) -> Dict[str, Any]:
        """Generate a specific SOAP section using RAG-enhanced prompts"""
        
        # Store conversation in RAG
        await self.conversation_rag.store_conversation(transcription_text)
        
        # Retrieve relevant context
        conversation_context = await self.conversation_rag.retrieve_relevant_chunks(
            query=f"{section_type} medical information",
            k=5
        )
        
        # Get SNOMED context
        snomed_context = await self.snomed_rag.get_relevant_codes(
            medical_terms=self._extract_medical_terms(transcription_text)
        )
        
        # Apply doctor preferences if available
        if doctor_id:
            section_prompt = await self.pattern_learning.apply_doctor_preferences(
                doctor_id=doctor_id,
                original_prompt=section_prompt
            )
        
        # Generate section using enhanced prompt
        enhanced_prompt = self._build_enhanced_prompt(
            section_prompt=section_prompt,
            conversation_context=conversation_context,
            snomed_context=snomed_context,
            custom_instructions=custom_instructions
        )
        
        response = await self.llm.agenerate([enhanced_prompt])
        
        return {
            "section_id": f"{section_type}_{uuid.uuid4()}",
            "content": response.generations[0][0].text,
            "section_type": section_type,
            "processing_metadata": {
                "chunks_used": len(conversation_context),
                "snomed_codes_referenced": len(snomed_context),
                "doctor_preferences_applied": doctor_id is not None
            }
        }
```

### 2. Conversation RAG Service
```python
# src/services/conversation_rag.py
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from src.utils.encryption import encrypt_sensitive_data

class ConversationRAGService:
    """Service for managing conversation data in vector database"""
    
    def __init__(self, vector_store: Chroma, embeddings: AzureOpenAIEmbeddings):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " "]
        )
    
    async def store_conversation(self, conversation_text: str) -> List[str]:
        """Store conversation chunks in vector database with encryption"""
        
        # Split conversation into chunks
        chunks = self.text_splitter.split_text(conversation_text)
        
        # Encrypt sensitive chunks
        encrypted_chunks = [
            encrypt_sensitive_data(chunk) for chunk in chunks
        ]
        
        # Store in vector database
        chunk_ids = await self.vector_store.aadd_texts(
            texts=encrypted_chunks,
            metadatas=[
                {
                    "chunk_index": i,
                    "conversation_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "encrypted": True
                }
                for i, _ in enumerate(chunks)
            ]
        )
        
        return chunk_ids
    
    async def retrieve_relevant_chunks(
        self, 
        query: str, 
        k: int = 5
    ) -> List[str]:
        """Retrieve and decrypt relevant conversation chunks"""
        
        # Retrieve similar chunks
        docs = await self.vector_store.asimilarity_search(query, k=k)
        
        # Decrypt chunks
        decrypted_chunks = [
            decrypt_sensitive_data(doc.page_content) 
            for doc in docs
        ]
        
        return decrypted_chunks
```

### 3. SNOMED RAG Service
```python
# src/services/snomed_rag.py
from langchain_neo4j import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from typing import List, Dict, Any

class SNOMEDRAGService:
    """Service for querying SNOMED knowledge graph"""
    
    def __init__(self, neo4j_graph: Neo4jGraph, llm):
        self.graph = neo4j_graph
        self.cypher_chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=neo4j_graph,
            verbose=True
        )
    
    async def get_relevant_codes(
        self, 
        medical_terms: List[str]
    ) -> List[Dict[str, Any]]:
        """Get relevant SNOMED codes for medical terms"""
        
        snomed_codes = []
        
        for term in medical_terms:
            # Query SNOMED graph for relevant codes
            query = f"""
            MATCH (c:Concept)-[:HAS_DESCRIPTION]->(d:Description)
            WHERE d.term CONTAINS '{term}' OR d.term =~ '(?i).*{term}.*'
            RETURN c.conceptId, c.preferredTerm, d.term, c.definitionStatus
            LIMIT 5
            """
            
            result = await self.graph.query(query)
            
            for record in result:
                snomed_codes.append({
                    "concept_id": record["c.conceptId"],
                    "preferred_term": record["c.preferredTerm"],
                    "description": record["d.term"],
                    "definition_status": record["c.definitionStatus"],
                    "matched_term": term
                })
        
        return snomed_codes
    
    async def get_code_hierarchy(self, concept_id: str) -> Dict[str, Any]:
        """Get hierarchical relationships for a SNOMED concept"""
        
        query = f"""
        MATCH (child:Concept {{conceptId: '{concept_id}'}})-[:IS_A*]->(parent:Concept)
        RETURN parent.conceptId, parent.preferredTerm
        ORDER BY length(path) DESC
        LIMIT 10
        """
        
        result = await self.graph.query(query)
        
        return {
            "concept_id": concept_id,
            "hierarchy": [
                {
                    "parent_id": record["parent.conceptId"],
                    "parent_term": record["parent.preferredTerm"]
                }
                for record in result
            ]
        }
```

### 4. Pattern Learning Service
```python
# src/services/pattern_learning.py
from typing import Dict, List, Any
import json
from pathlib import Path

class PatternLearningService:
    """Service for learning and applying doctor preferences"""
    
    def __init__(self):
        self.patterns_file = Path("doctor_patterns.json")
        self.doctor_patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load existing doctor patterns from storage"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_patterns(self):
        """Save patterns to persistent storage"""
        with open(self.patterns_file, 'w') as f:
            json.dump(self.doctor_patterns, f, indent=2)
    
    async def learn_from_modification(
        self,
        doctor_id: str,
        original_text: str,
        modified_text: str,
        section_type: str
    ):
        """Learn from doctor modifications to generated content"""
        
        if doctor_id not in self.doctor_patterns:
            self.doctor_patterns[doctor_id] = {
                "terminology_preferences": {},
                "style_preferences": {},
                "modification_count": 0
            }
        
        # Extract terminology changes
        terminology_changes = self._extract_terminology_changes(
            original_text, modified_text
        )
        
        # Update patterns
        for original_term, preferred_term in terminology_changes.items():
            self.doctor_patterns[doctor_id]["terminology_preferences"][original_term] = {
                "preferred_term": preferred_term,
                "confidence": self._calculate_confidence(doctor_id, original_term),
                "section_types": [section_type],
                "last_updated": datetime.utcnow().isoformat()
            }
        
        self.doctor_patterns[doctor_id]["modification_count"] += 1
        self._save_patterns()
    
    async def apply_doctor_preferences(
        self,
        doctor_id: str,
        original_prompt: str
    ) -> str:
        """Apply learned doctor preferences to prompts"""
        
        if doctor_id not in self.doctor_patterns:
            return original_prompt
        
        preferences = self.doctor_patterns[doctor_id]["terminology_preferences"]
        
        # Add preference instructions to prompt
        preference_instructions = []
        for original_term, pref_data in preferences.items():
            if pref_data["confidence"] > 0.7:  # High confidence threshold
                preference_instructions.append(
                    f"Use '{pref_data['preferred_term']}' instead of '{original_term}'"
                )
        
        if preference_instructions:
            enhanced_prompt = f"""
            {original_prompt}
            
            Doctor-specific preferences:
            {chr(10).join(preference_instructions)}
            """
            return enhanced_prompt
        
        return original_prompt
```

## API Endpoint Structure

### FastAPI Application Setup
```python
# src/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
from src.config.logging import setup_logging
from src.api import health, soap
from src.services.langchain_service import LangChainService

# Setup logging
setup_logging(settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="NoteGen AI APIs",
    description="Medical SOAP note generation using AI and RAG systems",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(soap.router, prefix="/api/v1/soap", tags=["soap"])

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    # Initialize LangChain services
    app.state.langchain_service = LangChainService()
```

### SOAP Generation Endpoints
```python
# src/api/soap.py
from fastapi import APIRouter, Depends, HTTPException
from src.models.api_models import SOAPGenerationRequest, SOAPGenerationResponse
from src.services.soap_generator import SOAPGeneratorService

router = APIRouter()

@router.post("/generate-section", response_model=SOAPGenerationResponse)
async def generate_soap_section(
    request: SOAPGenerationRequest,
    soap_service: SOAPGeneratorService = Depends(get_soap_service)
):
    """Generate a specific SOAP section from conversation data"""
    
    try:
        result = await soap_service.generate_soap_section(
            section_type=request.section_type,
            section_prompt=request.section_prompt,
            transcription_text=request.transcription_text,
            soap_template=request.soap_template,
            custom_instructions=request.custom_instructions,
            doctor_id=request.doctor_id
        )
        
        return SOAPGenerationResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SOAP generation failed: {str(e)}"
        )

@router.post("/store-conversation")
async def store_conversation(
    conversation_data: Dict[str, Any],
    conversation_rag: ConversationRAGService = Depends(get_conversation_rag)
):
    """Store conversation data in RAG system"""
    
    chunk_ids = await conversation_rag.store_conversation(
        conversation_data["transcription_text"]
    )
    
    return {"message": "Conversation stored successfully", "chunk_ids": chunk_ids}
```

## Configuration Management

### Pydantic Settings
```python
# src/config/settings.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application settings
    app_name: str = "NoteGen AI APIs"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Azure OpenAI settings
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_api_version: str = "2024-05-01-preview"
    azure_openai_model: str = "gpt-4"
    
    # Embedding settings
    openai_embedding_endpoint: str
    openai_embedding_api_key: str
    openai_embedding_deployment_name: str = "text-embedding-ada-002"
    
    # Neo4j settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str
    neo4j_database: str = "neo4j"
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # LangFuse settings
    langfuse_secret_key: str
    langfuse_public_key: str
    langfuse_host: str = "https://us.cloud.langfuse.com"
    
    # RAG settings
    vector_db_path: str = "./conversation_rag_db"
    conversation_chunk_size: int = 1500
    conversation_chunk_overlap: int = 150
    max_retrieval_chunks: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

## Testing Structure

### Test Configuration
```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.services.soap_generator import SOAPGeneratorService

@pytest.fixture
def mock_llm():
    """Mock Azure OpenAI LLM"""
    mock = AsyncMock()
    mock.agenerate.return_value = MagicMock(
        generations=[[MagicMock(text="Generated SOAP content")]]
    )
    return mock

@pytest.fixture
def mock_conversation_rag():
    """Mock conversation RAG service"""
    mock = AsyncMock()
    mock.store_conversation.return_value = ["chunk_id_1", "chunk_id_2"]
    mock.retrieve_relevant_chunks.return_value = ["relevant chunk 1", "relevant chunk 2"]
    return mock

@pytest.fixture
def mock_snomed_rag():
    """Mock SNOMED RAG service"""
    mock = AsyncMock()
    mock.get_relevant_codes.return_value = [
        {"concept_id": "12345", "preferred_term": "Hypertension"}
    ]
    return mock

@pytest.fixture
def soap_generator_service(mock_llm, mock_conversation_rag, mock_snomed_rag):
    """Create SOAP generator service with mocked dependencies"""
    return SOAPGeneratorService(
        llm=mock_llm,
        conversation_rag=mock_conversation_rag,
        snomed_rag=mock_snomed_rag,
        pattern_learning=AsyncMock()
    )
```

## Development Workflow

### Makefile Commands
```makefile
# Makefile for NoteGen AI APIs

.PHONY: install dev test lint format clean docker-up docker-down

# Install dependencies
install:
	poetry install

# Run development server
dev:
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests with coverage
test:
	poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Lint code
lint:
	poetry run ruff check src/
	poetry run mypy src/

# Format code
format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf .coverage htmlcov/

# Docker operations
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Neo4j operations
neo4j-status:
	docker ps | grep neo4j

neo4j-connect:
	docker exec -it neo4j-container cypher-shell -u neo4j

# Development utilities
deps-update:
	poetry update

deps-export:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

# Run specific test categories
test-unit:
	poetry run pytest tests/unit/ -v

test-integration:
	poetry run pytest tests/integration/ -v

# Security and compliance
security-scan:
	poetry run bandit -r src/

audit-deps:
	poetry audit
