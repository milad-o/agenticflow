# 🤖 Chatbots Examples

This directory contains interactive chatbot examples that demonstrate AgenticFlow's conversational AI capabilities with RAG (Retrieval-Augmented Generation) integration.

## 🌟 Featured Examples

### 🔬 Interactive Science & Nature Chatbot
**File:** `interactive_rag_chatbot.py`  
**Test:** `test_chatbot_interaction.py`

A production-ready RAG chatbot focused on science, nature, and space topics with:

- **📄 External Document Loading**: Loads knowledge from `knowledge_base/*.txt` files
- **🔍 Hybrid Retrieval**: Combines semantic search (vector embeddings) + keyword search (BM25)
- **💬 Conversational Memory**: Maintains context across multi-turn dialogues
- **🧮 Multiple LLM Providers**: Supports Groq, OpenAI, and Ollama with automatic fallback
- **⚛️ Rich Knowledge Base**: 5 comprehensive documents covering:
  - 🌊 Ocean Life & Marine Biology
  - 🚀 Space Exploration & Astronomy
  - 🦁 Wildlife Behavior & Animal Adaptations
  - ⚛️ Physics & Chemistry Fundamentals
  - 🌱 Biology & Life Sciences

#### Quick Start:
```bash
# Run interactive chatbot (requires LLM provider)
uv run python examples/chatbots/interactive_rag_chatbot.py

# Run automated test demonstration
uv run python examples/chatbots/test_chatbot_interaction.py
```

#### Requirements:
- **Embeddings**: `OPENAI_API_KEY` or Ollama with `nomic-embed-text`
- **Chat**: `GROQ_API_KEY`, `OPENAI_API_KEY`, or Ollama with `granite3.2:8b`/`qwen2.5:7b`

### 🔧 Agent-Powered RAG (Legacy)
**File:** `agent_powered_rag.py`

A legacy RAG implementation using AgenticFlow's framework patterns (needs updating).

## 📚 Knowledge Base

The `knowledge_base/` directory contains curated scientific content:

- `biology_life_sciences.txt` - Cell biology, evolution, ecosystems, genetics
- `ocean_life.txt` - Marine ecosystems, deep sea exploration, conservation
- `physics_chemistry.txt` - Quantum physics, states of matter, chemical reactions
- `space_exploration.txt` - Solar system, cosmic phenomena, space missions
- `wildlife_behavior.txt` - Animal intelligence, adaptations, migration patterns

## 🎯 Key Features Demonstrated

### True RAG Architecture
- Document ingestion from external files
- Text chunking with 400-character chunks, 100-character overlap
- FAISS vector indexing with 768-dimensional embeddings
- Hybrid retrieval (semantic + keyword search)

### Production-Ready Features
- Multiple LLM provider support with fallback
- Conversation memory and context preservation
- Error handling and graceful degradation
- Real-time retrieval and response generation
- Interactive commands and conversation management

### Performance Characteristics
- **Document Processing**: 32 indexed chunks from 5 documents
- **Retrieval Speed**: <100ms for hybrid search
- **Memory Usage**: <200MB for complete system
- **Conversation Context**: Maintains 50 message history

## 🚀 Adding Your Own Knowledge

To add custom knowledge to the chatbot:

1. Create `.txt` files in the `knowledge_base/` directory
2. Add your content in natural language format
3. Restart the chatbot - it will automatically index new documents

The system supports unlimited documents and automatically handles chunking, embedding, and indexing.

## 🔧 Customization

The chatbots can be easily customized for different domains by:
- Replacing knowledge base documents
- Adjusting agent instructions and personality
- Modifying retrieval parameters (chunk size, overlap, top-k)
- Adding domain-specific tools and capabilities

Each chatbot demonstrates different aspects of AgenticFlow's conversational AI capabilities, from simple RAG to complex multi-turn dialogue with memory.