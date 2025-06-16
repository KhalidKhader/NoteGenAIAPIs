"""Configuration management for NoteGen AI APIs.

This module provides centralized configuration management using Pydantic Settings,
handling all environment variables and application settings for the medical
SOAP generation microservice.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # =============================================================================
    # Application Settings
    # =============================================================================
    app_name: str = Field(default="NoteGen AI APIs", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="API workers")
    
    # =============================================================================
    # Azure OpenAI Configuration
    # =============================================================================
    azure_openai_api_key: str = Field(description="Azure OpenAI API key")
    azure_openai_endpoint: str = Field(description="Azure OpenAI endpoint")
    azure_openai_deployment_name: str = Field(
        default="gpt-4o", description="Azure OpenAI deployment name"
    )
    azure_openai_instance_name: str = Field(description="Azure OpenAI instance name")
    azure_openai_api_version: str = Field(
        default="2024-05-01-preview", description="Azure OpenAI API version"
    )
    azure_openai_model: str = Field(default="gpt-4", description="Azure OpenAI model")
    
    # Azure OpenAI Embeddings
    openai_embedding_endpoint: str = Field(description="OpenAI embedding endpoint")
    openai_embedding_api_key: str = Field(description="OpenAI embedding API key")
    openai_embedding_deployment_name: str = Field(
        default="text-embedding-ada-002", description="Embedding deployment name"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-ada-002", description="Embedding model name"
    )
    
    # =============================================================================
    # Neo4j Configuration (SNOMED RAG)
    # =============================================================================
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_username: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database")
    
    # Neo4j Connection Settings
    neo4j_max_connection_lifetime: int = Field(
        default=3600, description="Neo4j max connection lifetime"
    )
    neo4j_max_connection_pool_size: int = Field(
        default=50, description="Neo4j max connection pool size"
    )
    neo4j_connection_acquisition_timeout: int = Field(
        default=60, description="Neo4j connection acquisition timeout"
    )
    
    # =============================================================================
    # Vector Database Configuration
    # =============================================================================
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(
        default="./conversation_rag_db", description="Chroma persist directory"
    )
    chroma_collection_name: str = Field(
        default="medical_conversations", description="Chroma collection name"
    )
    
    # Weaviate Configuration
    weaviate_url: str = Field(default="http://localhost:8080", description="Weaviate URL")
    weaviate_api_key: Optional[str] = Field(default=None, description="Weaviate API key")
    weaviate_class_name: str = Field(
        default="MedicalConversation", description="Weaviate class name"
    )
    
    # Vector Database Settings
    vector_db_type: str = Field(default="chroma", description="Vector database type")
    conversation_chunk_size: int = Field(default=1500, description="Conversation chunk size")
    conversation_chunk_overlap: int = Field(
        default=150, description="Conversation chunk overlap"
    )
    max_retrieval_chunks: int = Field(default=5, description="Max retrieval chunks")
    
    # =============================================================================
    # Redis Configuration
    # =============================================================================
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    redis_password: str = Field(default="notegen2024", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database")
    redis_max_connections: int = Field(default=20, description="Redis max connections")
    redis_socket_timeout: int = Field(default=5, description="Redis socket timeout")
    redis_socket_connect_timeout: int = Field(
        default=5, description="Redis socket connect timeout"
    )
    
    # Cache TTL Settings
    cache_ttl_short: int = Field(default=300, description="Short cache TTL")
    cache_ttl_medium: int = Field(default=1800, description="Medium cache TTL")
    cache_ttl_long: int = Field(default=3600, description="Long cache TTL")
    
    # =============================================================================
    # LangFuse Configuration (Observability)
    # =============================================================================
    langfuse_secret_key: str = Field(description="LangFuse secret key")
    langfuse_public_key: str = Field(description="LangFuse public key")
    langfuse_host: str = Field(
        default="https://us.cloud.langfuse.com", description="LangFuse host"
    )
    langfuse_debug: bool = Field(default=False, description="LangFuse debug mode")
    langfuse_enabled: bool = Field(default=True, description="LangFuse enabled")
    
    # =============================================================================
    # Security Configuration
    # =============================================================================
    # JWT Settings
    jwt_secret_key: str = Field(description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=60, description="JWT expiration minutes")
    
    # Encryption Settings
    encryption_key: str = Field(description="Encryption key for sensitive data")
    patient_data_encryption: bool = Field(
        default=True, description="Patient data encryption enabled"
    )
    
    # API Security
    api_key_header: str = Field(default="X-API-Key", description="API key header")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000", "http://localhost:8005"],
        description="CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS allow credentials")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Rate limiting enabled")
    rate_limit_requests_per_minute: int = Field(
        default=60, description="Rate limit requests per minute"
    )
    rate_limit_burst: int = Field(default=10, description="Rate limit burst")
    
    # =============================================================================
    # Monitoring & Observability
    # =============================================================================
    prometheus_enabled: bool = Field(default=True, description="Prometheus enabled")
    prometheus_port: int = Field(default=9000, description="Prometheus port")
    metrics_endpoint: str = Field(default="/metrics", description="Metrics endpoint")
    
    # Health Check Settings
    health_check_timeout: int = Field(default=30, description="Health check timeout")
    health_check_interval: int = Field(default=10, description="Health check interval")
    
    # Logging Configuration
    log_format: str = Field(default="json", description="Log format")
    log_file_enabled: bool = Field(default=True, description="Log file enabled")
    log_file_path: str = Field(default="./logs/app.log", description="Log file path")
    log_rotation_size: str = Field(default="10MB", description="Log rotation size")
    log_retention_days: int = Field(default=30, description="Log retention days")
    
    # =============================================================================
    # External Services
    # =============================================================================
    hf_token: Optional[str] = Field(default=None, description="HuggingFace token")
    hf_cache_dir: str = Field(default="./hf_cache", description="HuggingFace cache dir")
    
    # Grafana Settings
    grafana_user: str = Field(default="admin", description="Grafana user")
    grafana_password: str = Field(default="notegen2024", description="Grafana password")
    
    # =============================================================================
    # RAG System Configuration
    # =============================================================================
    # Conversation RAG Settings
    conversation_rag_enabled: bool = Field(
        default=True, description="Conversation RAG enabled"
    )
    conversation_rag_similarity_threshold: float = Field(
        default=0.7, description="Conversation RAG similarity threshold"
    )
    conversation_rag_max_results: int = Field(
        default=5, description="Conversation RAG max results"
    )
    
    # SNOMED RAG Settings
    snomed_rag_enabled: bool = Field(default=True, description="SNOMED RAG enabled")
    snomed_rag_language: str = Field(default="en", description="SNOMED RAG language")
    snomed_rag_max_codes: int = Field(default=10, description="SNOMED RAG max codes")
    snomed_rag_similarity_threshold: float = Field(
        default=0.8, description="SNOMED RAG similarity threshold"
    )
    
    # Pattern Learning RAG Settings
    pattern_learning_enabled: bool = Field(
        default=True, description="Pattern learning enabled"
    )
    pattern_learning_confidence_threshold: float = Field(
        default=0.8, description="Pattern learning confidence threshold"
    )
    pattern_learning_min_frequency: int = Field(
        default=3, description="Pattern learning min frequency"
    )
    pattern_learning_storage_path: str = Field(
        default="./doctor_patterns.json", description="Pattern learning storage path"
    )
    
    # =============================================================================
    # SOAP Generation Settings
    # =============================================================================
    # Generation Parameters
    soap_generation_temperature: float = Field(
        default=0.1, description="SOAP generation temperature"
    )
    soap_generation_max_tokens: int = Field(
        default=4000, description="SOAP generation max tokens"
    )
    soap_generation_top_p: float = Field(default=0.95, description="SOAP generation top p")
    soap_generation_frequency_penalty: float = Field(
        default=0.0, description="SOAP generation frequency penalty"
    )
    soap_generation_presence_penalty: float = Field(
        default=0.0, description="SOAP generation presence penalty"
    )
    
    # Sequential Generation Settings
    soap_sequential_generation: bool = Field(
        default=True, description="SOAP sequential generation"
    )
    soap_context_window_size: int = Field(
        default=8000, description="SOAP context window size"
    )
    soap_max_retries: int = Field(default=3, description="SOAP max retries")
    soap_retry_delay: int = Field(default=2, description="SOAP retry delay")
    
    # Quality Assurance
    soap_validation_enabled: bool = Field(default=True, description="SOAP validation enabled")
    soap_snomed_validation: bool = Field(
        default=True, description="SOAP SNOMED validation enabled"
    )
    soap_completeness_check: bool = Field(
        default=True, description="SOAP completeness check enabled"
    )
    
    # =============================================================================
    # Development Settings
    # =============================================================================
    dev_data_path: str = Field(default="./dev_data", description="Development data path")
    test_data_path: str = Field(default="./test_data", description="Test data path")
    backup_path: str = Field(default="./backups", description="Backup path")
    
    # Performance Settings
    async_pool_size: int = Field(default=10, description="Async pool size")
    http_timeout: int = Field(default=30, description="HTTP timeout")
    request_timeout: int = Field(default=60, description="Request timeout")
    
    # Feature Flags
    feature_multilingual: bool = Field(default=True, description="Multilingual feature")
    feature_real_time: bool = Field(default=False, description="Real-time feature")
    feature_batch_processing: bool = Field(
        default=True, description="Batch processing feature"
    )
    
    # =============================================================================
    # Compliance & Audit
    # =============================================================================
    audit_logging_enabled: bool = Field(default=True, description="Audit logging enabled")
    audit_log_retention_days: int = Field(
        default=365, description="Audit log retention days"
    )
    audit_log_encryption: bool = Field(
        default=True, description="Audit log encryption enabled"
    )
    
    # Data Retention Policies
    conversation_retention_days: int = Field(
        default=90, description="Conversation retention days"
    )
    pattern_retention_days: int = Field(default=365, description="Pattern retention days")
    metrics_retention_days: int = Field(default=30, description="Metrics retention days")
    
    # Privacy Settings
    anonymize_logs: bool = Field(default=True, description="Anonymize logs")
    mask_pii: bool = Field(default=True, description="Mask PII")
    gdpr_compliance: bool = Field(default=True, description="GDPR compliance")
    
    # =============================================================================
    # Validators
    # =============================================================================
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("vector_db_type")
    def validate_vector_db_type(cls, v):
        """Validate vector database type."""
        allowed_types = ["chroma", "weaviate"]
        if v not in allowed_types:
            raise ValueError(f"vector_db_type must be one of {allowed_types}")
        return v
    
    @validator("snomed_rag_language")
    def validate_snomed_language(cls, v):
        """Validate SNOMED RAG language."""
        allowed_languages = ["en", "fr", "both"]
        if v not in allowed_languages:
            raise ValueError(f"snomed_rag_language must be one of {allowed_languages}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()
    
    @validator("encryption_key")
    def validate_encryption_key(cls, v):
        """Validate encryption key length."""
        if len(v) < 32:
            raise ValueError("encryption_key must be at least 32 characters long")
        return v
    
    # =============================================================================
    # Properties
    # =============================================================================
    
    @property
    def redis_dsn(self) -> str:
        """Get Redis DSN with password."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_url.split('://')[-1]}/{self.redis_db}"
        return f"{self.redis_url}/{self.redis_db}"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings() 