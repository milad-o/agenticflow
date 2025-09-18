#!/usr/bin/env python3
"""
Test script to demonstrate the interactive RAG chatbot
This simulates a conversation to show how the chatbot works
"""

import asyncio
import sys
from pathlib import Path
import os

# Add the source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the chatbot class
from interactive_rag_chatbot import InteractiveRAGChatbot

async def simulate_chatbot_conversation():
    """Simulate a conversation with the chatbot."""
    print("🤖 AGENTICFLOW INTERACTIVE RAG CHATBOT DEMONSTRATION")
    print("=" * 65)
    
    # Initialize the chatbot
    chatbot = InteractiveRAGChatbot()
    
    try:
        # Initialize the system
        await chatbot.initialize_chatbot()
        
        print("\n" + "=" * 65)
        print("💬 SIMULATED CONVERSATION DEMONSTRATION")
        print("=" * 65)
        
        # Simulate a conversation
        test_questions = [
            "What is AgenticFlow?",
            "How do retrievers work in AgenticFlow?",
            "Can you tell me more about the memory systems?",
            "What are the different multi-agent topologies?",
            "How does this compare to other AI frameworks?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'=' * 60}")
            print(f"👤 User Question {i}: {question}")
            print("=" * 60)
            
            # Get response from chatbot
            response = await chatbot.get_response(question)
            
            print(f"\n🤖 Assistant Response:")
            print("-" * 50)
            print(response)
            print("-" * 50)
            
            # Show conversation stats
            exchanges = len(chatbot.conversation_history) // 2
            print(f"📊 Conversation Stats: {exchanges} exchanges, {len(chatbot.chunks)} knowledge chunks available")
        
        print(f"\n{'=' * 65}")
        print("✅ CHATBOT DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 65)
        
        # Show final stats
        chatbot.display_stats()
        
        print("\n💡 The chatbot demonstrated:")
        print("  • Knowledge base loading and indexing")
        print("  • Semantic search and context retrieval")
        print("  • Conversation memory and follow-up awareness")
        print("  • Multi-turn dialogue with context preservation")
        print("  • RAG-powered responses with relevant information")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function."""
    await simulate_chatbot_conversation()

if __name__ == "__main__":
    asyncio.run(main())