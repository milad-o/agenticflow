"""
Advanced Memory Backends for AgenticFlow
========================================
Provides SQLite, PostgreSQL, and custom memory implementations with 
persistent storage, cross-session support, and advanced querying.
"""

import asyncio
import json
import sqlite3
import time
import uuid
from abc import abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

# Avoid circular imports by importing directly from parent module
from agenticflow.config.settings import MemoryConfig
from .config import DatabaseConfig, MemoryBackendConfig

# Import base classes from core module  
from .core import AsyncMemory, MemoryDocument

logger = structlog.get_logger(__name__)

try:
    import asyncpg
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logger.warning("asyncpg not available, PostgreSQL backend disabled")

try:
    import aiosqlite
    SQLITE_ASYNC_AVAILABLE = True
except ImportError:
    SQLITE_ASYNC_AVAILABLE = False
    logger.warning("aiosqlite not available, using synchronous SQLite")


class PersistentMemoryMixin:
    """Mixin providing persistence functionality for memory backends."""
    
    def __init__(self, config: MemoryBackendConfig):
        self.config = config
        self.logger = logger.bind(memory_backend=config.backend_type)
        self._session_id = str(uuid.uuid4())
        self._metadata = config.metadata or {}
    
    def _serialize_message(self, message: BaseMessage, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Serialize a LangChain message to dict for storage."""
        return {
            'id': str(uuid.uuid4()),
            'type': message.__class__.__name__.lower().replace('message', ''),
            'content': message.content,
            'metadata': json.dumps(metadata or {}),
            'session_id': self._session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'created_at': int(time.time())
        }
    
    def _deserialize_message(self, row: Dict[str, Any]) -> Tuple[BaseMessage, Dict[str, Any], str]:
        """Deserialize stored row back to LangChain message."""
        msg_type = row['type']
        content = row['content']
        metadata = json.loads(row['metadata'] or '{}')
        msg_id = row['id']
        
        # Create appropriate message type
        if msg_type == 'human':
            message = HumanMessage(content=content)
        elif msg_type == 'ai':
            message = AIMessage(content=content)
        elif msg_type == 'system':
            message = SystemMessage(content=content)
        else:
            message = HumanMessage(content=content)  # fallback
        
        return message, metadata, msg_id
    
    def _create_memory_document(self, row: Dict[str, Any]) -> MemoryDocument:
        """Create MemoryDocument from database row."""
        return MemoryDocument(
            id=row['id'],
            content=row['content'],
            metadata=json.loads(row['metadata'] or '{}'),
            timestamp=row['created_at']
        )


class SQLiteMemory(AsyncMemory, PersistentMemoryMixin):
    """SQLite-based persistent memory backend."""
    
    def __init__(self, config: MemoryBackendConfig):
        AsyncMemory.__init__(self, config.to_memory_config())
        PersistentMemoryMixin.__init__(self, config)
        
        self.db_path = config.connection_params.get('database', 'agenticflow_memory.db')
        self._connection: Optional[Union[sqlite3.Connection, Any]] = None
        self._setup_complete = False
        
        # Ensure parent directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def _get_connection(self):
        """Get database connection (async or sync based on availability)."""
        if not self._connection:
            if SQLITE_ASYNC_AVAILABLE:
                self._connection = await aiosqlite.connect(self.db_path)
                self._connection.row_factory = aiosqlite.Row
            else:
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row
        
        return self._connection
    
    async def _setup_tables(self):
        """Setup database tables if not exists."""
        if self._setup_complete:
            return
        
        conn = await self._get_connection()
        
        schema = '''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_session_timestamp ON messages(session_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_content ON messages(content);
        CREATE INDEX IF NOT EXISTS idx_type ON messages(type);
        '''
        
        if SQLITE_ASYNC_AVAILABLE:
            await conn.executescript(schema)
            await conn.commit()
        else:
            conn.executescript(schema)
            conn.commit()
        
        self._setup_complete = True
        self.logger.info(f"SQLite memory initialized at {self.db_path}")
    
    async def add_message(self, message: BaseMessage, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to SQLite storage."""
        await self._setup_tables()
        conn = await self._get_connection()
        
        data = self._serialize_message(message, metadata)
        
        query = '''
        INSERT INTO messages (id, type, content, metadata, session_id, timestamp, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (data['id'], data['type'], data['content'], data['metadata'], 
                 data['session_id'], data['timestamp'], data['created_at'])
        
        if SQLITE_ASYNC_AVAILABLE:
            await conn.execute(query, params)
            await conn.commit()
        else:
            conn.execute(query, params)
            conn.commit()
        
        self.logger.debug(f"Added message {data['id']} to SQLite memory")
        return data['id']
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> List[BaseMessage]:
        """Get messages from SQLite storage."""
        await self._setup_tables()
        conn = await self._get_connection()
        
        # Build query with filters
        query = "SELECT * FROM messages WHERE session_id = ?"
        params = [session_id or self._session_id]
        
        if filter_metadata:
            # Simple metadata filtering (can be enhanced)
            for key, value in filter_metadata.items():
                query += f" AND json_extract(metadata, '$.{key}') = ?"
                params.append(str(value))
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        if SQLITE_ASYNC_AVAILABLE:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
        else:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            message, _, _ = self._deserialize_message(dict(row))
            messages.append(message)
        
        return messages
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.7,
        session_id: Optional[str] = None
    ) -> List[MemoryDocument]:
        """Search messages by content similarity (basic text search for SQLite)."""
        await self._setup_tables()
        conn = await self._get_connection()
        
        # Basic text search with LIKE - can be enhanced with FTS if needed
        search_query = '''
        SELECT * FROM messages 
        WHERE session_id = ? AND content LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
        '''
        
        params = [session_id or self._session_id, f"%{query}%", limit]
        
        if SQLITE_ASYNC_AVAILABLE:
            cursor = await conn.execute(search_query, params)
            rows = await cursor.fetchall()
        else:
            cursor = conn.execute(search_query, params)
            rows = cursor.fetchall()
        
        results = []
        for row in rows:
            doc = self._create_memory_document(dict(row))
            results.append(doc)
        
        return results
    
    async def clear(self, session_id: Optional[str] = None) -> None:
        """Clear messages for a session."""
        await self._setup_tables()
        conn = await self._get_connection()
        
        query = "DELETE FROM messages WHERE session_id = ?"
        params = [session_id or self._session_id]
        
        if SQLITE_ASYNC_AVAILABLE:
            await conn.execute(query, params)
            await conn.commit()
        else:
            conn.execute(query, params)
            conn.commit()
        
        self.logger.info(f"Cleared SQLite memory for session {session_id or self._session_id}")
    
    async def save(self, path: Optional[str] = None) -> None:
        """SQLite auto-saves, this is a no-op but could backup the file."""
        self.logger.info("SQLite memory is auto-saved")
    
    async def load(self, path: str) -> None:
        """Load from a different SQLite file."""
        self.db_path = path
        self._connection = None
        self._setup_complete = False
        await self._setup_tables()
        self.logger.info(f"Loaded SQLite memory from {path}")
    
    async def get_sessions(self) -> List[str]:
        """Get all session IDs in the database."""
        await self._setup_tables()
        conn = await self._get_connection()
        
        query = "SELECT DISTINCT session_id FROM messages ORDER BY session_id"
        
        if SQLITE_ASYNC_AVAILABLE:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
        else:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
        
        return [row[0] for row in rows]
    
    async def get_session_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a session."""
        await self._setup_tables()
        conn = await self._get_connection()
        
        target_session = session_id or self._session_id
        
        query = '''
        SELECT 
            COUNT(*) as message_count,
            MIN(created_at) as first_message,
            MAX(created_at) as last_message,
            COUNT(DISTINCT type) as message_types
        FROM messages 
        WHERE session_id = ?
        '''
        
        if SQLITE_ASYNC_AVAILABLE:
            cursor = await conn.execute(query, [target_session])
            row = await cursor.fetchone()
        else:
            cursor = conn.execute(query, [target_session])
            row = cursor.fetchone()
        
        if row and row[0] > 0:
            return {
                'session_id': target_session,
                'message_count': row[0],
                'first_message': datetime.fromtimestamp(row[1]) if row[1] else None,
                'last_message': datetime.fromtimestamp(row[2]) if row[2] else None,
                'message_types': row[3],
                'duration_seconds': (row[2] - row[1]) if (row[1] and row[2]) else 0
            }
        
        return {'session_id': target_session, 'message_count': 0}
    
    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            if SQLITE_ASYNC_AVAILABLE:
                await self._connection.close()
            else:
                self._connection.close()
            self._connection = None


if POSTGRESQL_AVAILABLE:
    class PostgreSQLMemory(AsyncMemory, PersistentMemoryMixin):
        """PostgreSQL-based persistent memory backend."""
        
        def __init__(self, config: MemoryBackendConfig):
            AsyncMemory.__init__(self, config.to_memory_config())
            PersistentMemoryMixin.__init__(self, config)
            
            self._pool: Optional[asyncpg.Pool] = None
            self._setup_complete = False
            
            # Extract connection parameters
            self.connection_params = {
                'host': config.connection_params.get('host', 'localhost'),
                'port': config.connection_params.get('port', 5432),
                'database': config.connection_params.get('database', 'agenticflow'),
                'user': config.connection_params.get('user', 'postgres'),
                'password': config.connection_params.get('password', ''),
            }
        
        async def _get_pool(self) -> asyncpg.Pool:
            """Get database connection pool."""
            if not self._pool:
                try:
                    self._pool = await asyncpg.create_pool(**self.connection_params)
                    self.logger.info("Connected to PostgreSQL")
                except Exception as e:
                    raise MemoryError(f"Failed to connect to PostgreSQL: {e}")
            
            return self._pool
    
    async def _setup_tables(self):
        """Setup database tables if not exists."""
        if self._setup_complete:
            return
        
        pool = await self._get_pool()
        
        schema = '''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at BIGINT NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_messages_session_time ON messages(session_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_messages_content ON messages USING gin(to_tsvector('english', content));
        CREATE INDEX IF NOT EXISTS idx_messages_metadata ON messages USING gin(metadata);
        '''
        
        async with pool.acquire() as conn:
            await conn.execute(schema)
        
        self._setup_complete = True
        self.logger.info("PostgreSQL memory initialized")
    
    async def add_message(self, message: BaseMessage, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to PostgreSQL storage."""
        await self._setup_tables()
        pool = await self._get_pool()
        
        data = self._serialize_message(message, metadata)
        
        query = '''
        INSERT INTO messages (id, type, content, metadata, session_id, timestamp, created_at)
        VALUES ($1, $2, $3, $4::jsonb, $5, $6::timestamp, $7)
        '''
        
        async with pool.acquire() as conn:
            await conn.execute(
                query, 
                data['id'], data['type'], data['content'], data['metadata'],
                data['session_id'], data['timestamp'], data['created_at']
            )
        
        self.logger.debug(f"Added message {data['id']} to PostgreSQL memory")
        return data['id']
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> List[BaseMessage]:
        """Get messages from PostgreSQL storage."""
        await self._setup_tables()
        pool = await self._get_pool()
        
        # Build query with filters
        query = "SELECT * FROM messages WHERE session_id = $1"
        params = [session_id or self._session_id]
        
        if filter_metadata:
            # Advanced JSONB filtering
            conditions = []
            for i, (key, value) in enumerate(filter_metadata.items(), 2):
                conditions.append(f"metadata->>'{key}' = ${i}")
                params.append(str(value))
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += f" LIMIT ${len(params) + 1}"
            params.append(limit)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        messages = []
        for row in rows:
            message, _, _ = self._deserialize_message(dict(row))
            messages.append(message)
        
        return messages
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.7,
        session_id: Optional[str] = None
    ) -> List[MemoryDocument]:
        """Search messages using PostgreSQL full-text search."""
        await self._setup_tables()
        pool = await self._get_pool()
        
        # Use PostgreSQL full-text search
        search_query = '''
        SELECT *, ts_rank_cd(to_tsvector('english', content), query) AS rank
        FROM messages, plainto_tsquery('english', $1) query
        WHERE session_id = $2 
        AND to_tsvector('english', content) @@ query
        ORDER BY rank DESC
        LIMIT $3
        '''
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(search_query, query, session_id or self._session_id, limit)
        
        results = []
        for row in rows:
            doc = self._create_memory_document(dict(row))
            results.append(doc)
        
        return results
    
    async def clear(self, session_id: Optional[str] = None) -> None:
        """Clear messages for a session."""
        await self._setup_tables()
        pool = await self._get_pool()
        
        query = "DELETE FROM messages WHERE session_id = $1"
        
        async with pool.acquire() as conn:
            result = await conn.execute(query, session_id or self._session_id)
        
        self.logger.info(f"Cleared PostgreSQL memory for session {session_id or self._session_id}")
    
    async def save(self, path: Optional[str] = None) -> None:
        """PostgreSQL auto-saves, this is a no-op."""
        self.logger.info("PostgreSQL memory is auto-saved")
    
    async def load(self, path: str) -> None:
        """Load from different PostgreSQL database."""
        # This would typically involve changing connection params
        self.logger.info("PostgreSQL load not implemented - use connection params instead")
    
    async def get_sessions(self) -> List[str]:
        """Get all session IDs in the database."""
        await self._setup_tables()
        pool = await self._get_pool()
        
        query = "SELECT DISTINCT session_id FROM messages ORDER BY session_id"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        return [row['session_id'] for row in rows]
    
    async def get_session_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a session."""
        await self._setup_tables()
        pool = await self._get_pool()
        
        target_session = session_id or self._session_id
        
        query = '''
        SELECT 
            COUNT(*) as message_count,
            MIN(created_at) as first_message,
            MAX(created_at) as last_message,
            COUNT(DISTINCT type) as message_types,
            AVG(length(content)) as avg_content_length
        FROM messages 
        WHERE session_id = $1
        '''
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, target_session)
        
        if row and row['message_count'] > 0:
            return {
                'session_id': target_session,
                'message_count': row['message_count'],
                'first_message': datetime.fromtimestamp(row['first_message']) if row['first_message'] else None,
                'last_message': datetime.fromtimestamp(row['last_message']) if row['last_message'] else None,
                'message_types': row['message_types'],
                'avg_content_length': float(row['avg_content_length']) if row['avg_content_length'] else 0,
                'duration_seconds': (row['last_message'] - row['first_message']) if (row['first_message'] and row['last_message']) else 0
            }
        
        return {'session_id': target_session, 'message_count': 0}
    
        async def close(self) -> None:
            """Close database connection pool."""
            if self._pool:
                await self._pool.close()
                self._pool = None

else:
    # Fallback when asyncpg is not available
    class PostgreSQLMemory:
        def __init__(self, config):
            raise MemoryError("PostgreSQL backend requires 'asyncpg' package. Install with: pip install asyncpg")


class CustomMemory(AsyncMemory):
    """Custom memory backend that can be extended by users."""
    
    def __init__(self, config: MemoryBackendConfig, custom_handler: Optional[Any] = None):
        super().__init__(config.to_memory_config())
        self.config = config
        self.custom_handler = custom_handler
        self.logger = logger.bind(memory_backend="custom")
        
        if not custom_handler:
            raise MemoryError("CustomMemory requires a custom_handler implementation")
        
        # Validate custom handler has required methods
        required_methods = ['add_message', 'get_messages', 'search', 'clear', 'save', 'load']
        for method in required_methods:
            if not hasattr(custom_handler, method):
                raise MemoryError(f"Custom handler missing required method: {method}")
    
    async def add_message(self, message: BaseMessage, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Delegate to custom handler."""
        return await self.custom_handler.add_message(message, metadata)
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[BaseMessage]:
        """Delegate to custom handler."""
        return await self.custom_handler.get_messages(limit, filter_metadata)
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[MemoryDocument]:
        """Delegate to custom handler."""
        return await self.custom_handler.search(query, limit, similarity_threshold)
    
    async def clear(self) -> None:
        """Delegate to custom handler."""
        return await self.custom_handler.clear()
    
    async def save(self, path: Optional[str] = None) -> None:
        """Delegate to custom handler."""
        return await self.custom_handler.save(path)
    
    async def load(self, path: str) -> None:
        """Delegate to custom handler."""
        return await self.custom_handler.load(path)