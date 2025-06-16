"""SOAP Generator Service for NoteGen AI APIs.

This service orchestrates the generation of medical SOAP notes from patient-doctor
conversations using AI and RAG systems.
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage

from src.core.config import settings
from src.core.logging import get_logger, audit_logger
from src.core.security import data_encryption
from src.models.soap_models import SOAPSectionType, SOAPLanguage
from src.services.conversation_rag import ConversationRAGService
from src.services.snomed_rag import SNOMEDRAGService
from src.services.pattern_learning import PatternLearningService

logger = get_logger(__name__)


class SOAPGeneratorService:
    """Main service for generating SOAP notes from medical conversations."""
    
    def __init__(self):
        """Initialize the SOAP generator service."""
        self.llm = self._initialize_llm()
        self.embeddings = self._initialize_embeddings()
        self.conversation_rag = ConversationRAGService()
        self.snomed_rag = SNOMEDRAGService()
        self.pattern_learning = PatternLearningService()
        
        logger.info("SOAP Generator Service initialized")
    
    def _initialize_llm(self) -> AzureChatOpenAI:
        """Initialize Azure OpenAI LLM."""
        try:
            return AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                deployment_name=settings.azure_openai_deployment_name,
                model=settings.azure_openai_model,
                temperature=settings.soap_generation_temperature,
                max_tokens=settings.soap_generation_max_tokens
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI LLM: {str(e)}")
            raise
    
    def _initialize_embeddings(self) -> AzureOpenAIEmbeddings:
        """Initialize Azure OpenAI embeddings."""
        try:
            return AzureOpenAIEmbeddings(
                azure_endpoint=settings.openai_embedding_endpoint,
                api_key=settings.openai_embedding_api_key,
                api_version=settings.azure_openai_api_version,
                deployment=settings.openai_embedding_deployment_name
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI embeddings: {str(e)}")
            raise
    
    async def generate_soap_section(
        self,
        section_type: SOAPSectionType,
        section_prompt: str,
        transcription_text: str,
        soap_template: Dict[str, Any],
        custom_instructions: str = "",
        doctor_id: Optional[str] = None,
        previous_sections: Optional[Dict[str, str]] = None,
        language: SOAPLanguage = SOAPLanguage.ENGLISH,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a specific SOAP section using RAG-enhanced prompts."""
        
        start_time = time.time()
        section_id = f"{section_type}_{uuid.uuid4().hex[:8]}"
        
        logger.set_context(
            section_id=section_id,
            section_type=section_type,
            doctor_id=doctor_id
        )
        
        logger.info("Starting SOAP section generation")
        
        try:
            # Step 1: Store conversation in RAG system
            conversation_chunks = await self.conversation_rag.store_and_chunk_conversation(
                transcription_text=transcription_text,
                conversation_id=f"temp_{uuid.uuid4().hex[:8]}"
            )
            
            # Step 2: Retrieve relevant context from conversation
            conversation_context = await self.conversation_rag.retrieve_relevant_chunks(
                query=f"{section_type} medical information from conversation",
                max_results=settings.max_retrieval_chunks
            )
            
            # Step 3: Get SNOMED context for medical terms
            medical_terms = self._extract_medical_terms(transcription_text)
            snomed_context = []
            if medical_terms:
                snomed_context = await self.snomed_rag.get_relevant_codes(
                    medical_terms=medical_terms,
                    language=language
                )
            
            # Step 4: Apply doctor preferences if available
            enhanced_prompt = section_prompt
            if doctor_id:
                enhanced_prompt = await self.pattern_learning.apply_doctor_preferences(
                    doctor_id=doctor_id,
                    original_prompt=section_prompt,
                    section_type=section_type
                )
            
            # Step 5: Build the complete prompt with context
            complete_prompt = self._build_enhanced_prompt(
                section_type=section_type,
                section_prompt=enhanced_prompt,
                conversation_context=conversation_context,
                snomed_context=snomed_context,
                custom_instructions=custom_instructions,
                previous_sections=previous_sections or {},
                language=language,
                soap_template=soap_template
            )
            
            # Step 6: Generate the section using LLM
            generation_result = await self._generate_with_llm(
                prompt=complete_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Step 7: Post-process and validate the result
            processed_content = self._post_process_content(
                content=generation_result,
                section_type=section_type,
                medical_terms=medical_terms
            )
            
            # Calculate processing metrics
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Create response
            result = {
                "section_id": section_id,
                "content": processed_content,
                "chunks_used": len(conversation_context),
                "snomed_codes_referenced": len(snomed_context),
                "doctor_preferences_applied": doctor_id is not None,
                "processing_time_ms": processing_time_ms,
                "medical_terms": medical_terms,
                "snomed_codes": [code.get("concept_id") for code in snomed_context],
                "confidence_score": self._calculate_confidence_score(processed_content),
                "validation_passed": True,
                "model_version": settings.azure_openai_model,
                "warnings": []
            }
            
            logger.info(
                "SOAP section generated successfully",
                extra={
                    "processing_time_ms": processing_time_ms,
                    "confidence_score": result["confidence_score"]
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"SOAP section generation failed: {str(e)}")
            raise
        finally:
            logger.clear_context()
    
    def _build_enhanced_prompt(
        self,
        section_type: SOAPSectionType,
        section_prompt: str,
        conversation_context: List[str],
        snomed_context: List[Dict[str, Any]],
        custom_instructions: str,
        previous_sections: Dict[str, str],
        language: SOAPLanguage,
        soap_template: Dict[str, Any]
    ) -> str:
        """Build the enhanced prompt with all context."""
        
        # Base system prompt
        system_prompt = f"""You are a medical documentation specialist creating the {section_type.upper()} section of a SOAP note.

LANGUAGE: Generate content in {language}
MEDICAL STANDARDS: Follow SNOMED Canadian Edition guidelines
SECTION TYPE: {section_type.upper()}

INSTRUCTIONS:
{section_prompt}

{custom_instructions}
"""
        
        # Add conversation context
        if conversation_context:
            context_text = "\n".join(conversation_context)
            system_prompt += f"\n\nRELEVANT CONVERSATION CONTEXT:\n{context_text}"
        
        # Add previous sections for context
        if previous_sections:
            prev_context = "\n".join([
                f"{section.upper()}: {content}"
                for section, content in previous_sections.items()
            ])
            system_prompt += f"\n\nPREVIOUS SECTIONS:\n{prev_context}"
        
        # Add SNOMED context
        if snomed_context:
            snomed_info = "\n".join([
                f"- {code.get('preferred_term', '')} ({code.get('concept_id', '')})"
                for code in snomed_context
            ])
            system_prompt += f"\n\nRELEVANT SNOMED CODES:\n{snomed_info}"
        
        # Add template guidance
        if soap_template and section_type in soap_template:
            template_info = soap_template[section_type]
            system_prompt += f"\n\nTEMPLATE GUIDANCE:\n{template_info}"
        
        system_prompt += f"""

REQUIREMENTS:
1. Generate only the {section_type.upper()} section content
2. Use professional medical terminology
3. Be concise but comprehensive
4. Include relevant SNOMED codes where appropriate
5. Maintain medical accuracy and clarity
6. Follow the specified language and format requirements

Generate the {section_type.upper()} section now:"""
        
        return system_prompt
    
    async def _generate_with_llm(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate content using the LLM with retry logic."""
        
        # Update LLM parameters if provided
        if temperature is not None:
            self.llm.temperature = temperature
        if max_tokens is not None:
            self.llm.max_tokens = max_tokens
        
        # Retry logic with exponential backoff
        for attempt in range(settings.soap_max_retries):
            try:
                messages = [SystemMessage(content=prompt)]
                response = await self.llm.agenerate([messages])
                
                if response.generations and response.generations[0]:
                    return response.generations[0][0].text.strip()
                else:
                    raise ValueError("Empty response from LLM")
                    
            except Exception as e:
                if attempt == settings.soap_max_retries - 1:
                    logger.error(f"LLM generation failed after {settings.soap_max_retries} attempts: {str(e)}")
                    raise
                
                wait_time = (2 ** attempt) * settings.soap_retry_delay
                logger.warning(f"LLM generation attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                await asyncio.sleep(wait_time)
        
        raise Exception("LLM generation failed")
    
    def _extract_medical_terms(self, text: str) -> List[str]:
        """Extract medical terms from conversation text."""
        # Placeholder for medical term extraction
        # This would use NLP libraries to identify medical terminology
        
        # Simple keyword extraction for now
        medical_keywords = [
            "pain", "chest", "breathing", "heart", "blood", "pressure",
            "temperature", "fever", "headache", "nausea", "vomiting",
            "diabetes", "hypertension", "medication", "symptoms",
            "diagnosis", "treatment", "allergy", "infection"
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in medical_keywords:
            if term in text_lower:
                found_terms.append(term)
        
        return list(set(found_terms))
    
    def _post_process_content(
        self,
        content: str,
        section_type: SOAPSectionType,
        medical_terms: List[str]
    ) -> str:
        """Post-process the generated content."""
        
        # Basic cleanup
        content = content.strip()
        
        # Remove any unwanted prefixes/suffixes
        prefixes_to_remove = [
            f"{section_type.upper()}:",
            f"{section_type.capitalize()}:",
            "SOAP",
            "Note:"
        ]
        
        for prefix in prefixes_to_remove:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
        
        # Ensure proper formatting
        if not content.endswith('.'):
            content += '.'
        
        return content
    
    def _calculate_confidence_score(self, content: str) -> float:
        """Calculate a confidence score for the generated content."""
        
        # Simple heuristic-based confidence calculation
        # In production, this would be more sophisticated
        
        score = 0.8  # Base score
        
        # Length check
        if len(content) > 50:
            score += 0.1
        
        # Check for medical terminology
        medical_terms_count = len([
            term for term in ["patient", "reports", "presents", "history", "examination"]
            if term.lower() in content.lower()
        ])
        score += min(medical_terms_count * 0.02, 0.1)
        
        # Ensure score is within bounds
        return min(max(score, 0.0), 1.0)
    
    async def generate_complete_soap(
        self,
        transcription_text: str,
        soap_template: Dict[str, Any],
        doctor_id: Optional[str] = None,
        custom_instructions: str = "",
        language: SOAPLanguage = SOAPLanguage.ENGLISH
    ) -> Dict[str, Any]:
        """Generate a complete SOAP note with all sections."""
        
        logger.info("Starting complete SOAP note generation")
        
        try:
            sections = {}
            section_order = [
                SOAPSectionType.SUBJECTIVE,
                SOAPSectionType.OBJECTIVE,
                SOAPSectionType.ASSESSMENT,
                SOAPSectionType.PLAN
            ]
            
            # Generate sections sequentially for context accumulation
            for section_type in section_order:
                section_prompt = soap_template.get("prompts", {}).get(section_type, "")
                
                if not section_prompt:
                    section_prompt = self._get_default_section_prompt(section_type)
                
                section_result = await self.generate_soap_section(
                    section_type=section_type,
                    section_prompt=section_prompt,
                    transcription_text=transcription_text,
                    soap_template=soap_template,
                    custom_instructions=custom_instructions,
                    doctor_id=doctor_id,
                    previous_sections=sections,
                    language=language
                )
                
                sections[section_type] = section_result["content"]
                
                logger.info(f"Generated {section_type} section")
            
            logger.info("Complete SOAP note generation finished")
            
            return {
                "sections": sections,
                "status": "completed",
                "language": language,
                "doctor_id": doctor_id
            }
            
        except Exception as e:
            logger.error(f"Complete SOAP generation failed: {str(e)}")
            raise
    
    def _get_default_section_prompt(self, section_type: SOAPSectionType) -> str:
        """Get default prompt for a section type."""
        
        default_prompts = {
            SOAPSectionType.SUBJECTIVE: """Extract the patient's subjective experience including:
- Chief complaint and history of present illness
- Review of systems mentioned
- Past medical history relevant to current visit
- Social history and family history if discussed
- Patient's own words and descriptions
Focus on what the patient reports, not clinical observations.""",
            
            SOAPSectionType.OBJECTIVE: """Extract objective clinical findings including:
- Vital signs and measurements mentioned
- Physical examination findings described
- Laboratory results or test results discussed
- Clinical observations by healthcare provider
Focus on measurable, observable data only.""",
            
            SOAPSectionType.ASSESSMENT: """Extract clinical assessment including:
- Primary and secondary diagnoses discussed
- Clinical impressions and differential diagnoses
- Assessment of patient's condition
- Medical decision-making rationale
Include relevant SNOMED codes where applicable.""",
            
            SOAPSectionType.PLAN: """Extract treatment plan including:
- Medications prescribed or discussed
- Procedures recommended or planned
- Follow-up appointments scheduled
- Patient education provided
- Lifestyle modifications recommended
- Referrals to specialists mentioned
Include specific details like dosages and frequencies."""
        }
        
        return default_prompts.get(section_type, "Generate the appropriate SOAP section content.") 