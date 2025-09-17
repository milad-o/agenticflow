#!/usr/bin/env python3
"""
AgenticFlow Memory Backends Demo
================================
Demonstrates different memory backend types with practical examples.
"""

import asyncio
import json
import os
import sqlite3
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class SimpleMemoryBackend:
    """Base class for simple memory backends."""
    
    async def add_message(self, message, metadata=None):
        """Add a message to memory."""
        raise NotImplementedError
    
    async def get_messages(self, limit=None):
        """Get messages from memory."""
        raise NotImplementedError
    
    async def search(self, query, limit=5):
        """Search messages."""
        raise NotImplementedError
    
    def close(self):
        """Close resources."""
        pass


class BufferMemory(SimpleMemoryBackend):
    """Ephemeral in-memory buffer."""
    
    def __init__(self, max_messages=100):
        self.max_messages = max_messages
        self._messages = []
        self._counter = 0
    
    async def add_message(self, message, metadata=None):
        msg_id = f"msg_{self._counter}"
        self._counter += 1
        
        self._messages.append({
            'id': msg_id,
            'message': message,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow()
        })
        
        # Trim if needed
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]
        
        return msg_id
    
    async def get_messages(self, limit=None):
        messages = [item['message'] for item in self._messages]
        if limit:
            messages = messages[-limit:]
        return list(reversed(messages))
    
    async def search(self, query, limit=5):
        results = []
        for item in self._messages:
            if query.lower() in item['message'].content.lower():
                results.append({
                    'id': item['id'],
                    'content': item['message'].content,
                    'metadata': item['metadata']
                })
                if len(results) >= limit:
                    break
        return results


class SQLiteMemory(SimpleMemoryBackend):
    """Persistent SQLite memory."""
    
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self.session_id = str(uuid.uuid4())
        self._setup_tables()
    
    def _setup_tables(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    
    async def add_message(self, message, metadata=None):
        msg_id = str(uuid.uuid4())
        msg_type = message.__class__.__name__.lower().replace('message', '')
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO messages (id, session_id, message_type, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            msg_id, self.session_id, msg_type, message.content,
            json.dumps(metadata or {}), int(datetime.utcnow().timestamp())
        ))
        conn.commit()
        conn.close()
        
        return msg_id
    
    async def get_messages(self, limit=None, session_id=None):
        target_session = session_id or self.session_id
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at DESC"
        params = [target_session]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            if row['message_type'] == 'human':
                msg = HumanMessage(content=row['content'])
            elif row['message_type'] == 'ai':
                msg = AIMessage(content=row['content'])
            elif row['message_type'] == 'system':
                msg = SystemMessage(content=row['content'])
            else:
                msg = HumanMessage(content=row['content'])
            
            messages.append(msg)
        
        return messages
    
    async def search(self, query, limit=5):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('''
            SELECT * FROM messages 
            WHERE content LIKE ?
            ORDER BY created_at DESC LIMIT ?
        ''', (f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'content': row['content'],
                'metadata': json.loads(row['metadata'] or '{}'),
                'session_id': row['session_id']
            })
        
        conn.close()
        return results
    
    async def get_sessions(self):
        """Get all session IDs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT DISTINCT session_id FROM messages")
        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sessions


async def demo_buffer_memory():
    """Demonstrate ephemeral buffer memory."""
    print("💭 Buffer Memory (Ephemeral)")
    print("-" * 40)
    
    memory = BufferMemory(max_messages=10)
    
    # Add conversation
    await memory.add_message(HumanMessage(content="Hello, my name is Alice"))
    await memory.add_message(AIMessage(content="Hi Alice! Nice to meet you."))
    await memory.add_message(HumanMessage(content="I love programming in Python"))
    await memory.add_message(AIMessage(content="Python is a great language!"))
    
    # Retrieve messages
    messages = await memory.get_messages()
    print(f"📝 Stored {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        speaker = "👤" if isinstance(msg, HumanMessage) else "🤖"
        print(f"   {i}. {speaker} {msg.content}")
    
    # Search
    search_results = await memory.search("Python")
    print(f"🔍 Search for 'Python': {len(search_results)} results")
    
    print("⚠️  Memory lost when agent restarts!")
    return len(messages)


async def demo_sqlite_memory():
    """Demonstrate persistent SQLite memory."""
    print("\n💾 SQLite Memory (Persistent)")
    print("-" * 40)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Session 1
        memory1 = SQLiteMemory(db_path)
        session1_id = memory1.session_id
        
        await memory1.add_message(HumanMessage(content="Hi, I'm Bob from Seattle"))
        await memory1.add_message(AIMessage(content="Hello Bob! I'll remember you."))
        await memory1.add_message(HumanMessage(content="I work as a data scientist"))
        await memory1.add_message(AIMessage(content="Interesting! Data science is fascinating."))
        
        messages1 = await memory1.get_messages()
        print(f"📝 Session 1: {len(messages1)} messages stored")
        memory1.close()
        
        # Simulate restart - Session 2
        print("🔄 Restarting (new session)...")
        memory2 = SQLiteMemory(db_path)
        
        # Check what we can access
        all_sessions = await memory2.get_sessions()
        print(f"📚 Found {len(all_sessions)} sessions in database")
        
        # Access previous session
        previous_messages = await memory2.get_messages(session_id=session1_id)
        print(f"🔍 Previous session: {len(previous_messages)} messages recovered")
        
        # Add to current session
        await memory2.add_message(HumanMessage(content="Do you remember Bob?"))
        await memory2.add_message(AIMessage(content="I can access previous conversations!"))
        
        current_messages = await memory2.get_messages()
        print(f"📝 Current session: {len(current_messages)} new messages")
        
        # Search across all sessions
        search_results = await memory2.search("scientist")
        print(f"🔍 Search 'scientist' across all sessions: {len(search_results)} results")
        
        memory2.close()
        print("✅ Memory persists across restarts!")
        
        return {
            "sessions": len(all_sessions),
            "previous_messages": len(previous_messages),
            "current_messages": len(current_messages)
        }
    
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


async def memory_comparison():
    """Compare memory types side by side."""
    print("\n⚖️  Memory Comparison")
    print("-" * 40)
    
    buffer_mem = BufferMemory()
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        sqlite_mem = SQLiteMemory(db_path)
        
        # Same data to both
        test_data = [
            HumanMessage(content="Test message 1"),
            AIMessage(content="Response 1"),
            HumanMessage(content="Test message 2"),
            AIMessage(content="Response 2")
        ]
        
        for msg in test_data:
            await buffer_mem.add_message(msg)
            await sqlite_mem.add_message(msg)
        
        buffer_messages = await buffer_mem.get_messages()
        sqlite_messages = await sqlite_mem.get_messages()
        
        print(f"📊 Buffer Memory: {len(buffer_messages)} messages")
        print(f"📊 SQLite Memory: {len(sqlite_messages)} messages")
        print(f"✅ Both store the same data")
        
        # Performance note
        print(f"\n⚡ Performance Characteristics:")
        print(f"   Buffer: Fastest access, no persistence")
        print(f"   SQLite: Fast access, full persistence")
        print(f"   PostgreSQL: Scalable, multi-user support")
        
        sqlite_mem.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


async def main():
    """Run memory demonstration."""
    print("🧠 AgenticFlow Memory Backends Demonstration")
    print("=" * 60)
    print("Showing ephemeral vs persistent memory for AI agents\n")
    
    # Run demonstrations
    buffer_count = await demo_buffer_memory()
    sqlite_results = await demo_sqlite_memory()
    await memory_comparison()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 MEMORY SYSTEM SUMMARY")
    print("=" * 60)
    
    print("✅ Ephemeral Memory (Buffer):")
    print("   • In-memory storage")
    print("   • Fast access")
    print("   • Lost on restart")
    print("   • Best for: Temporary conversations, session context")
    
    print("\n✅ Persistent Memory (SQLite):")
    print("   • Database storage")
    print("   • Survives restarts")
    print("   • Session management")
    print("   • Cross-session access")
    print("   • Best for: Personal assistants, customer history")
    
    print("\n✅ Advanced Persistent (PostgreSQL):")
    print("   • Full database features")
    print("   • Multi-user support")
    print("   • Advanced queries")
    print("   • Best for: Enterprise systems, analytics")
    
    print(f"\n🎯 Choose Your Memory Backend:")
    print(f"   Development/Testing: Buffer Memory")
    print(f"   Production Single-User: SQLite Memory")
    print(f"   Production Multi-User: PostgreSQL Memory")
    print(f"   Custom Needs: Custom Memory Handler")

if __name__ == "__main__":
    asyncio.run(main())