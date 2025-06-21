"""Configuration management for NoteGen AI APIs.

This module provides centralized configuration management using Pydantic Settings,
handling all environment variables and application settings for the medical
SOAP generation microservice.
"""

import os
from functools import lru_cache
from typing import List

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # =============================================================================
    # Application Settings
    # =============================================================================
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")

    # =============================================================================
    # CORS Configuration
    # =============================================================================
    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:8000,http://localhost:8005",
        description="CORS origins (comma-separated)",
        alias="cors_origins",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        return self._parse_cors_origins(self.cors_origins_raw)

    def _parse_cors_origins(self, v: str) -> List[str]:
        """Parse CORS origins from string."""
        if not v or not v.strip():
            return ["http://localhost:3000", "http://localhost:8000", "http://localhost:8005"]
        
        v = v.strip().strip('"').strip("'")
        if not v:
            return ["http://localhost:3000", "http://localhost:8000", "http://localhost:8005"]
        
        origins = []
        for origin in v.split(","):
            origin = origin.strip().strip('"').strip("'")
            if origin:
                origins.append(origin)
        
        return origins if origins else ["http://localhost:3000", "http://localhost:8000", "http://localhost:8005"]

    # =============================================================================
    # Neo4j Configuration (SNOMED RAG)
    # =============================================================================
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j user")
    neo4j_username: str = Field(default="neo4j", description="Neo4j username (alias)")
    neo4j_password: str = Field(description="Neo4j password - REQUIRED")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database")
    neo4j_max_connection_lifetime: int = Field(default=30, description="Neo4j max connection lifetime in seconds")
    neo4j_max_connections: int = Field(default=50, description="Neo4j max connection pool size")
    neo4j_connection_timeout: int = Field(default=30, description="Neo4j connection timeout in seconds")

    # =============================================================================
    # Azure OpenAI Configuration
    # =============================================================================
    azure_openai_api_key: str = Field(description="Azure OpenAI API key - REQUIRED")
    azure_openai_endpoint: str = Field(description="Azure OpenAI endpoint - REQUIRED")
    azure_openai_deployment_name: str = Field(default="gpt-4o", description="Azure OpenAI deployment name")
    azure_openai_api_version: str = Field(default="2024-05-01-preview", description="Azure OpenAI API version")
    azure_openai_model: str = Field(default="gpt-4o", description="Azure OpenAI model name")
    azure_input_price_per_1k_tokens: float = Field(default=0.005, description="Price per 1K input tokens for the Azure model")
    azure_output_price_per_1k_tokens: float = Field(default=0.015, description="Price per 1K output tokens for the Azure model")

    # Azure OpenAI Embeddings
    openai_embedding_endpoint: str = Field(description="OpenAI embedding endpoint - REQUIRED")
    openai_embedding_api_key: str = Field(description="OpenAI embedding API key - REQUIRED")
    openai_embedding_deployment_name: str = Field(default="text-embedding-ada-002", description="Embedding deployment name")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", description="OpenAI embedding model")

    # =============================================================================
    # LangFuse Configuration (Observability)
    # =============================================================================
    langfuse_secret_key: str = Field(description="LangFuse secret key - REQUIRED")
    langfuse_public_key: str = Field(description="LangFuse public key - REQUIRED")
    langfuse_host: str = Field(default="https://us.cloud.langfuse.com", description="LangFuse host")

    # =============================================================================
    # AWS Configuration (OpenSearch)
    # =============================================================================
    aws_access_key_id: str = Field(description="AWS Access Key ID - REQUIRED")
    aws_secret_access_key: str = Field(description="AWS Secret Access Key - REQUIRED")
    opensearch_endpoint: str = Field(
        default="https://9tty40b80t5pqwdeqop6.ca-central-1.aoss.amazonaws.com",
        description="AWS OpenSearch endpoint"
    )
    opensearch_index: str = Field(default="medical-conversations", description="OpenSearch index name")
    opensearch_timeout: int = Field(default=300, description="OpenSearch timeout in seconds")

    # =============================================================================
    # RAG Configuration
    # =============================================================================
    snomed_query_limit: int = Field(default=10, description="SNOMED query limit per term")
    retrieval_k_value: int = Field(default=5, description="Number of chunks to retrieve for RAG")
    chunk_size: int = Field(default=1500, description="Chunk size for conversation splitting")
    chunk_overlap: int = Field(default=100, description="Chunk overlap for conversation splitting")
    store_full_conversation: bool = Field(default=True, description="Store full conversation text in RAG")

    # =============================================================================
    # Validators
    # =============================================================================
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()

    # =============================================================================
    # Properties
    # =============================================================================
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True,
        use_enum_values=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
