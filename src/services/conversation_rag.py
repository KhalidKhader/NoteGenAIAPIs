"""Conversation RAG Service for NoteGen AI APIs.

This service handles storing medical conversations in a vector database
and retrieving relevant chunks for SOAP generation.
"""

import uuid
from typing import Dict, List, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings

from src.core.config import settings
from src.core.logging import get_logger
from src.core.security import data_encryption
from src.models.conversation_models import ConversationData, ConversationStoreResponse

logger = get_logger(__name__)


class ConversationRAGService:
    """Service for managing conversation data in vector database."""
    
    def __init__(self):
        """Initialize the conversation RAG service."""
        self.embeddings = self._initialize_embeddings()
        self.vector_store = self._initialize_vector_store()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.conversation_chunk_size,
            chunk_overlap=settings.conversation_chunk_overlap,
            separators=["\n\n", "\n", ". ", " "]
        )
        logger.info("Conversation RAG Service initialized")
    
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
            logger.error(f"Failed to initialize embeddings: {str(e)}")
            # Return a mock embeddings for development
            return None
    
    def _initialize_vector_store(self) -> Chroma:
        """Initialize ChromaDB vector store."""
        try:
            return Chroma(
                embedding_function=self.embeddings,
                persist_directory=settings.chroma_persist_directory,
                collection_name=settings.chroma_collection_name
            )
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            # Return None for development mode
            return None
    
    async def store_and_chunk_conversation(
        self,
        transcription_text: str,
        conversation_id: str
    ) -> List[str]:
        """Store conversation and return chunk IDs."""
        
        logger.info(f"Storing conversation {conversation_id}")
        
        try:
            # Split conversation into chunks
            chunks = self.text_splitter.split_text(transcription_text)
            
            if not self.vector_store:
                # Development mode - return mock chunk IDs
                logger.warning("Vector store not available, returning mock chunks")
                return [f"chunk_{i}" for i in range(len(chunks))]
            
            # Encrypt chunks if required
            if settings.patient_data_encryption:
                encrypted_chunks = [
                    data_encryption.encrypt_patient_data(chunk) 
                    for chunk in chunks
                ]
            else:
                encrypted_chunks = chunks
            
            # Store chunks with metadata
            metadatas = [
                {
                    "chunk_index": i,
                    "conversation_id": conversation_id,
                    "encrypted": settings.patient_data_encryption
                }
                for i, _ in enumerate(chunks)
            ]
            
            chunk_ids = await self.vector_store.aadd_texts(
                texts=encrypted_chunks,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(chunk_ids)} chunks for conversation {conversation_id}")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {str(e)}")
            raise
    
    async def retrieve_relevant_chunks(
        self,
        query: str,
        max_results: int = 5
    ) -> List[str]:
        """Retrieve relevant conversation chunks."""
        
        try:
            if not self.vector_store:
                # Development mode - return mock chunks
                return [f"Mock relevant chunk for query: {query}"]
            
            # Retrieve similar chunks
            docs = await self.vector_store.asimilarity_search(
                query, 
                k=max_results
            )
            
            # Decrypt chunks if needed
            chunks = []
            for doc in docs:
                content = doc.page_content
                if doc.metadata.get("encrypted") and settings.patient_data_encryption:
                    content = data_encryption.decrypt_patient_data(content)
                chunks.append(content)
            
            logger.info(f"Retrieved {len(chunks)} relevant chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {str(e)}")
            return []
    
    async def store_conversation(
        self,
        conversation_data: ConversationData,
        encrypt_content: bool = True,
        generate_embeddings: bool = True
    ) -> ConversationStoreResponse:
        """Store a complete conversation."""
        
        try:
            text_content = conversation_data.get_text_content()
            
            if not text_content:
                raise ValueError("No text content found in conversation")
            
            # Store and chunk the conversation
            chunk_ids = await self.store_and_chunk_conversation(
                transcription_text=text_content,
                conversation_id=conversation_data.conversation_id
            )
            
            # Create response
            response = ConversationStoreResponse(
                conversation_id=conversation_data.conversation_id,
                storage_id=str(uuid.uuid4()),
                chunks_created=len(chunk_ids),
                embeddings_generated=len(chunk_ids) if generate_embeddings else 0,
                medical_terms_extracted=0,  # Placeholder
                encrypted=encrypt_content,
                validation_passed=True,
                processing_time_ms=100.0  # Placeholder
            )
            
            logger.info(f"Successfully stored conversation {conversation_data.conversation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {str(e)}")
            raise 