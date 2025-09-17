"""
Memory Backend Configuration
============================
Configuration classes for different memory backend types including
database connections, persistence options, and custom handlers.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from ..config.settings import MemoryConfig


class MemoryBackendType(str, Enum):
    """Supported memory backend types."""
    BUFFER = "buffer"
    RETRIEVAL = "retrieval"
    HYBRID = "hybrid"
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    CUSTOM = "custom"


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    
    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    database: str = Field("agenticflow", description="Database name")
    user: str = Field("postgres", description="Database user")
    password: str = Field("", description="Database password")
    
    # Connection pool settings
    min_size: int = Field(1, ge=1, description="Minimum pool size")
    max_size: int = Field(10, ge=1, description="Maximum pool size")
    timeout: int = Field(30, ge=1, description="Connection timeout in seconds")


class MemoryBackendConfig(BaseModel):
    """Enhanced memory configuration with backend support."""
    
    backend_type: MemoryBackendType = Field(MemoryBackendType.BUFFER, description="Memory backend type")
    
    # Basic memory settings (inherited from original MemoryConfig)
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to store")
    max_messages: Optional[int] = Field(None, ge=1, description="Maximum messages to store")
    
    # Retrieval memory specific
    vector_store_path: Optional[str] = Field(None, description="Path for vector store persistence")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold for retrieval")
    max_retrievals: int = Field(5, ge=1, description="Maximum number of retrievals")
    
    # Database backend specific
    connection_params: Dict[str, Any] = Field(default_factory=dict, description="Database connection parameters")
    
    # Session management
    session_persistence: bool = Field(True, description="Whether to persist sessions across restarts")
    auto_create_session: bool = Field(True, description="Automatically create session if not exists")
    session_timeout_hours: int = Field(24, ge=1, description="Session timeout in hours")
    
    # Performance and caching
    enable_caching: bool = Field(True, description="Enable in-memory caching for frequently accessed data")
    cache_size: int = Field(1000, ge=1, description="Maximum cache size")
    
    # Custom backend specific
    custom_handler_class: Optional[str] = Field(None, description="Custom handler class path")
    custom_handler_config: Dict[str, Any] = Field(default_factory=dict, description="Custom handler configuration")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def to_memory_config(self) -> MemoryConfig:
        """Convert to legacy MemoryConfig for compatibility."""
        return MemoryConfig(
            type=self.backend_type.value,
            max_tokens=self.max_tokens,
            max_messages=self.max_messages,
            vector_store_path=self.vector_store_path,
            similarity_threshold=self.similarity_threshold,
            max_retrievals=self.max_retrievals
        )
    
    @classmethod
    def from_memory_config(cls, config: MemoryConfig) -> "MemoryBackendConfig":
        """Create from legacy MemoryConfig."""
        return cls(
            backend_type=MemoryBackendType(config.type),
            max_tokens=config.max_tokens,
            max_messages=config.max_messages,
            vector_store_path=config.vector_store_path,
            similarity_threshold=config.similarity_threshold,
            max_retrievals=config.max_retrievals
        )
    
    @classmethod
    def create_sqlite_config(
        cls,
        database_path: str = "agenticflow_memory.db",
        max_messages: Optional[int] = None,
        session_persistence: bool = True,
        **kwargs
    ) -> "MemoryBackendConfig":
        """Create SQLite memory configuration."""
        return cls(
            backend_type=MemoryBackendType.SQLITE,
            connection_params={"database": database_path},
            max_messages=max_messages,
            session_persistence=session_persistence,
            **kwargs
        )
    
    @classmethod
    def create_postgresql_config(
        cls,
        host: str = "localhost",
        port: int = 5432,
        database: str = "agenticflow",
        user: str = "postgres",
        password: str = "",
        max_messages: Optional[int] = None,
        session_persistence: bool = True,
        **kwargs
    ) -> "MemoryBackendConfig":
        """Create PostgreSQL memory configuration."""
        return cls(
            backend_type=MemoryBackendType.POSTGRESQL,
            connection_params={
                "host": host,
                "port": port,
                "database": database,
                "user": user,
                "password": password
            },
            max_messages=max_messages,
            session_persistence=session_persistence,
            **kwargs
        )
    
    @classmethod
    def create_custom_config(
        cls,
        handler_class: str,
        handler_config: Dict[str, Any] = None,
        max_messages: Optional[int] = None,
        **kwargs
    ) -> "MemoryBackendConfig":
        """Create custom memory configuration."""
        return cls(
            backend_type=MemoryBackendType.CUSTOM,
            custom_handler_class=handler_class,
            custom_handler_config=handler_config or {},
            max_messages=max_messages,
            **kwargs
        )