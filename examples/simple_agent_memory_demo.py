#!/usr/bin/env python3
"""
Simple Agent Memory Demo
========================
Demonstrates ephemeral vs persistent memory in AI agents.
"""

import asyncio
from test_memory_simple import SimpleSQLiteMemory, SimpleBufferMemory


async def main():
    """Run agent memory demonstration."""
    print("🧠 AgenticFlow Agent Memory Demo")
    print("=" * 50)
    print("Demonstrating different memory backends for AI agents")
    print()
    
    # Test 1: Ephemeral Memory Agent
    print("1️⃣ Ephemeral Memory Agent (Buffer)")
    print("-" * 40)
    
    buffer_memory = SimpleBufferMemory(max_messages=10)
    
    from langchain_core.messages import HumanMessage, AIMessage
    
    # Simulate conversation
    await buffer_memory.add_message(HumanMessage(content="Hi, I'm Alice"))
    await buffer_memory.add_message(AIMessage(content="Hello Alice! Nice to meet you."))
    await buffer_memory.add_message(HumanMessage(content="My favorite color is blue"))
    await buffer_memory.add_message(AIMessage(content="I'll remember that you like blue!"))
    
    messages = await buffer_memory.get_messages()
    print(f"💭 Ephemeral agent remembers {len(messages)} messages")
    for i, msg in enumerate(messages):
        speaker = "🧑 User" if "HumanMessage" in str(type(msg)) else "🤖 Agent"
        print(f"   {speaker}: {msg.content}")
    
    print("🔄 After restart, ephemeral memory is lost!")
    
    # Test 2: Persistent Memory Agent
    print(f"\n2️⃣ Persistent Memory Agent (SQLite)")
    print("-" * 40)
    
    # Use a persistent file (don't delete)
    db_path = "demo_agent_memory.db"
    sqlite_memory = SimpleSQLiteMemory(db_path)
    
    # Add some conversation
    await sqlite_memory.add_message(HumanMessage(content="Hi, I'm Bob"))
    await sqlite_memory.add_message(AIMessage(content="Hello Bob! I'll remember you."))
    await sqlite_memory.add_message(HumanMessage(content="I work as a developer"))
    await sqlite_memory.add_message(AIMessage(content="Great! I've noted that you're a developer."))
    
    session1_id = sqlite_memory.session_id
    messages = await sqlite_memory.get_messages()
    print(f"💾 Persistent agent remembers {len(messages)} messages")
    
    # Get session stats
    stats = await sqlite_memory.get_session_stats()
    print(f"📊 Session stats: {stats['message_count']} messages, duration: {stats['duration_seconds']}s")
    
    sqlite_memory.close()
    
    # Simulate restart
    print(f"\n🔄 Restarting persistent agent...")
    sqlite_memory2 = SimpleSQLiteMemory(db_path)
    
    # Check what it remembers
    all_sessions = await sqlite_memory2.get_sessions()
    print(f"📚 Found {len(all_sessions)} sessions in database")
    
    # Access previous session
    previous_messages = await sqlite_memory2.get_messages(session_id=session1_id)
    print(f"💾 Previous session: {len(previous_messages)} messages recovered")
    
    # Add to new session
    await sqlite_memory2.add_message(HumanMessage(content="Do you remember me?"))
    await sqlite_memory2.add_message(AIMessage(content="I can access our previous conversation!"))
    
    current_messages = await sqlite_memory2.get_messages()
    print(f"🆕 Current session: {len(current_messages)} messages")
    
    sqlite_memory2.close()
    
    print(f"\n" + "=" * 50)
    print("📋 MEMORY COMPARISON SUMMARY")
    print("=" * 50)
    print("✅ Ephemeral Memory (Buffer):")
    print("   • Fast, in-memory storage")
    print("   • Lost when agent restarts")
    print("   • Best for temporary conversations")
    print()
    print("✅ Persistent Memory (SQLite):")
    print("   • Database-backed storage")  
    print("   • Survives agent restarts")
    print("   • Session management")
    print("   • Cross-session data access")
    print("   • Best for long-term memory")
    
    print(f"\n🎯 Use Cases:")
    print(f"   Buffer: Chat sessions, temporary context")
    print(f"   SQLite: Customer history, personal assistants")
    print(f"   PostgreSQL: Multi-user systems, analytics")
    
    # Clean up (optional - keep for demo persistence)
    # import os
    # if os.path.exists(db_path):
    #     os.unlink(db_path)
    #     print(f"\n🧹 Cleaned up {db_path}")

if __name__ == "__main__":
    asyncio.run(main())