"""Configuration management for NoteGen AI APIs.

This module provides centralized configuration management using Pydantic Settings,
handling all environment variables and application settings for the medical
SOAP generation microservice.
"""

from functools import lru_cache
from typing import List, Optional, Any

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # =============================================================================
    # Application Settings
    # =============================================================================
    app_name: str = Field(default="notegen-ai-api", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug_mode(cls, v: Any) -> bool:
        """Allow flexible boolean validation for debug mode."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

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

    def _parse_cors_origins(self, cors_origins_str: str) -> List[str]:
        """Parse CORS origins from string."""
        if not cors_origins_str or not cors_origins_str.strip():
            return ["http://localhost:3000", "http://localhost:8000", "http://localhost:8005"]
        
        cleaned_str = cors_origins_str.strip().strip('"').strip("'")
        if not cleaned_str:
            return ["http://localhost:3000", "http://localhost:8000", "http://localhost:8005"]
        
        origins = []
        for origin in cleaned_str.split(","):
            origin = origin.strip().strip('"').strip("'")
            if origin:
                origins.append(origin)
        
        return origins if origins else ["http://localhost:3000", "http://localhost:8000", "http://localhost:8005"]

    # =============================================================================
    # Neo4j Configuration (SNOMED RAG)
    # =============================================================================
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j user")
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
    azure_openai_embedding_endpoint: str = Field(description="Azure OpenAI embedding endpoint - REQUIRED")
    azure_openai_embedding_api_key: str = Field(description="Azure OpenAI embedding API key - REQUIRED")
    azure_openai_embedding_deployment_name: str = Field(default="text-embedding-ada-002", description="Embedding deployment name")
    azure_openai_embedding_model: str = Field(default="text-embedding-ada-002", description="Azure OpenAI embedding model")

    # =============================================================================
    # LangFuse Configuration (Observability)
    # =============================================================================
    langfuse_secret_key: str = Field(description="LangFuse secret key - REQUIRED")
    langfuse_public_key: str = Field(description="LangFuse public key - REQUIRED")
    langfuse_host: str = Field(default="https://us.cloud.langfuse.com", description="LangFuse host")

    # =============================================================================
    # AWS Configuration (OpenSearch)
    # =============================================================================
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS Access Key ID - Optional (not needed when running on AWS with IAM roles)")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS Secret Access Key - Optional (not needed when running on AWS with IAM roles)")
    aws_region: str = Field(default="ca-central-1", description="AWS region for services like OpenSearch")
    
    # =============================================================================
    # OpenSearch Configuration
    # =============================================================================
    opensearch_endpoint: str = Field(
        default="https://9tty40b80t5pqwdeqop6.ca-central-1.aoss.amazonaws.com",
        description="OpenSearch endpoint URL"
    )
    opensearch_port: int = Field(default=443, description="OpenSearch port")
    opensearch_index: str = Field(default="medical-conversations", description="OpenSearch index name")
    opensearch_timeout: int = Field(default=300, description="OpenSearch timeout in seconds")
    opensearch_username: Optional[str] = Field(default=None, description="OpenSearch username for basic authentication")
    opensearch_password: Optional[str] = Field(default=None, description="OpenSearch password for basic authentication")
    is_aoss: bool = Field(default=True, description="Flag to indicate if the OpenSearch instance is an AWS OpenSearch Serverless instance")

    # =============================================================================
    # NoteGen API Service Integration Configuration
    # =============================================================================
    notegen_api_base_url: str = Field(
        default="https://demo.notegen.ai/internal/encounters",  
        description="Base URL for NoteGen API service backend integration",
        alias="notegen_api_base_url"
    )
    notegen_api_timeout: float = Field(
        default=30.0,
        description="HTTP timeout for NoteGen API service requests in seconds",
        alias="notegen_api_timeout"
    )
    notegen_api_max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for NoteGen API service requests",
        alias="notegen_api_max_retries"
    )

    # =============================================================================
    # RAG Configuration
    # =============================================================================
    retrieval_k_value: int = Field(default=10, description="Number of chunks to retrieve for RAG")
    chunk_size: int = Field(default=1500, description="Chunk size for conversation splitting")
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
