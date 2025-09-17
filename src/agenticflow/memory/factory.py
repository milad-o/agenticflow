"""
Enhanced Memory Factory
=======================
Factory for creating different memory backend instances with proper
configuration and error handling.
"""

import importlib
from typing import Any, Optional
from langchain_core.embeddings import Embeddings

from ..memory import AsyncMemory, BufferMemory, RetrievalMemory, HybridMemory, MemoryError
from .backends import SQLiteMemory, PostgreSQLMemory, CustomMemory
from .config import MemoryBackendType, MemoryBackendConfig


class EnhancedMemoryFactory:
    """Enhanced factory for creating memory instances with multiple backends."""
    
    @classmethod
    async def create_memory(
        cls,
        config: MemoryBackendConfig,
        embeddings: Optional[Embeddings] = None,
        custom_handler: Optional[Any] = None
    ) -> AsyncMemory:
        """
        Create memory instance based on backend configuration.
        
        Args:
            config: Memory backend configuration
            embeddings: Optional embeddings for retrieval memory
            custom_handler: Optional custom handler for custom memory backend
            
        Returns:
            AsyncMemory: Configured memory instance
            
        Raises:
            MemoryError: If backend type is unsupported or configuration is invalid
        """
        backend_type = config.backend_type
        
        # Create legacy memory types
        if backend_type == MemoryBackendType.BUFFER:
            return BufferMemory(config.to_memory_config())
        
        elif backend_type == MemoryBackendType.RETRIEVAL:
            return RetrievalMemory(config.to_memory_config(), embeddings)
        
        elif backend_type == MemoryBackendType.HYBRID:
            return HybridMemory(config.to_memory_config(), embeddings)
        
        # Create enhanced memory types
        elif backend_type == MemoryBackendType.SQLITE:
            return SQLiteMemory(config)
        
        elif backend_type == MemoryBackendType.POSTGRESQL:
            return PostgreSQLMemory(config)
        
        elif backend_type == MemoryBackendType.CUSTOM:
            if not custom_handler and config.custom_handler_class:
                # Dynamically load custom handler
                custom_handler = cls._load_custom_handler(
                    config.custom_handler_class,
                    config.custom_handler_config
                )
            
            if not custom_handler:
                raise MemoryError("Custom memory backend requires a custom_handler")
            
            return CustomMemory(config, custom_handler)
        
        else:
            raise MemoryError(f"Unsupported memory backend type: {backend_type}")
    
    @classmethod
    def _load_custom_handler(cls, handler_class: str, handler_config: dict) -> Any:
        """
        Dynamically load a custom handler class.
        
        Args:
            handler_class: Full class path (e.g., 'mymodule.MyHandler')
            handler_config: Configuration to pass to handler constructor
            
        Returns:
            Instance of the custom handler class
            
        Raises:
            MemoryError: If the class cannot be loaded or instantiated
        """
        try:
            # Split module and class name
            if '.' not in handler_class:
                raise MemoryError(f"Invalid handler class path: {handler_class}")
            
            module_path, class_name = handler_class.rsplit('.', 1)
            
            # Import module
            module = importlib.import_module(module_path)
            
            # Get class
            handler_cls = getattr(module, class_name)
            
            # Instantiate with config
            return handler_cls(**handler_config)
            
        except ImportError as e:
            raise MemoryError(f"Failed to import custom handler module: {e}")
        except AttributeError as e:
            raise MemoryError(f"Custom handler class not found: {e}")
        except Exception as e:
            raise MemoryError(f"Failed to instantiate custom handler: {e}")
    
    @classmethod
    def create_sqlite_memory(
        cls,
        database_path: str = "agenticflow_memory.db",
        max_messages: Optional[int] = None,
        session_persistence: bool = True,
        **kwargs
    ) -> AsyncMemory:
        """
        Convenience method to create SQLite memory backend.
        
        Args:
            database_path: Path to SQLite database file
            max_messages: Maximum number of messages to store
            session_persistence: Whether to persist sessions
            **kwargs: Additional configuration options
            
        Returns:
            SQLiteMemory instance
        """
        config = MemoryBackendConfig.create_sqlite_config(
            database_path=database_path,
            max_messages=max_messages,
            session_persistence=session_persistence,
            **kwargs
        )
        return SQLiteMemory(config)
    
    @classmethod
    def create_postgresql_memory(
        cls,
        host: str = "localhost",
        port: int = 5432,
        database: str = "agenticflow",
        user: str = "postgres",
        password: str = "",
        max_messages: Optional[int] = None,
        session_persistence: bool = True,
        **kwargs
    ) -> AsyncMemory:
        """
        Convenience method to create PostgreSQL memory backend.
        
        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
            max_messages: Maximum number of messages to store
            session_persistence: Whether to persist sessions
            **kwargs: Additional configuration options
            
        Returns:
            PostgreSQLMemory instance
        """
        config = MemoryBackendConfig.create_postgresql_config(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            max_messages=max_messages,
            session_persistence=session_persistence,
            **kwargs
        )
        return PostgreSQLMemory(config)
    
    @classmethod 
    def create_custom_memory(
        cls,
        handler_class: str,
        handler_config: dict = None,
        max_messages: Optional[int] = None,
        **kwargs
    ) -> AsyncMemory:
        """
        Convenience method to create custom memory backend.
        
        Args:
            handler_class: Full class path to custom handler
            handler_config: Configuration for custom handler
            max_messages: Maximum number of messages to store
            **kwargs: Additional configuration options
            
        Returns:
            CustomMemory instance
        """
        config = MemoryBackendConfig.create_custom_config(
            handler_class=handler_class,
            handler_config=handler_config or {},
            max_messages=max_messages,
            **kwargs
        )
        
        # Load the custom handler
        custom_handler = cls._load_custom_handler(handler_class, handler_config or {})
        
        return CustomMemory(config, custom_handler)