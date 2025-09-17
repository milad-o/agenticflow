"""
Enhanced Memory System for AgenticFlow
======================================
Provides multiple memory backends including ephemeral (buffer), persistent 
(SQLite, PostgreSQL), and custom implementations with session management.
"""

from .backends import (
    SQLiteMemory,
    PostgreSQLMemory, 
    CustomMemory,
    PersistentMemoryMixin
)
from .config import (
    MemoryBackendType,
    MemoryBackendConfig,
    DatabaseConfig
)
from .factory import EnhancedMemoryFactory

# Re-export original memory classes for compatibility
from ..memory import (
    AsyncMemory,
    BufferMemory,
    RetrievalMemory,
    HybridMemory,
    MemoryDocument,
    MemoryError,
    VectorStoreError,
    MemoryFactory
)

__all__ = [
    # Enhanced backends
    'SQLiteMemory',
    'PostgreSQLMemory',
    'CustomMemory',
    'PersistentMemoryMixin',
    
    # Configuration
    'MemoryBackendType',
    'MemoryBackendConfig', 
    'DatabaseConfig',
    
    # Factory
    'EnhancedMemoryFactory',
    
    # Original classes (compatibility)
    'AsyncMemory',
    'BufferMemory',
    'RetrievalMemory', 
    'HybridMemory',
    'MemoryDocument',
    'MemoryError',
    'VectorStoreError',
    'MemoryFactory'
]