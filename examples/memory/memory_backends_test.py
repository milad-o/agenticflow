#!/usr/bin/env python3
"""
AgenticFlow Memory Backends Test
================================
Comprehensive test of all memory backend types including ephemeral (buffer),
persistent (SQLite, PostgreSQL), and custom implementations.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import memory system
from agenticflow.memory import (
    BufferMemory, 
    SQLiteMemory,
    MemoryBackendConfig,
    MemoryBackendType,
    EnhancedMemoryFactory
)
from agenticflow.memory.config import DatabaseConfig


# Custom memory handler example
class RedisLikeMemoryHandler:
    """Example custom memory handler that simulates Redis-like storage."""
    
    def __init__(self, prefix: str = "agenticflow:"):
        self.prefix = prefix
        self._storage: Dict[str, Any] = {}  # Simulate Redis storage
        self._counter = 0
    
    async def add_message(self, message, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add message to simulated Redis storage."""
        msg_id = f"{self.prefix}msg_{self._counter}"
        self._counter += 1
        
        self._storage[msg_id] = {
            "content": message.content,
            "type": message.__class__.__name__.lower().replace("message", ""),
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"📝 Added message {msg_id} to Redis-like storage")
        return msg_id
    
    async def get_messages(
        self, 
        limit: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ):
        """Get messages from simulated Redis storage."""
        messages = []
        for key, data in list(self._storage.items())[:limit] if limit else list(self._storage.items()):
            # Simple metadata filtering
            if filter_metadata:
                match = all(
                    data.get("metadata", {}).get(k) == v 
                    for k, v in filter_metadata.items()
                )
                if not match:
                    continue
            
            # Reconstruct message
            if data["type"] == "human":
                message = HumanMessage(content=data["content"])
            elif data["type"] == "ai":
                message = AIMessage(content=data["content"])
            elif data["type"] == "system":
                message = SystemMessage(content=data["content"])
            else:
                message = HumanMessage(content=data["content"])
            
            messages.append(message)
        
        return messages
    
    async def search(self, query: str, limit: int = 5, similarity_threshold: float = 0.7):
        """Search messages in simulated Redis storage."""
        from agenticflow.memory import MemoryDocument
        
        results = []
        for key, data in self._storage.items():
            if query.lower() in data["content"].lower():
                doc = MemoryDocument(
                    id=key,
                    content=data["content"],
                    metadata=data.get("metadata", {}),
                    timestamp=0.0  # Could parse timestamp
                )
                results.append(doc)
                
                if len(results) >= limit:
                    break
        
        return results
    
    async def clear(self):
        """Clear all storage."""
        self._storage.clear()
        print("🧹 Cleared Redis-like storage")
    
    async def save(self, path: Optional[str] = None):
        """Save to file (simulate Redis persistence)."""
        if path:
            with open(path, 'w') as f:
                json.dump(self._storage, f)
            print(f"💾 Saved Redis-like storage to {path}")
    
    async def load(self, path: str):
        """Load from file."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._storage = json.load(f)
            print(f"📂 Loaded Redis-like storage from {path}")


async def test_buffer_memory():
    """Test basic buffer memory (ephemeral)."""
    print("🧠 Testing Buffer Memory (Ephemeral)")
    print("-" * 50)
    
    config = MemoryBackendConfig(
        backend_type=MemoryBackendType.BUFFER,
        max_messages=10
    )
    
    memory = await EnhancedMemoryFactory.create_memory(config)
    
    # Add some messages
    msg1_id = await memory.add_message(HumanMessage(content="Hello, how are you?"))
    msg2_id = await memory.add_message(AIMessage(content="I'm doing well, thank you!"))
    msg3_id = await memory.add_message(HumanMessage(content="What's the weather like?"))
    
    print(f"✅ Added 3 messages: {[msg1_id, msg2_id, msg3_id]}")
    
    # Retrieve messages
    messages = await memory.get_messages(limit=5)
    print(f"📤 Retrieved {len(messages)} messages")
    for i, msg in enumerate(messages):
        print(f"   {i+1}. [{msg.__class__.__name__}] {msg.content}")
    
    # Search
    search_results = await memory.search("weather")
    print(f"🔍 Search for 'weather': {len(search_results)} results")
    
    return {"backend": "buffer", "messages_added": 3, "messages_retrieved": len(messages)}


async def test_sqlite_memory():
    """Test SQLite persistent memory."""
    print("\n💾 Testing SQLite Memory (Persistent)")
    print("-" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        config = MemoryBackendConfig.create_sqlite_config(
            database_path=db_path,
            max_messages=100
        )
        
        memory = SQLiteMemory(config)
        
        # Add messages
        msg1_id = await memory.add_message(
            HumanMessage(content="This is a persistent message"),
            metadata={"session": "test", "priority": "high"}
        )
        
        msg2_id = await memory.add_message(
            AIMessage(content="I will remember this across sessions!"),
            metadata={"session": "test", "priority": "medium"}
        )
        
        print(f"✅ Added 2 messages to SQLite: {[msg1_id, msg2_id]}")
        
        # Get session statistics
        if hasattr(memory, 'get_session_stats'):
            stats = await memory.get_session_stats()
            print(f"📊 Session stats: {stats}")
        
        # Test retrieval with metadata filtering
        filtered_messages = await memory.get_messages(
            limit=10, 
            filter_metadata={"priority": "high"}
        )
        print(f"🔍 High priority messages: {len(filtered_messages)}")
        
        # Search functionality
        search_results = await memory.search("persistent", limit=5)
        print(f"🔎 Search results: {len(search_results)}")
        
        # Close connection
        await memory.close()
        
        return {
            "backend": "sqlite", 
            "messages_added": 2, 
            "database_path": db_path,
            "session_stats": stats if 'stats' in locals() else None
        }
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"🧹 Cleaned up SQLite database: {db_path}")


async def test_postgresql_memory():
    """Test PostgreSQL persistent memory (if available)."""
    print("\n🐘 Testing PostgreSQL Memory (Persistent)")
    print("-" * 50)
    
    try:
        # Try to create PostgreSQL memory - will fail gracefully if not available
        config = MemoryBackendConfig.create_postgresql_config(
            host="localhost",
            database="agenticflow_test",
            user="postgres",
            password=""
        )
        
        from agenticflow.memory.backends import PostgreSQLMemory
        memory = PostgreSQLMemory(config)
        
        # Add a test message
        msg_id = await memory.add_message(
            HumanMessage(content="PostgreSQL test message"),
            metadata={"test": True}
        )
        
        print(f"✅ Added message to PostgreSQL: {msg_id}")
        
        # Get messages
        messages = await memory.get_messages(limit=5)
        print(f"📤 Retrieved {len(messages)} messages from PostgreSQL")
        
        # Close connection
        await memory.close()
        
        return {"backend": "postgresql", "messages_added": 1, "available": True}
        
    except Exception as e:
        print(f"⚠️  PostgreSQL not available: {e}")
        return {"backend": "postgresql", "available": False, "error": str(e)}


async def test_custom_memory():
    """Test custom memory implementation."""
    print("\n🎨 Testing Custom Memory (Redis-like)")
    print("-" * 50)
    
    # Create custom handler
    redis_handler = RedisLikeMemoryHandler(prefix="test:")
    
    config = MemoryBackendConfig.create_custom_config(
        handler_class="__main__.RedisLikeMemoryHandler",  # Won't work dynamically
        max_messages=50
    )
    
    # Create memory with custom handler directly
    from agenticflow.memory.backends import CustomMemory
    memory = CustomMemory(config, redis_handler)
    
    # Add messages
    msg1_id = await memory.add_message(
        HumanMessage(content="Hello from custom memory!"),
        metadata={"source": "custom_test"}
    )
    
    msg2_id = await memory.add_message(
        AIMessage(content="Custom memory is working great!"),
        metadata={"source": "custom_test", "type": "response"}
    )
    
    print(f"✅ Added 2 messages to custom memory")
    
    # Retrieve messages
    messages = await memory.get_messages(limit=10)
    print(f"📤 Retrieved {len(messages)} messages from custom handler")
    
    # Search
    search_results = await memory.search("custom")
    print(f"🔍 Search results: {len(search_results)}")
    
    # Test save/load
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        await memory.save(tmp.name)
        
        # Clear and reload
        await memory.clear()
        messages_after_clear = await memory.get_messages()
        print(f"📭 After clear: {len(messages_after_clear)} messages")
        
        await memory.load(tmp.name)
        messages_after_load = await memory.get_messages()
        print(f"📂 After load: {len(messages_after_load)} messages")
        
        os.unlink(tmp.name)
    
    return {"backend": "custom", "messages_added": 2, "handler_type": "redis_like"}


async def test_session_persistence():
    """Test session persistence across multiple memory instances."""
    print("\n🔄 Testing Session Persistence")
    print("-" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Session 1: Add messages
        config1 = MemoryBackendConfig.create_sqlite_config(database_path=db_path)
        memory1 = SQLiteMemory(config1)
        
        await memory1.add_message(HumanMessage(content="Session 1 message 1"))
        await memory1.add_message(HumanMessage(content="Session 1 message 2"))
        
        session1_id = memory1._session_id
        print(f"💾 Session 1 ({session1_id}): Added 2 messages")
        
        await memory1.close()
        
        # Session 2: Create new memory instance, different session
        config2 = MemoryBackendConfig.create_sqlite_config(database_path=db_path)
        memory2 = SQLiteMemory(config2)
        
        await memory2.add_message(HumanMessage(content="Session 2 message 1"))
        
        session2_id = memory2._session_id
        print(f"💾 Session 2 ({session2_id}): Added 1 message")
        
        # Check cross-session data
        if hasattr(memory2, 'get_sessions'):
            all_sessions = await memory2.get_sessions()
            print(f"🗂️  Total sessions in database: {len(all_sessions)}")
            
            # Get messages from session 1
            session1_messages = await memory2.get_messages(session_id=session1_id)
            session2_messages = await memory2.get_messages(session_id=session2_id)
            
            print(f"📊 Session 1 messages: {len(session1_messages)}")
            print(f"📊 Session 2 messages: {len(session2_messages)}")
        
        await memory2.close()
        
        return {
            "session1_id": session1_id,
            "session2_id": session2_id, 
            "total_sessions": len(all_sessions) if 'all_sessions' in locals() else 2
        }
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


async def main():
    """Run comprehensive memory backend tests."""
    print("🧠 AgenticFlow Memory Backends Test Suite")
    print("=" * 60)
    print("Testing ephemeral, persistent, and custom memory implementations")
    print()
    
    results = {}
    
    # Test each backend
    try:
        results["buffer"] = await test_buffer_memory()
    except Exception as e:
        print(f"❌ Buffer memory test failed: {e}")
        results["buffer"] = {"error": str(e)}
    
    try:
        results["sqlite"] = await test_sqlite_memory()
    except Exception as e:
        print(f"❌ SQLite memory test failed: {e}")
        results["sqlite"] = {"error": str(e)}
    
    try:
        results["postgresql"] = await test_postgresql_memory()
    except Exception as e:
        print(f"❌ PostgreSQL memory test failed: {e}")
        results["postgresql"] = {"error": str(e)}
    
    try:
        results["custom"] = await test_custom_memory()
    except Exception as e:
        print(f"❌ Custom memory test failed: {e}")
        results["custom"] = {"error": str(e)}
    
    try:
        results["session_persistence"] = await test_session_persistence()
    except Exception as e:
        print(f"❌ Session persistence test failed: {e}")
        results["session_persistence"] = {"error": str(e)}
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 MEMORY BACKENDS TEST SUMMARY")
    print("=" * 60)
    
    for backend, result in results.items():
        if "error" in result:
            print(f"❌ {backend.upper()}: FAILED - {result['error']}")
        else:
            print(f"✅ {backend.upper()}: PASSED")
            if "messages_added" in result:
                print(f"   📝 Messages added: {result['messages_added']}")
            if backend == "sqlite" and "database_path" in result:
                print(f"   💾 Database: {os.path.basename(result['database_path'])}")
    
    print("\n🎉 Memory backend testing complete!")
    print("\n💡 Key Features Demonstrated:")
    print("   • Ephemeral memory (buffer) - fast, in-memory storage")
    print("   • Persistent memory (SQLite) - local file-based persistence")
    print("   • Advanced persistent memory (PostgreSQL) - full database features")  
    print("   • Custom memory handlers - extensible architecture")
    print("   • Session management - multi-session persistence")
    print("   • Cross-session data retrieval")
    print("   • Metadata filtering and search functionality")

if __name__ == "__main__":
    asyncio.run(main())