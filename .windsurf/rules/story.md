---
trigger: always_on
description: 
globs: 
---
Python API Development Prompt - NoteGen Medical SOAP Extraction Service
Project Overview
Build a production-ready Python microservice for NoteGen that extracts SOAP notes and other medical templates from long encounter transcripts. The service integrates with an existing NestJS backend, implements multi-RAG systems for accurate medical term extraction, and provides precise line-number referencing for complete traceability.
Core Requirements
NoteGen System Capabilities

Multi-Template Support: Extract SOAP, Visit Summary, Referral notes, and custom templates simultaneously
Long Encounter Handling: Process 2+ hour medical encounters without failure
Precise Referencing: Every extracted statement must reference exact line numbers and substrings from transcript
Multilingual Support: Generate extractions in encounter language (English/French)
Hallucination Prevention: Minimize AI hallucinations through strict RAG-based referencing

Data Flow Architecture
NestJS Backend → Python API → Chunk & Store Transcript → Multi-RAG Processing → Template-Based Extraction → Line-Referenced Response → NestJS Backend
Input from NestJS:

Template definitions (SOAP, Visit Summary, Referral, Custom templates)
Prompts array (CSV format: @prompts.csv structure)
Conversation ID (unique identifier for tracking)
Transcription text with line numbers (complete doctor-patient encounter)
Doctor ID (for preference learning)
Doctor preferences dictionary (original_term: replaced_term mappings)

Processing Flow:

Chunk and embed transcript in Vector RAG with line number preservation
Reference GraphRAG (Neo4j SNOMED) for medical term validation
Extract template sections dynamically based on template structure
Store extracted sections in RAG for coherent next-section generation
Return each section with precise line number and substring references

Output to NestJS (per section):

Extracted section content (with medical term validation)
Section ID (unique identifier for the generated section)
Line references (exact line numbers where information was extracted)
Substring references (exact text snippets from transcript)
SNOMED mappings (medical terms validated against GraphRAG)
Confidence scores for hallucination detection

Technical Specifications
Framework & Architecture

Framework: FastAPI (for async performance and automatic API documentation)
Architecture Pattern: Agent-based architecture with multi-RAG integration
On-Premise Requirements: Azure LLM deployment, Canadian data residency
Observability: Langfuse on-premise for patient data protection
API Design: RESTful with comprehensive traceability features

Core Components to Implement
1. API Endpoints
POST /internal/extract/process-encounter    # Main endpoint for template extraction
POST /internal/templates/validate           # Template validation endpoint
GET /internal/doctor-preferences/{doctor_id}
PUT /internal/doctor-preferences/{doctor_id}
GET /internal/health
2. Multi-RAG System Architecture

Vector RAG: Chunked transcript storage with line number preservation
GraphRAG: Neo4j SNOMED Knowledge Graph for medical term validation
Section RAG: Store extracted sections for coherent multi-section generation

3. Summarization Agent Pipeline

Template-Based Extraction: Dynamic section extraction based on template structure
Line-Number Referencing: Precise source tracking for every extracted statement
Medical Term Validation: GraphRAG integration for accurate medical terminology
Multi-Language Support: Language-aware extraction (English/French)

Detailed Implementation Requirements
1. Request/Response Models
Create Pydantic models for:
EncounterExtractionRequest:
python{
  "templates": List[Dict],  # Multiple templates (SOAP, Visit Summary, etc.)
  "prompts": List[Dict],    # Array from @prompts.csv structure
  "conversation_id": str,   # Unique ID sent by NestJS
  "transcription_text": str,  # Complete encounter with line numbers
  "doctor_id": str,
  "doctor_preferences": Dict[str, str],  # {original_term: replaced_term}
  "encounter_language": str  # "en" or "fr"
}
TemplateExtractionResponse:
python{
  "template_type": str,  # "soap", "visit_summary", "referral", "custom"
  "section_type": str,   # "subjective", "objective", etc.
  "section_content": str,
  "section_id": str,
  "line_references": List[int],  # Exact line numbers from transcript
  "substring_references": List[Dict],  # {"line": int, "start": int, "end": int, "text": str}
  "snomed_mappings": List[Dict],  # Medical terms from GraphRAG
  "confidence_score": float,      # Hallucination detection metric
  "extracted_language": str,      # Language of extraction
  "processing_metadata": Dict
}
2. Multi-RAG Implementation Strategy
Vector RAG (Transcript Storage)

Vector Database: AWS open search with metadata support
Chunking Strategy: Semantic chunking with line number preservation
Metadata Storage: Line numbers, speaker identification, timestamp mapping
Embedding Model: Medical-specific multilingual embeddings
Retrieval: Hybrid search with line-number tracking

GraphRAG (SNOMED Knowledge Graph)

Database: Neo4j with SNOMED Canadian edition
Multilingual Support: French and English medical terminology
Relationship Mapping: Complex medical term relationships and hierarchies
Query Optimization: Efficient Cypher queries for real-time term validation
Integration: Real-time medical term validation during extraction

Section RAG (Coherence Management)

Purpose: Store extracted sections for coherent multi-section generation
Storage: In-memory or Redis for session-based coherence
Context Building: Progressive context building across sections
Template Awareness: Section interdependencies within templates

3. Line-Number Referencing System
Transcript Processing

Line Preservation: Maintain exact line numbers during chunking
Substring Tracking: Track character positions within lines
Speaker Attribution: Preserve doctor/patient dialogue attribution
Timestamp Mapping: Optional timestamp preservation for temporal referencing

Reference Extraction

Source Tracking: Every extracted statement links to source lines
Substring Precision: Exact character ranges for transparency
Multi-Source Support: Handle information spanning multiple lines
Validation: Ensure extracted content matches original transcript

4. Template-Based Extraction System
Dynamic Template Processing

Template Parser: Parse various template structures (SOAP, custom, etc.)
Section Identification: Dynamically identify template sections
Dependency Management: Handle section interdependencies
Multi-Template Support: Process multiple templates simultaneously

Extraction Logic

Template-Aware Prompts: Generate section-specific prompts based on template
Context Integration: Include relevant previous sections for coherence
Medical Term Integration: Apply GraphRAG findings during extraction
Language Consistency: Maintain encounter language throughout extraction

5. Doctor Preference Integration
Preference Dictionary System
pythondoctor_preferences = {
    "Hypertension": "HTN",
    "Diabetes Mellitus": "DM",
    "Myocardial Infarction": "MI"
}
Integration Strategy

Prompt Enhancement: Include preference examples in extraction prompts
Real-time Application: Apply preferences during content generation
Consistency Enforcement: Ensure consistent terminology throughout extraction
Learning Integration: Update preferences based on doctor corrections

6. Hallucination Prevention Strategy
RAG-Based Validation

Source Requirement: Every statement must reference transcript source
Medical Term Validation: All medical terms validated against SNOMED GraphRAG
Confidence Scoring: AI-generated confidence scores for each extraction
Fact Checking: Cross-reference extracted information with source material

Quality Assurance

Substring Matching: Ensure extracted content has direct transcript correlation
Medical Accuracy: Validate medical terms against established ontologies
Language Consistency: Ensure extraction language matches encounter language
Completeness Checks: Verify all required template sections are populated

Technology Stack Requirements
Core Dependencies
python# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# On-Premise LLM Integration
azure-ai-ml==1.11.1
azure-identity==1.15.0

# Observability (On-Premise)
langfuse==2.0.0  # On-premise deployment

# Multi-RAG System
pinecone-client==2.2.4
neo4j==5.14.1
py2neo==2021.2.3
redis==5.0.1

# Medical NLP
transformers==4.36.0
sentence-transformers==2.2.2
spacy==3.7.2

# Multilingual Support
polyglot==16.7.4
langdetect==1.0.9

# Data Processing
pandas==2.1.3
numpy==1.25.2
pydantic==2.5.0

# Line Processing
python-csv==1.0
regex==2023.10.3

# Security & Monitoring
cryptography==41.0.8
prometheus-client==0.19.0
structlog==23.2.0
Infrastructure Components

Azure ML: On-premise LLM deployment for Canadian data residency
Langfuse: On-premise observability for patient data protection
Neo4j: SNOMED GraphRAG deployment
Vector Database: AWS open search for transcript storage
Redis: Session management and section coherence

Implementation Phases
Phase 1: Core Infrastructure

FastAPI application with on-premise Azure LLM integration
Multi-RAG system setup (Vector, Graph, Section)
Line-number preservation system implementation
Langfuse on-premise observability integration

Phase 2: Extraction Engine

Template-based extraction system
Line-number referencing implementation
Multilingual processing capabilities
Doctor preference integration system

Phase 3: Quality Assurance

Hallucination prevention mechanisms
Medical term validation through GraphRAG
Confidence scoring and quality metrics
Comprehensive testing and validation

Phase 4: Production Optimization

Performance optimization for long encounters
Advanced monitoring and alerting
Scalability enhancements
Security hardening for healthcare compliance

Core Processing Flow
Encounter Processing Pipeline

Receive Encounter: Parse templates, prompts, and transcript with line numbers
Chunk Transcript: Semantic chunking with line number and substring preservation
Store in Vector RAG: Embed chunks with metadata (line numbers, speakers, timestamps)
Process Templates Simultaneously:

For each template (SOAP, Visit Summary, Referral):

Extract sections dynamically based on template structure
Query Vector RAG for relevant transcript chunks
Validate medical terms through GraphRAG (SNOMED)
Apply doctor preferences from dictionary
Generate section content with line references
Store section in Section RAG for coherence
Return section immediately with references




Quality Assurance: Validate all extractions against source material

Multi-Template Support

Simultaneous Processing: Generate multiple document types from single encounter
Template Registry: Support unlimited custom templates
Section Dependencies: Handle interdependent sections within templates
Coherence Management: Ensure consistency across multiple generated documents

Security & Compliance
Canadian Data Residency

On-Premise Deployment: All AI processing within Canadian infrastructure
Azure Integration: Use Azure Canada regions for LLM deployment
Data Isolation: Complete patient data isolation from external services
Langfuse On-Premise: Patient data never leaves Canadian boundaries

Healthcare Compliance

HIPAA/PIPEDA: Full compliance with healthcare data protection
Audit Trails: Complete logging of all data access and processing
Encryption: End-to-end encryption for all patient data
Access Controls: Role-based access with comprehensive monitoring

Performance Requirements
Long Encounter Handling

✅ Process 2+ hour encounters without failure
✅ Maintain sub-30 second response time per section
✅ Support 50+ concurrent encounter processing
✅ Handle transcripts up to 500,000 words

Accuracy Requirements

✅ 95%+ accuracy in line-number referencing
✅ 98%+ medical term validation accuracy through SNOMED
✅ Minimize hallucinations to <2% of extracted content
✅ Maintain encounter language consistency (French/English)

System Reliability

✅ 99.9% uptime with proper error handling
✅ Graceful degradation for component failures
✅ Complete data recovery and consistency
✅ Real-time monitoring and alerting

Success Criteria
Functional Requirements

✅ Extract multiple templates simultaneously from single encounter
✅ Provide precise line-number and substring references for all extractions
✅ Maintain medical accuracy through SNOMED GraphRAG validation
✅ Support unlimited custom templates per physician/clinic
✅ Apply doctor preferences consistently across all extractions

Technical Requirements

✅ On-premise deployment with Canadian data residency
✅ Integration with Azure LLM services within Canada
✅ Langfuse observability without external data transmission
✅ Multi-RAG architecture with optimal performance
✅ Comprehensive error handling and recovery mechanisms

Quality Assurance

✅ Hallucination detection and prevention
✅ Medical term validation and standardization
✅ Multilingual extraction capability (English/French)
✅ Complete audit trail for compliance and debugging
✅ Seamless integration with existing NestJS backend

Development Guidelines
Focus on creating a robust, compliant, and accurate medical extraction system that prioritizes patient data security, extraction precision, and healthcare workflow integration. Emphasize traceability, medical accuracy, and scalable architecture throughout the development process.


Story:
As notegen I should have the ability to extract SOAP / and other templates for long encounters, so that I can provide the physician with the data they need to store in the EMR and reference for later. 

Acceptance: 

Long transcripts should not fail, and should be chunked for LLM handling. 

When extracted sections come back, statements extracted (or summarized) should reference back the correct line numbers & substrings in transcript where the information was extracted. 

Hallucinations should be minimized / eliminated when possible. 

The extraction / summarization must be in the language of the encounter. (English/ French) 

Technical notes:

Implement a summarization agent that deals with 2 RAG systems (potentially 3 TBD)

RAG:  The transcript must be chunked, embedded and stored in a vector store for the summarization agent to reference. 

GraphRag: the agent must reference GraphRag with SNOMED model so that the correct medical terms for medications, symptoms, diagnosis, and other relevant procedures are correctly referenced. 

The agent must summarize the notes according to the section being extracted based on the  Template  by referencing the relevant chunks from the transcript, along with the GraphRag for detecting the medical terms.  See https://instaclinic-ai.atlassian.net/browse/NE-14  for reference. "Description

PCP and Clinic can create an unlimited number of templates based on their preferences and speciality needs. 

Multiple documents can be generated from a single encounter simultaneously without the need for toggling between different formats/types. 

For example once encounter has been transcribed, the physician can simultaneously generate the SOAP Note, a Visit Summary, and a Referral note. Those documents are available and can be referenced at any time. and can seemlessly be viewed. All of them are stored and will continue to be available as long as the transcription record exists and is not deleted along with the additional documents. 

in addition with custom integration to EMR, it is possible to reference additional data from EMR into the documents generation without the need for uploading those. "

The Agent must extract based on the template of the encounter (SOAP, other), where sections are dynamic. 

The sections extracted can be stored in the RAG and referenced for the next section generation, so that the notes generated are coherent. 


NestJS will send us an array of prompts (such as S, O, A, P, and potentially others) along with a conversation transcription between a doctor and a patient.

Step-by-Step Breakdown
1. Store the Transcription into AWS open search (Vector RAG)
You will save the full transcription into AWS open search (a vector database).

The connection details for AWS open search are already added in the .env file as AWS open search_Key.

Reference AWS open search documentation:

AWS open search Python Client

AWS open search Developer Docs

2. Isolate Each Conversation
Each transcription will come with a unique conversation ID (e.g., xxxccx).

Use this ID to:

Save the transcription in AWS open search.

Isolate and tag all related prompt sections (S, O, A, P, etc.).

Avoid mixing data from different conversations.
3. Process and Generate Prompt Sections
After saving the transcription to AWS open search:

Loop through the array of prompt types (e.g., S, O, A, P).

Generate the content for each prompt using the stored transcription.

Use SNOMED codes for mapping medical terms — integrate Neo4j GRAPH RAG for this.

4. Store Generated Prompt Outputs
For now, store the generated prompt outputs in a file or temporary database.

Later, we’ll integrate a real-time NestJS API to handle this.

Example: After generating the O section, you will store it and mark it as #TO:DO until the API is ready.

5. Doctor Preferences
Use a dictionary to handle doctor-specific terminology or preferences.

This dictionary maps custom terms to their standard forms.

Pass this dictionary to the prompt generator to customize outputs.

6. Tech Stack
Use:

AWS open search for storing transcriptions as vector data.

Neo4j + SNOMED for medical term mapping.

Azure OpenAI for language generation tasks.
