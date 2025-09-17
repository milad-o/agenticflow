#!/usr/bin/env python3
"""
Agent Memory Backend Demo
========================
Demonstrates how to use different memory backends with AgenticFlow agents
for ephemeral and persistent conversation memory.
"""

import asyncio
import tempfile
import os
from pathlib import Path

from agenticflow import Agent
from agenticflow.config.settings import AgentConfig, LLMProvider, LLMProviderConfig
from test_memory_simple import SimpleSQLiteMemory, SimpleBufferMemory


class MemoryDemoAgent:
    """Demo agent that uses different memory backends."""
    
    def __init__(self, name: str, memory_backend):
        self.name = name
        self.memory = memory_backend
        self.conversation_count = 0
    
    async def start(self):
        """Start the agent."""
        print(f"🤖 Starting agent '{self.name}'")
    
    async def stop(self):
        """Stop the agent and clean up memory."""
        if hasattr(self.memory, 'close'):
            self.memory.close()
        print(f"🛑 Stopped agent '{self.name}'")
    
    async def chat(self, user_message: str) -> str:
        """Simulate a chat interaction with memory persistence."""
        from langchain_core.messages import HumanMessage, AIMessage
        
        self.conversation_count += 1
        
        # Store user message
        await self.memory.add_message(
            HumanMessage(content=user_message),
            metadata={
                "conversation_id": self.conversation_count,
                "speaker": "user"
            }
        )
        
        # Simulate AI response (in real implementation, this would use LLM)
        if "weather" in user_message.lower():
            ai_response = "The weather is sunny and 72°F today!"
        elif "remember" in user_message.lower():
            # Get conversation history
            history = await self.memory.get_messages(limit=5)
            ai_response = f"I remember our last {len(history)-1} messages. What would you like to know?"
        elif "hello" in user_message.lower():
            ai_response = f"Hello! This is agent '{self.name}'. How can I help you?"
        else:
            ai_response = f"I understand you said: '{user_message}'. How can I assist you further?"
        
        # Store AI response
        await self.memory.add_message(
            AIMessage(content=ai_response),
            metadata={
                "conversation_id": self.conversation_count,
                "speaker": "assistant"
            }
        )
        
        return ai_response
    
    async def get_conversation_summary(self) -> dict:
        """Get summary of conversation history."""
        messages = await self.memory.get_messages()
        
        summary = {
            "agent_name": self.name,
            "total_messages": len(messages),
            "conversations": self.conversation_count,
            "recent_messages": []
        }
        
        # Add recent messages
        for msg in messages[:6]:  # Last 3 exchanges
            summary["recent_messages"].append({
                "type": msg.__class__.__name__,
                "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            })
        
        return summary


async def demo_buffer_memory():
    """Demonstrate agent with buffer (ephemeral) memory."""
    print("💭 Buffer Memory Agent Demo")
    print("-" * 40)
    
    # Create agent with buffer memory
    buffer_memory = SimpleBufferMemory(max_messages=20)
    agent = MemoryDemoAgent("BufferBot", buffer_memory)
    
    await agent.start()
    
    # Simulate conversation
    responses = []
    
    response1 = await agent.chat("Hello! Nice to meet you.")
    print(f"User: Hello! Nice to meet you.")
    print(f"BufferBot: {response1}")
    responses.append(response1)
    
    response2 = await agent.chat("What's the weather like?")
    print(f"User: What's the weather like?")
    print(f"BufferBot: {response2}")
    responses.append(response2)
    
    response3 = await agent.chat("Do you remember what I asked you?")
    print(f"User: Do you remember what I asked you?")
    print(f"BufferBot: {response3}")
    responses.append(response3)
    
    # Get conversation summary
    summary = await agent.get_conversation_summary()
    print(f"\n📊 Conversation Summary:")
    print(f"   Total messages: {summary['total_messages']}")
    print(f"   Conversations: {summary['conversations']}")
    
    await agent.stop()
    
    return {
        "agent_type": "buffer",
        "responses": len(responses),
        "memory_persistent": False
    }


async def demo_sqlite_memory():
    """Demonstrate agent with SQLite (persistent) memory."""
    print("\n🗃️ SQLite Memory Agent Demo")
    print("-" * 40)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Create agent with SQLite memory
        sqlite_memory = SimpleSQLiteMemory(db_path)
        agent = MemoryDemoAgent("PersistentBot", sqlite_memory)
        
        await agent.start()
        
        # First conversation session
        print("📱 Session 1:")
        response1 = await agent.chat("Hi, I'm starting a new conversation.")
        print(f"User: Hi, I'm starting a new conversation.")
        print(f"PersistentBot: {response1}")
        
        response2 = await agent.chat("Please remember that my favorite color is blue.")
        print(f"User: Please remember that my favorite color is blue.")
        print(f"PersistentBot: {response2}")
        
        # Get session stats after first session
        session1_id = sqlite_memory.session_id
        stats1 = await sqlite_memory.get_session_stats()
        print(f"📊 Session 1 stats: {stats1['message_count']} messages")
        
        await agent.stop()
        
        # Simulate agent restart (new session, same database)
        print("\n📱 Session 2 (after restart):")
        sqlite_memory2 = SimpleSQLiteMemory(db_path)
        agent2 = MemoryDemoAgent("PersistentBot", sqlite_memory2)
        
        await agent2.start()
        
        response3 = await agent2.chat("Do you remember our previous conversation?")
        print(f"User: Do you remember our previous conversation?")
        print(f"PersistentBot: {response3}")
        
        # Check if we can access previous session data
        all_sessions = await sqlite_memory2.get_sessions()
        print(f"🗂️  Total sessions in database: {len(all_sessions)}")
        
        # Get messages from previous session
        previous_messages = await sqlite_memory2.get_messages(session_id=session1_id)
        print(f"💾 Previous session had {len(previous_messages)} messages")
        
        await agent2.stop()
        
        return {
            "agent_type": "sqlite",
            "sessions": len(all_sessions),
            "previous_session_messages": len(previous_messages),
            "memory_persistent": True
        }
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"🧹 Cleaned up database")


async def demo_memory_comparison():
    """Compare memory behavior between ephemeral and persistent backends."""
    print("\n⚖️  Memory Comparison Demo")
    print("-" * 40)
    
    # Create agents with different memory types
    buffer_agent = MemoryDemoAgent("EphemeralBot", SimpleBufferMemory())
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        persistent_agent = MemoryDemoAgent("PersistentBot", SimpleSQLiteMemory(db_path))
        
        await buffer_agent.start()
        await persistent_agent.start()
        
        # Same conversation for both agents
        test_message = "Remember: my name is Alice and I like pizza."
        
        print(f"User to both agents: {test_message}")
        
        buffer_response = await buffer_agent.chat(test_message)
        persistent_response = await persistent_agent.chat(test_message)
        
        print(f"EphemeralBot: {buffer_response}")
        print(f"PersistentBot: {persistent_response}")
        
        # Get summaries
        buffer_summary = await buffer_agent.get_conversation_summary()
        persistent_summary = await persistent_agent.get_conversation_summary()
        
        print(f"\n📊 Memory Comparison:")
        print(f"   Ephemeral (Buffer): {buffer_summary['total_messages']} messages")
        print(f"   Persistent (SQLite): {persistent_summary['total_messages']} messages")
        
        await buffer_agent.stop()
        await persistent_agent.stop()
        
        # Test persistence: Restart persistent agent
        print(f"\n🔄 Restarting PersistentBot...")
        persistent_agent2 = MemoryDemoAgent("PersistentBot-Restarted", SimpleSQLiteMemory(db_path))
        await persistent_agent2.start()
        
        # Check if it remembers
        all_sessions = await persistent_agent2.memory.get_sessions()
        print(f"📚 After restart: {len(all_sessions)} sessions found in database")
        
        await persistent_agent2.stop()
        
        return {
            "buffer_messages": buffer_summary['total_messages'],
            "persistent_messages": persistent_summary['total_messages'],
            "persistent_sessions": len(all_sessions)
        }
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


async def main():
    """Run comprehensive agent memory demonstration."""
    print("🧠 AgenticFlow Agent Memory Backend Demo")
    print("=" * 60)
    print("Demonstrating ephemeral vs persistent memory in AI agents")
    print()
    
    results = {}
    
    try:
        results["buffer"] = await demo_buffer_memory()
    except Exception as e:
        print(f"❌ Buffer demo failed: {e}")
        results["buffer"] = {"error": str(e)}
    
    try:
        results["sqlite"] = await demo_sqlite_memory()
    except Exception as e:
        print(f"❌ SQLite demo failed: {e}")
        results["sqlite"] = {"error": str(e)}
    
    try:
        results["comparison"] = await demo_memory_comparison()
    except Exception as e:
        print(f"❌ Comparison demo failed: {e}")
        results["comparison"] = {"error": str(e)}
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 AGENT MEMORY DEMO SUMMARY")
    print("=" * 60)
    
    for demo_type, result in results.items():
        if "error" in result:
            print(f"❌ {demo_type.upper()}: FAILED - {result['error']}")
        else:
            print(f"✅ {demo_type.upper()}: SUCCESS")
            if "memory_persistent" in result:
                persistence = "Persistent" if result["memory_persistent"] else "Ephemeral"
                print(f"   Memory Type: {persistence}")
    
    print(f"\n🎉 Agent memory demonstration complete!")
    print(f"\n💡 Key Concepts Demonstrated:")
    print(f"   • Ephemeral Memory: Fast, in-memory storage (lost on restart)")
    print(f"   • Persistent Memory: SQLite database storage (survives restarts)")
    print(f"   • Session Management: Multiple conversation sessions")
    print(f"   • Cross-Session Access: Agents can access previous sessions")
    print(f"   • Memory Integration: Seamless memory backend switching")
    
    print(f"\n🚀 Production Use Cases:")
    print(f"   • Customer service bots: Persistent customer history")
    print(f"   • Personal assistants: Remember user preferences")
    print(f"   • Development tools: Session-based conversation memory")
    print(f"   • Multi-user systems: Per-user memory isolation")

if __name__ == "__main__":
    asyncio.run(main())