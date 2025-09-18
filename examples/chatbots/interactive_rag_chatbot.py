#!/usr/bin/env python3
"""
Interactive RAG Chatbot with AgenticFlow

This chatbot demonstrates:
- Interactive conversation with follow-up questions
- Conversation memory and context awareness
- RAG-powered responses with document retrieval
- Natural conversation flow with the knowledge base

Features:
- Real-time chat interface
- Conversation history tracking
- Context-aware follow-up questions
- RAG integration for knowledge-based responses
- Multiple conversation modes

Usage:
    python examples/chatbots/interactive_rag_chatbot.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agenticflow import Agent, LLMProviderConfig
from agenticflow.config.settings import AgentConfig, LLMProvider
from agenticflow.memory import VectorMemory, BufferMemory
from agenticflow.memory.vector_memory import VectorMemoryConfig
from agenticflow.config.settings import MemoryConfig
from agenticflow.vectorstores.factory import VectorStoreFactory
from agenticflow.text.splitters.manager import split_text
from agenticflow.text import SplitterType
from agenticflow.retrievers import (
    HybridRetriever, BM25Retriever, create_from_memory
)
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import HumanMessage, AIMessage

class InteractiveRAGChatbot:
    """Interactive chatbot with RAG capabilities and conversation memory."""
    
    def __init__(self):
        self.documents: List[str] = []
        self.chunks: List[Any] = []
        self.embeddings: Optional[Any] = None
        self.vector_memory: Optional[VectorMemory] = None
        self.conversation_memory: Optional[BufferMemory] = None
        self.retriever: Optional[Any] = None
        self.chatbot_agent: Optional[Agent] = None
        
        # Conversation state
        self.conversation_history: List[Dict[str, str]] = []
        self.session_id = f"chat_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_context: List[str] = []
        self.conversation_active = True
    
    async def setup_embeddings(self) -> None:
        """Setup embedding provider with multiple fallbacks."""
        print("🧮 Setting up embeddings...")
        
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                print("  ✅ Using OpenAI embeddings (premium quality)")
                return
            except Exception as e:
                print(f"  ❌ OpenAI embeddings failed: {e}")
        
        try:
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
            await self.embeddings.aembed_query("test")
            print("  ✅ Using Ollama embeddings (local, free)")
            return
        except Exception as e:
            print(f"  ❌ Ollama embeddings failed: {e}")
        
        raise RuntimeError("❌ No embedding provider available. Please install Ollama or set OPENAI_API_KEY.")
    
    async def load_knowledge_base(self) -> None:
        """Load knowledge base documents from external files, including custom topics."""
        print("📚 Loading knowledge base from external documents...")
        
        self.documents = []
        self.knowledge_docs = {}  # Track document sources
        
        # 1. Load from built-in knowledge_base directory
        knowledge_base_path = Path(__file__).parent / "knowledge_base"
        if knowledge_base_path.exists() and knowledge_base_path.is_dir():
            text_files = list(knowledge_base_path.glob("*.txt"))
            print(f"  🔍 Found {len(text_files)} built-in knowledge documents")
            
            for file_path in sorted(text_files):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:  # Only add non-empty files
                            self.documents.append(content)
                            self.knowledge_docs[file_path.name] = content
                            print(f"  📄 Loaded: {file_path.name} ({len(content)} chars)")
                except Exception as e:
                    print(f"  ⚠️ Error loading {file_path}: {e}")
        
        # 2. Load from user's custom knowledge directory
        custom_knowledge_path = Path.home() / ".agenticflow" / "knowledge"
        if custom_knowledge_path.exists() and custom_knowledge_path.is_dir():
            custom_text_files = list(custom_knowledge_path.glob("*.txt"))
            if custom_text_files:
                print(f"  🏠 Found {len(custom_text_files)} custom knowledge documents")
                
                for file_path in sorted(custom_text_files):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:  # Only add non-empty files
                                self.documents.append(content)
                                self.knowledge_docs[f"[custom] {file_path.name}"] = content
                                print(f"  🏠 Custom loaded: {file_path.name} ({len(content)} chars)")
                    except Exception as e:
                        print(f"  ⚠️ Error loading custom {file_path}: {e}")
        
        # 3. Load from examples/retrievers/sample_docs (compatibility)
        sample_docs_path = Path("examples/retrievers/sample_docs")
        if sample_docs_path.exists() and sample_docs_path.is_dir():
            text_files = list(sample_docs_path.glob("*.txt"))
            for file_path in text_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:  # Only add non-empty files
                            self.documents.append(content)
                            self.knowledge_docs[f"[compat] {file_path.name}"] = content
                            print(f"  📄 Additional doc loaded: {file_path.name} ({len(content)} chars)")
                except Exception as e:
                    print(f"  ⚠️ Error loading {file_path}: {e}")
        
        # 4. Show instructions for custom knowledge if none found
        if not any(key.startswith("[custom]") for key in self.knowledge_docs.keys()):
            print(f"\n💡 To add custom knowledge:")
            print(f"   1. Create directory: {custom_knowledge_path}")
            print(f"   2. Add .txt files with your domain-specific content")
            print(f"   3. Restart the chatbot to load your custom knowledge")
            print(f"   🌟 The chatbot will automatically include your custom topics!")
        
        # Fallback if no documents loaded
        if not self.documents:
            print("  📝 Creating basic fallback knowledge...")
            self.documents = ["This is a science chatbot with knowledge about nature, space, and the natural world."]
            self.knowledge_docs["fallback.txt"] = self.documents[0]
        
        print(f"📚 Knowledge base ready: {len(self.documents)} total documents")
    
    async def setup_memories(self) -> None:
        """Setup both vector memory for RAG and conversation memory."""
        print("🧠 Setting up memory systems...")
        
        # Setup vector memory for knowledge base
        if self.embeddings:
            vector_store_config = VectorStoreFactory.create_faiss_config(
                persist_path="./chatbot_vectors",
                embedding_dimension=1536 if "openai" in str(self.embeddings.__class__).lower() else 768
            )
            
            memory_config = VectorMemoryConfig(vector_store_config=vector_store_config)
            base_config = MemoryConfig()
            
            self.vector_memory = VectorMemory(base_config, memory_config, self.embeddings)
            print("  ✅ Vector memory ready for knowledge base")
        
        # Setup conversation memory
        conv_config = MemoryConfig(max_messages=50)  # Keep last 50 messages
        self.conversation_memory = BufferMemory(conv_config)
        print("  ✅ Conversation memory ready")
    
    async def index_knowledge_base(self) -> None:
        """Index documents in vector memory."""
        if not self.vector_memory:
            print("  ⚠️ Skipping indexing - no vector memory available")
            return
            
        print("📊 Indexing knowledge base...")
        
        # Initialize the text splitter manager
        from agenticflow.text.splitters.manager import initialize_manager
        try:
            manager = await initialize_manager()
            print("  ✅ Text splitter manager initialized")
        except Exception as e:
            print(f"  ⚠️ Splitter manager initialization failed: {e}")
        
        all_chunks = []
        for i, doc in enumerate(self.documents):
            try:
                chunks = await split_text(
                    doc.strip(),
                    splitter_type=SplitterType.RECURSIVE,
                    chunk_size=400,
                    chunk_overlap=100
                )
                
                for chunk in chunks:
                    chunk.metadata["doc_id"] = i
                    chunk.metadata["source"] = f"knowledge_doc_{i}"
                    all_chunks.append(chunk)
                    
            except Exception as e:
                print(f"  ❌ Error chunking document {i}: {e}")
        
        self.chunks = all_chunks
        
        # Index in vector memory
        from langchain_core.messages import HumanMessage
        for chunk in self.chunks:
            try:
                message = HumanMessage(content=chunk.content)
                await self.vector_memory.add_message(message, metadata=chunk.metadata)
            except Exception as e:
                print(f"  ❌ Error indexing chunk: {e}")
        
        print(f"  ✅ Indexed {len(self.chunks)} knowledge chunks")
        
        # Debug: Show sample of what was indexed
        if self.chunks:
            print("  📝 Sample indexed content:")
            for i, chunk in enumerate(self.chunks[:3]):  # Show first 3 chunks
                preview = chunk.content[:100].replace('\n', ' ')
                print(f"    Chunk {i+1}: {preview}...")
    
    async def setup_retriever(self) -> None:
        """Setup intelligent hybrid retriever."""
        if not self.vector_memory:
            print("  ⚠️ No vector memory - using text-only retrieval")
            # Create a simple text data source for BM25
            text_data_source = self._create_text_data_source()
            self.retriever = BM25Retriever(text_data_source)
            return
        
        print("🔍 Setting up intelligent retriever...")
        
        # Debug: Check what chunks we have
        print(f"  📝 Available chunks: {len(self.chunks)}")
        if self.chunks:
            print(f"  📝 Sample chunk attributes: {dir(self.chunks[0])}")
            if hasattr(self.chunks[0], 'content'):
                print(f"  📝 First chunk content: {self.chunks[0].content[:100]}...")
        
        print(f"  📝 Text data for BM25: {len(self.chunks)} chunks")
        
        semantic_retriever = create_from_memory(self.vector_memory)
        
        # Create a text data source for BM25 retriever
        text_data_source = self._create_text_data_source()
        sparse_retriever = BM25Retriever(text_data_source)
        
        # Create hybrid retriever combining semantic and BM25
        self.retriever = HybridRetriever(
            dense_retriever=semantic_retriever,
            sparse_retriever=sparse_retriever
        )
        
        print("  ✅ Hybrid retriever ready (text + semantic)")
    
    def _create_text_data_source(self):
        """Create a simple data source wrapper for text-based retrievers."""
        from agenticflow.memory.core import MemoryDocument
        import time
        
        class TextDataSource:
            def __init__(self, chunks):
                # Convert text fragments to MemoryDocument objects
                self.documents = []
                for i, chunk in enumerate(chunks):
                    doc = MemoryDocument(
                        id=f"chunk_{i}",
                        content=chunk.content if hasattr(chunk, 'content') else str(chunk),
                        metadata=getattr(chunk, 'metadata', {}),
                        timestamp=time.time()
                    )
                    self.documents.append(doc)
            
            async def search(self, query: str, limit: int = 10):
                # Simple keyword search for BM25 retriever
                return self.documents[:limit]
        
        return TextDataSource(self.chunks)
    
    async def setup_chatbot_agent(self) -> None:
        """Setup the conversational agent."""
        print("🤖 Setting up chatbot agent...")
        
        # Determine best LLM provider
        llm_config = None
        provider_name = "Unknown"
        
        if os.getenv("GROQ_API_KEY"):
            llm_config = LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            )
            provider_name = "Groq (fast)"
        elif os.getenv("OPENAI_API_KEY"):
            llm_config = LLMProviderConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini"
            )
            provider_name = "OpenAI"
        else:
            # Try available Ollama models
            ollama_models = ["granite3.2:8b", "qwen2.5:7b", "llama3.2", "llama2"]
            for model in ollama_models:
                try:
                    llm_config = LLMProviderConfig(
                        provider=LLMProvider.OLLAMA,
                        model=model
                    )
                    provider_name = f"Ollama ({model})"
                    break
                except Exception:
                    continue
            else:
                # Ultimate fallback to Groq if no Ollama models work
                llm_config = LLMProviderConfig(
                    provider=LLMProvider.GROQ,
                    model="llama-3.1-8b-instant"
                )
                provider_name = "Groq (fallback)"
        
        # Configure agent with conversation and RAG capabilities
        config = AgentConfig(
            name="science_chatbot",
            instructions="""You are an intelligent, helpful AI assistant with access to a comprehensive knowledge base about nature, space, and science.

Your personality and behavior:
- Be conversational, friendly, and engaging
- Show enthusiasm about helping users learn about the natural world
- Ask clarifying questions when needed
- Reference specific information from the knowledge base when relevant
- Maintain context across multiple conversation turns
- Provide practical examples and fascinating facts

When answering questions:
1. Use the retrieved context to provide accurate, detailed information
2. If the context doesn't fully answer the question, say so and provide what you can
3. For follow-up questions, consider the previous conversation context
4. Suggest related topics the user might be interested in
5. Be concise but thorough - aim for helpful, not overwhelming responses
6. Share interesting facts and examples that make science come alive

Remember: You have access to detailed information about ocean life, space exploration, wildlife behavior, earth sciences, physics, chemistry, and biology. Use this knowledge to inspire curiosity and provide educational, engaging responses.""",
            llm=llm_config,
            memory=MemoryConfig(max_messages=20)  # Keep conversation context
        )
        
        self.chatbot_agent = Agent(config)
        print(f"  ✅ Chatbot ready with {provider_name}")
    
    async def retrieve_context(self, query: str, max_context: int = 3) -> List[str]:
        """Retrieve relevant context for the query."""
        if not self.retriever:
            return []
        
        try:
            results = await self.retriever.retrieve(query, top_k=max_context)
            context_list = []
            
            print(f"    Raw retrieval results: {len(results)} items")
            
            for i, result in enumerate(results):
                print(f"    Result {i+1} type: {type(result)}")
                content = None
                
                # Try multiple ways to extract content
                if hasattr(result, 'document') and hasattr(result.document, 'page_content'):
                    content = result.document.page_content
                elif hasattr(result, 'document') and hasattr(result.document, 'content'):
                    content = result.document.content
                elif hasattr(result, 'page_content'):
                    content = result.page_content
                elif hasattr(result, 'content'):
                    content = result.content
                else:
                    content = str(result)
                
                if content:
                    context_list.append(content)
                    print(f"    Extracted content: {content[:100]}...")
            
            return context_list
        except Exception as e:
            print(f"  ⚠️ Context retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def format_conversation_context(self, limit: int = 6) -> str:
        """Format recent conversation history for context."""
        if not self.conversation_history:
            return ""
        
        # Get recent exchanges (limit pairs of user/assistant messages)
        recent_history = self.conversation_history[-(limit * 2):]
        
        context_parts = []
        for entry in recent_history:
            role = "You" if entry["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {entry['content']}")
        
        return "\n".join(context_parts)
    
    async def get_response(self, user_message: str) -> str:
        """Generate response using RAG and conversation context."""
        print(f"\n🤔 Processing: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'")
        
        # Retrieve relevant context
        print("  🔍 Retrieving context...")
        retrieved_context = await self.retrieve_context(user_message, max_context=3)
        print(f"  📄 Retrieved {len(retrieved_context)} context items")
        
        # Get conversation history
        conversation_context = self.format_conversation_context(limit=4)
        
        # Build comprehensive prompt
        prompt_parts = []
        
        # Add conversation history if available
        if conversation_context:
            prompt_parts.append(f"Recent conversation:\n{conversation_context}\n")
        
        # Add retrieved context
        if retrieved_context:
            prompt_parts.append("Relevant information from knowledge base:")
            for i, context in enumerate(retrieved_context, 1):
                prompt_parts.append(f"{i}. {context}")
            prompt_parts.append("")
        else:
            prompt_parts.append("No specific information found in knowledge base for this query.\n")
        
        # Add user query
        prompt_parts.append(f"User: {user_message}")
        prompt_parts.append("\nPlease provide a helpful response:")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            # Generate response
            print("  🧠 Generating response...")
            # Start the agent if not already started
            if not self.chatbot_agent._running:
                await self.chatbot_agent.start()
            
            response = await self.chatbot_agent.execute_task(prompt)
            answer = response.get('response', '') if isinstance(response, dict) else str(response)
            
            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            # Store in conversation memory
            if self.conversation_memory:
                try:
                    user_msg = HumanMessage(content=user_message)
                    ai_msg = AIMessage(content=answer)
                    await self.conversation_memory.add_message(user_msg)
                    await self.conversation_memory.add_message(ai_msg)
                except Exception as e:
                    print(f"  ⚠️ Memory storage failed: {e}")
            
            return answer
        
        except Exception as e:
            error_response = f"I apologize, but I encountered an error processing your request: {e}"
            print(f"  ❌ Error generating response: {e}")
            return error_response
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        print("\n" + "=" * 60)
        print("🔬 Interactive Science & Nature Chatbot")
        print("=" * 60)
        print("Welcome! I'm your AI assistant with knowledge about:")
        print("  • 🌊 Ocean life and marine biology")
        print("  • 🚀 Space exploration and astronomy")
        print("  • 🦁 Wildlife behavior and animal adaptations")
        print("  • 🌍 Earth sciences and geology")
        print("  • ⚛️ Physics and chemistry fundamentals")
        print("  • 🌱 Biology and life sciences")
        print()
        print("💡 What I can do:")
        print("  ✅ Answer questions about the natural world")
        print("  ✅ Handle follow-up questions and conversations")
        print("  ✅ Provide detailed explanations with fascinating facts")
        print("  ✅ Suggest related topics you might find interesting")
        print()
        print("🎯 Example questions you can ask:")
        print("  • 'What are some fascinating facts about ocean life?'")
        print("  • 'Tell me about space exploration and our solar system'")
        print("  • 'How do animals adapt to their environments?'")
        print("  • 'What are the fundamental forces of nature?'")
        print("  • 'Explain how photosynthesis works in plants'")
        print()
        print("💬 Commands:")
        print("  • Type 'quit', 'exit', or 'bye' to end the conversation")
        print("  • Type 'help' to see this message again")
        print("  • Type 'clear' to clear conversation history")
        print("  • Type 'stats' to show session statistics")
        print("  • Type 'topics' to see available knowledge topics")
        print("  • Type 'examples' to see example questions")
        print("  • Type 'search <query>' to search knowledge base directly")
        print("  • Type 'context' to see current retrieved context")
        print("  • Type 'history' to show conversation history")
        print("  • Type 'add-knowledge' to get instructions for adding custom topics")
        print("=" * 60)
        print()
    
    def display_stats(self):
        """Display conversation statistics."""
        num_exchanges = len(self.conversation_history) // 2
        context_items = len(self.current_context)
        
        print(f"\n📊 Session Stats:")
        print(f"  💬 Exchanges: {num_exchanges}")
        print(f"  🧠 Knowledge chunks: {len(self.chunks)}")
        print(f"  🔍 Last context items: {context_items}")
        print(f"  📚 Knowledge documents loaded: {len(self.knowledge_docs)}")
        if hasattr(self, 'vector_memory') and self.vector_memory:
            print(f"  🗂️ Vector memory status: Active")
        print(f"  🔄 Chat session: {'Active' if self.conversation_active else 'Ended'}")
    
    def display_topics(self):
        """Display available knowledge topics."""
        print("\n📚 Available Knowledge Topics:")
        if self.knowledge_docs:
            for doc_name, content in self.knowledge_docs.items():
                # Extract topic from filename
                topic = doc_name.replace('.txt', '').replace('_', ' ').title()
                char_count = len(content)
                print(f"  • {topic} ({char_count:,} characters)")
        else:
            print("  No knowledge documents loaded")
        
        print("\n🎯 You can ask questions about any of these topics!")
    
    def display_examples(self):
        """Display example questions categorized by topic."""
        examples = {
            "🌊 Ocean & Marine Life": [
                "What are some fascinating facts about ocean life?",
                "Tell me about bioluminescence in marine animals",
                "How do coral reefs support biodiversity?"
            ],
            "🚀 Space & Astronomy": [
                "Tell me about space exploration and our solar system",
                "What makes black holes so mysterious?",
                "How do we search for life on other planets?"
            ],
            "🦁 Wildlife & Animals": [
                "How do animals adapt to their environments?",
                "What are some amazing migration patterns?",
                "How do animals communicate with each other?"
            ],
            "⚛️ Physics & Chemistry": [
                "What are the fundamental forces of nature?",
                "How do chemical reactions work?",
                "Explain quantum physics in simple terms"
            ],
            "🌱 Biology & Life Sciences": [
                "Explain how photosynthesis works in plants",
                "How does evolution shape life on Earth?",
                "What makes DNA so important?"
            ]
        }
        
        print("\n🎯 Example Questions by Topic:")
        for topic, questions in examples.items():
            print(f"\n{topic}:")
            for question in questions:
                print(f"  • {question}")
        print("\n💡 Feel free to ask variations or follow-up questions!")
    
    async def direct_search(self, query: str):
        """Perform direct knowledge base search."""
        print(f"\n🔍 Searching knowledge base for: '{query}'")
        
        if not self.retriever:
            print("❌ Retriever not initialized")
            return
        
        try:
            results = await self.retrieve_context(query, max_context=5)
            if results:
                print(f"\n📄 Found {len(results)} relevant results:")
                print("-" * 50)
                for i, result in enumerate(results, 1):
                    preview = result[:200] + "..." if len(result) > 200 else result
                    print(f"\n{i}. {preview}")
                print("-" * 50)
            else:
                print("❌ No results found for your query")
                print("💡 Try different keywords or ask a question instead")
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    def display_context(self):
        """Display current retrieved context."""
        if not self.current_context:
            print("\n📄 No context currently retrieved")
            print("💡 Context is loaded when you ask questions")
            return
        
        print(f"\n📄 Current Context ({len(self.current_context)} items):")
        print("-" * 50)
        for i, context in enumerate(self.current_context, 1):
            preview = context[:150] + "..." if len(context) > 150 else context
            print(f"\n{i}. {preview}")
        print("-" * 50)
    
    def display_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            print("\n💭 No conversation history yet")
            print("💡 Start asking questions to build history")
            return
        
        print(f"\n💭 Conversation History ({len(self.conversation_history)} messages):")
        print("-" * 50)
        
        for i, entry in enumerate(self.conversation_history):
            role_emoji = "👤" if entry["role"] == "user" else "🤖"
            role_name = "You" if entry["role"] == "user" else "Assistant"
            content = entry["content"]
            
            # Truncate long messages for readability
            if len(content) > 100:
                content = content[:100] + "..."
            
            print(f"\n{i+1}. {role_emoji} {role_name}: {content}")
        
        print("-" * 50)
        print(f"💡 Showing last {len(self.conversation_history)} messages")
    
    def show_add_knowledge_instructions(self):
        """Show detailed instructions for adding custom knowledge."""
        custom_knowledge_path = Path.home() / ".agenticflow" / "knowledge"
        
        print("\n📚 HOW TO ADD CUSTOM KNOWLEDGE")
        print("=" * 50)
        
        print(f"\n📁 1. Create the custom knowledge directory:")
        print(f"   mkdir -p {custom_knowledge_path}")
        
        print(f"\n📝 2. Create .txt files with your content:")
        print(f"   # Example: medical knowledge")
        print(f"   echo 'Medical knowledge content...' > {custom_knowledge_path}/medical_guide.txt")
        print(f"   ")
        print(f"   # Example: company knowledge")
        print(f"   echo 'Company policies and procedures...' > {custom_knowledge_path}/company_handbook.txt")
        
        print(f"\n💻 3. Example Python script to create knowledge:")
        print(f"   ```python")
        print(f"   from pathlib import Path")
        print(f"   ")
        print(f"   # Create knowledge directory")
        print(f"   knowledge_dir = Path.home() / '.agenticflow' / 'knowledge'")
        print(f"   knowledge_dir.mkdir(parents=True, exist_ok=True)")
        print(f"   ")
        print(f"   # Add your content")
        print(f"   content = '''Your domain-specific knowledge here...'''")
        print(f"   (knowledge_dir / 'my_topic.txt').write_text(content)")
        print(f"   ```")
        
        print(f"\n🔄 4. Restart the chatbot to load your custom knowledge")
        print(f"   The chatbot will automatically detect and index your files")
        
        print(f"\n🎆 5. Example custom knowledge topics:")
        print(f"   • Technical documentation (APIs, code guides)")
        print(f"   • Business knowledge (policies, procedures)")
        print(f"   • Educational content (courses, textbooks)")
        print(f"   • Research papers and articles")
        print(f"   • Product manuals and guides")
        print(f"   • Legal documents and regulations")
        
        print(f"\n📊 6. Tips for effective knowledge files:")
        print(f"   • Use descriptive filenames (e.g., 'python_best_practices.txt')")
        print(f"   • Keep content well-structured with headers and sections")
        print(f"   • Include examples and specific details")
        print(f"   • Use plain text format for best compatibility")
        print(f"   • Each file can be 1KB to 1MB (optimal: 10-100KB)")
        
        print(f"\n🌟 Once added, you can ask questions about your custom topics!")
        print("=" * 50)
    
    async def interactive_chat(self):
        """Main interactive chat loop."""
        self.display_welcome()
        
        print("🚀 Chatbot ready! Ask me anything...\n")
        
        while self.conversation_active:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    print("\n👋 Thank you for chatting! Have a great day!")
                    self.display_stats()
                    break
                
                elif user_input.lower() == 'help':
                    self.display_welcome()
                    continue
                
                elif user_input.lower() == 'clear':
                    self.conversation_history.clear()
                    self.current_context.clear()  # Also clear current context
                    if self.conversation_memory:
                        await self.conversation_memory.clear()
                    print("🧹 Conversation history and context cleared!")
                    continue
                
                elif user_input.lower() == 'stats':
                    self.display_stats()
                    continue
                
                elif user_input.lower() == 'topics':
                    self.display_topics()
                    continue
                
                elif user_input.lower() == 'examples':
                    self.display_examples()
                    continue
                
                elif user_input.lower() == 'context':
                    self.display_context()
                    continue
                
                elif user_input.lower() == 'history':
                    self.display_history()
                    continue
                
                elif user_input.lower().startswith('search '):
                    search_query = user_input[7:].strip()  # Remove 'search ' prefix
                    if search_query:
                        await self.direct_search(search_query)
                    else:
                        print("❌ Please provide a search query. Example: search ocean life")
                    continue
                
                elif user_input.lower() == 'add-knowledge':
                    self.show_add_knowledge_instructions()
                    continue
                
                # Generate and display response
                response = await self.get_response(user_input)
                
                print(f"\n🤖 Assistant: {response}\n")
                print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                self.display_stats()
                break
            except EOFError:
                print("\n\n👋 Chat ended. Goodbye!")
                self.display_stats()
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Let's try again...\n")
    
    async def initialize_chatbot(self) -> None:
        """Initialize the complete chatbot system."""
        print("🚀 Initializing Interactive Science & Nature Chatbot")
        print("=" * 55)
        
        try:
            await self.setup_embeddings()
            await self.load_knowledge_base()
            await self.setup_memories()
            await self.index_knowledge_base()
            await self.setup_retriever()
            await self.setup_chatbot_agent()
            
            print("\n✅ Chatbot initialization complete!")
            
        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            print("Please check your setup and try again.")
            sys.exit(1)
    
    async def run_chatbot(self) -> None:
        """Main function to run the interactive chatbot."""
        try:
            await self.initialize_chatbot()
            await self.interactive_chat()
        except Exception as e:
            print(f"❌ Chatbot failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main function to start the chatbot."""
    chatbot = InteractiveRAGChatbot()
    await chatbot.run_chatbot()

if __name__ == "__main__":
    print("🔬 Interactive Science & Nature Chatbot")
    print("This chatbot provides interactive conversations about science, nature, and space")
    print()
    print("Setup Requirements:")
    print("  🔹 For embeddings: OPENAI_API_KEY or Ollama with 'nomic-embed-text'")
    print("  🔹 For chat: GROQ_API_KEY, OPENAI_API_KEY, or Ollama with 'llama3.2'")
    print("  🔹 No API keys needed if using Ollama for everything")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start chatbot: {e}")