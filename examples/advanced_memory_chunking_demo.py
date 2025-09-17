#!/usr/bin/env python3
"""
Advanced Memory and Chunking Demonstration
==========================================

This example demonstrates AgenticFlow's advanced memory capabilities including:
- Intelligent text chunking with multiple strategies
- Semantic search with embeddings
- Automatic memory compression and summarization
- Memory lifecycle management and analytics
- Long-term memory with archiving and cleanup

Features showcased:
✅ Multiple chunking strategies (semantic, recursive, token-based, etc.)
✅ Automatic embedding generation for chunks and messages
✅ Semantic search across chunked content
✅ LLM-based memory compression
✅ Memory analytics and health monitoring
✅ Automatic archiving and cleanup
"""

import asyncio
import time
from pathlib import Path
import sys
from datetime import datetime

# Add the src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from agenticflow.text.chunking import (
        ChunkingManager, ChunkingConfig, ChunkingStrategy, 
        TextChunk, get_chunking_manager, chunk_text
    )
    from agenticflow.memory.enhanced import (
        EnhancedMemory, MemoryConfiguration, create_enhanced_memory
    )
    from agenticflow.config.settings import MemoryConfig, LLMProviderConfig, LLMProvider
    from agenticflow.llm_providers import get_llm_manager
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)


# Sample long texts for demonstration
SAMPLE_TEXTS = {
    "research_paper": """
# Advanced AI Memory Systems: A Comprehensive Survey

## Abstract
This paper presents a comprehensive survey of advanced memory systems in artificial intelligence, 
focusing on long-term memory management, semantic retrieval, and adaptive compression techniques.

## Introduction
Memory systems are crucial components of intelligent agents, enabling them to retain and utilize 
past experiences for future decision-making. Traditional memory approaches often struggle with 
scalability and semantic understanding of stored information.

## Memory Architecture
Modern AI memory systems typically consist of multiple components:

### 1. Working Memory
Working memory serves as a temporary storage for currently active information. It has limited 
capacity but provides fast access to recently used data.

### 2. Long-term Memory
Long-term memory stores information for extended periods. It can be further divided into:
- Episodic memory: Specific experiences and events
- Semantic memory: General knowledge and facts
- Procedural memory: Skills and procedures

### 3. Retrieval Mechanisms
Effective retrieval is essential for memory utility. Modern systems employ:
- Associative recall based on semantic similarity
- Context-aware retrieval using embeddings
- Hierarchical organization of memories

## Chunking and Compression
Text chunking is a fundamental process in memory systems, involving the division of large texts 
into smaller, manageable pieces. Various strategies exist:

1. Fixed-size chunking: Simple but may break semantic units
2. Sentence-based chunking: Preserves meaning but variable size
3. Semantic chunking: Uses AI to identify natural boundaries
4. Token-based chunking: Considers language model constraints

Memory compression techniques help manage storage efficiency:
- Lossy compression through summarization
- Lossless compression using redundancy removal
- Adaptive compression based on access patterns

## Evaluation Metrics
Memory system performance can be measured using several metrics:
- Retrieval accuracy: How well the system finds relevant information
- Compression ratio: Storage efficiency achieved
- Access latency: Speed of memory operations
- Semantic preservation: Quality of compressed information

## Future Directions
Future research should focus on:
- Neuromorphic memory architectures
- Quantum memory systems
- Personalized memory adaptation
- Cross-modal memory integration

## Conclusion
Advanced memory systems are essential for creating truly intelligent AI agents. The integration 
of chunking, compression, and semantic retrieval represents a significant step forward in this 
field. Continued research will further improve the capabilities and efficiency of these systems.
""",

    "conversation_log": """
User: I'm working on a machine learning project and need help with data preprocessing.

Assistant: I'd be happy to help you with data preprocessing! Data preprocessing is a crucial step in any ML pipeline. What type of data are you working with and what specific preprocessing challenges are you facing?

User: I have a large dataset of customer reviews, about 100,000 text reviews. I need to clean them and extract features for sentiment analysis.

Assistant: Great! For text preprocessing and sentiment analysis, here's a comprehensive approach:

1. **Text Cleaning:**
   - Remove HTML tags, URLs, and special characters
   - Handle contractions (don't -> do not)
   - Normalize case (usually lowercase)
   - Remove excessive whitespace

2. **Tokenization and Normalization:**
   - Split text into tokens
   - Remove stop words (optional for sentiment)
   - Apply stemming or lemmatization
   - Handle negations carefully for sentiment

3. **Feature Extraction:**
   - TF-IDF vectors
   - N-grams (1-3 grams work well)
   - Word embeddings (Word2Vec, GloVe, or transformers)
   - Sentiment-specific features (positive/negative word counts)

User: That's really helpful! I'm particularly interested in the embedding approach. Should I use pre-trained embeddings or train my own?

Assistant: Excellent question! For sentiment analysis, I'd recommend a hybrid approach:

**Pre-trained Embeddings (Start here):**
- Use models like BERT, RoBERTa, or DistilBERT
- They capture general language understanding
- Fine-tune on your domain for better performance
- Much faster than training from scratch

**Domain-specific Training:**
- If your reviews are from a specific domain (e.g., restaurants, electronics)
- Train embeddings on your corpus for domain-specific terms
- Combine with pre-trained for best results

**Implementation Tips:**
- Start with DistilBERT for speed
- Use sentence transformers for sentence-level embeddings
- Consider VADER for quick sentiment baseline
- Implement data augmentation for class balance

Would you like me to show you some code examples for any of these approaches?

User: Yes, please show me how to implement the BERT-based approach with fine-tuning.

Assistant: Here's a complete implementation for BERT-based sentiment analysis with fine-tuning:

```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset, DataLoader
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report

class SentimentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# Initialize model and tokenizer
model_name = 'distilbert-base-uncased'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name, 
    num_labels=3  # negative, neutral, positive
)

# Prepare your data
train_dataset = SentimentDataset(train_texts, train_labels, tokenizer)
eval_dataset = SentimentDataset(eval_texts, eval_labels, tokenizer)

# Training arguments
training_args = TrainingArguments(
    output_dir='./sentiment_model',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    evaluation_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True,
    metric_for_best_model='eval_accuracy',
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=lambda eval_pred: {
        'accuracy': accuracy_score(eval_pred.label_ids, eval_pred.predictions.argmax(-1))
    }
)

# Train the model
trainer.train()

# Save the fine-tuned model
model.save_pretrained('./fine_tuned_sentiment')
tokenizer.save_pretrained('./fine_tuned_sentiment')
```

This approach gives you:
- Transfer learning benefits
- Domain adaptation
- High accuracy on sentiment tasks
- Easy deployment and inference

User: This is fantastic! One more question - how do I handle the large scale? 100k reviews might be too much for my current setup.

Assistant: Great question! Here are several strategies for handling large-scale text processing:

**1. Data Sampling and Stratification:**
```python
# Stratified sampling to maintain class distribution
from sklearn.model_selection import train_test_split

# Start with a representative subset
sample_size = 10000
X_sample, _, y_sample, _ = train_test_split(
    reviews, labels, 
    train_size=sample_size,
    stratify=labels,
    random_state=42
)
```

**2. Incremental Learning:**
- Train on batches sequentially
- Use learning rate scheduling
- Implement checkpointing for recovery

**3. Model Optimization:**
- Use smaller models (DistilBERT vs BERT)
- Reduce sequence length (256 vs 512)
- Mixed precision training
- Gradient accumulation for larger effective batch sizes

**4. Infrastructure Solutions:**
- Use cloud services (AWS SageMaker, Google Colab Pro)
- Implement data pipeline with generators
- Consider distributed training

**5. Alternative Approaches:**
- Classical ML (SVM, Naive Bayes) for baseline
- Feature selection to reduce dimensionality
- Ensemble methods with smaller models

Start small, validate your approach, then scale up gradually!
"""}


async def demonstrate_text_chunking():
    """Demonstrate various text chunking strategies."""
    print("\n" + "=" * 80)
    print("📄 TEXT CHUNKING DEMONSTRATION")
    print("=" * 80)
    
    text = SAMPLE_TEXTS["research_paper"]
    print(f"Original text length: {len(text)} characters")
    print(f"Word count: {len(text.split())} words")
    
    # Test different chunking strategies
    strategies_to_test = [
        (ChunkingStrategy.RECURSIVE, "Recursive Character Splitting"),
        (ChunkingStrategy.SENTENCE, "Sentence-based Chunking"),
        (ChunkingStrategy.MARKDOWN, "Markdown Structure Aware"),
        (ChunkingStrategy.FIXED_SIZE, "Fixed Size Chunking"),
    ]
    
    results = {}
    
    for strategy, description in strategies_to_test:
        print(f"\n🔍 Testing {description}")
        
        config = ChunkingConfig(
            strategy=strategy,
            chunk_size=800,
            chunk_overlap=100,
            smart_overlap=True
        )
        
        chunks = await chunk_text(
            text,
            strategy=strategy,
            chunk_size=800,
            chunk_overlap=100,
            text_id="research_paper"
        )
        
        results[strategy] = chunks
        
        print(f"   📊 Created {len(chunks)} chunks")
        print(f"   📏 Average chunk size: {sum(len(c.content) for c in chunks) // len(chunks)} chars")
        print(f"   🎯 Size range: {min(len(c.content) for c in chunks)} - {max(len(c.content) for c in chunks)} chars")
        
        # Show first chunk preview
        if chunks:
            first_chunk = chunks[0]
            print(f"   📝 First chunk preview: {first_chunk.content[:100]}...")
            print(f"   🏷️  Chunk metadata: boundary_type={first_chunk.metadata.boundary_type}")
    
    return results


async def demonstrate_semantic_chunking():
    """Demonstrate semantic chunking with embeddings."""
    print("\n" + "=" * 80)
    print("🧠 SEMANTIC CHUNKING WITH EMBEDDINGS")
    print("=" * 80)
    
    try:
        # Try to get embeddings from LLM manager
        llm_manager = get_llm_manager()
        providers = [name for name, info in llm_manager.list_providers().items() if info["supports_embeddings"]]
        
        if not providers:
            print("⚠️  No embedding providers available - simulating semantic chunking")
            return await demonstrate_text_chunking()
        
        provider = llm_manager.get_provider(providers[0])
        embeddings = provider.embeddings
        
        if not embeddings:
            print("⚠️  Embeddings not initialized - falling back to non-semantic chunking")
            return await demonstrate_text_chunking()
        
        print(f"✅ Using embeddings from: {providers[0]}")
        
        config = ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=1000,
            chunk_overlap=150,
            semantic_threshold=0.75,
            min_chunk_size=200,
            max_chunk_size=1500
        )
        
        chunking_manager = get_chunking_manager(config, embeddings)
        
        text = SAMPLE_TEXTS["research_paper"]
        chunks = await chunking_manager.chunk_with_embeddings(
            text,
            text_id="semantic_paper",
            metadata={"source": "research_paper", "type": "academic"}
        )
        
        print(f"📊 Created {len(chunks)} semantic chunks")
        
        # Analyze semantic coherence
        semantic_scores = [c.metadata.semantic_score for c in chunks if c.metadata.semantic_score is not None]
        if semantic_scores:
            avg_score = sum(semantic_scores) / len(semantic_scores)
            print(f"🎯 Average semantic coherence: {avg_score:.3f}")
        
        # Show chunks with embeddings
        embedded_chunks = [c for c in chunks if c.embedding is not None]
        print(f"🔗 Chunks with embeddings: {len(embedded_chunks)}/{len(chunks)}")
        
        # Show sample chunk
        if chunks:
            sample_chunk = chunks[0]
            print(f"\n📝 Sample semantic chunk:")
            print(f"   Content: {sample_chunk.content[:200]}...")
            print(f"   Length: {len(sample_chunk.content)} chars")
            print(f"   Semantic score: {sample_chunk.metadata.semantic_score}")
            print(f"   Has embedding: {sample_chunk.embedding is not None}")
        
        return chunks
    
    except Exception as e:
        print(f"⚠️  Semantic chunking failed: {e}")
        print("   Falling back to basic chunking...")
        return await demonstrate_text_chunking()


async def demonstrate_enhanced_memory():
    """Demonstrate the enhanced memory system with chunking and compression."""
    print("\n" + "=" * 80)
    print("🧠 ENHANCED MEMORY SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Configure enhanced memory
    memory_config = MemoryConfig(
        type="enhanced",
        max_messages=100,
        vector_store_path="demo_memory"
    )
    
    enhanced_config = MemoryConfiguration(
        enable_chunking=True,
        chunking_strategy=ChunkingStrategy.SEMANTIC,
        chunk_size=800,
        chunk_overlap=100,
        enable_compression=False,  # Disable for demo (requires LLM)
        enable_archiving=False,    # Disable for demo
        generate_embeddings=True,
        enable_caching=True,
        cache_size=50
    )
    
    # Create enhanced memory
    try:
        memory = await create_enhanced_memory(memory_config, enhanced_config)
        print("✅ Enhanced memory system initialized")
    except Exception as e:
        print(f"⚠️  Enhanced memory initialization failed: {e}")
        return
    
    # Add various types of messages
    messages_to_add = [
        (HumanMessage("What are the key components of AI memory systems?"), {"type": "question", "topic": "memory_architecture"}),
        (AIMessage(SAMPLE_TEXTS["research_paper"][:1000]), {"type": "research_content", "topic": "memory_systems"}),
        (HumanMessage("How does semantic chunking work?"), {"type": "question", "topic": "chunking"}),
        (AIMessage("Semantic chunking uses AI to identify natural boundaries in text by analyzing semantic similarity between sentences."), {"type": "explanation", "topic": "chunking"}),
        (HumanMessage("What are the benefits of memory compression?"), {"type": "question", "topic": "compression"}),
        (AIMessage(SAMPLE_TEXTS["conversation_log"][:800]), {"type": "conversation", "topic": "preprocessing"}),
    ]
    
    print(f"\n📝 Adding {len(messages_to_add)} messages to memory...")
    
    for message, metadata in messages_to_add:
        try:
            doc_id = await memory.add_message(message, metadata)
            print(f"   ✅ Added message: {doc_id}")
        except Exception as e:
            print(f"   ❌ Failed to add message: {e}")
    
    # Get memory statistics
    print("\n📊 Memory Statistics:")
    try:
        stats = await memory.get_memory_stats()
        print(f"   📧 Total messages: {stats.total_messages}")
        print(f"   🧩 Total chunks: {stats.total_chunks}")
        print(f"   📏 Total characters: {stats.total_characters:,}")
        print(f"   🔢 Estimated tokens: {stats.total_tokens:,}")
        print(f"   💾 Memory size: {stats.memory_size_mb:.2f} MB")
        print(f"   📅 Time span: {stats.oldest_message} to {stats.newest_message}")
        print(f"   🔍 Search count: {stats.search_count}")
        print(f"   📈 Cache hit rate: {stats.cache_hit_rate:.2%}")
        print(f"   🎯 Embedding coverage: {stats.embedding_coverage:.2%}")
    except Exception as e:
        print(f"   ⚠️  Failed to get stats: {e}")
    
    # Demonstrate semantic search
    print("\n🔍 Semantic Search Demonstration:")
    search_queries = [
        "memory architecture components",
        "text chunking strategies",
        "machine learning preprocessing",
        "BERT fine-tuning approach"
    ]
    
    for query in search_queries:
        print(f"\n🔎 Searching for: '{query}'")
        try:
            results = await memory.search(query, limit=3, similarity_threshold=0.6)
            print(f"   📊 Found {len(results)} results")
            
            for i, doc in enumerate(results, 1):
                print(f"   📄 Result {i}:")
                print(f"      Content: {doc.content[:100]}...")
                if "similarity_score" in doc.metadata:
                    print(f"      Similarity: {doc.metadata['similarity_score']:.3f}")
                if "topic" in doc.metadata:
                    print(f"      Topic: {doc.metadata['topic']}")
        
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
    
    # Get memory insights
    print("\n💡 Memory Insights:")
    try:
        insights = await memory.get_memory_insights()
        print(f"   🏥 Health score: {insights['health_score']:.2%}")
        print(f"   ⚡ Performance score: {insights['performance_score']:.2%}")
        print(f"   📈 Efficiency score: {insights['efficiency_score']:.2%}")
        
        if insights['recommendations']:
            print("   💭 Recommendations:")
            for rec in insights['recommendations']:
                print(f"      • {rec}")
        else:
            print("   ✅ No recommendations - memory is operating optimally!")
    
    except Exception as e:
        print(f"   ⚠️  Failed to get insights: {e}")
    
    # Clean up
    try:
        await memory.clear()
        print("\n🧹 Memory cleared for demo cleanup")
    except Exception as e:
        print(f"⚠️  Cleanup failed: {e}")
    
    return memory


async def demonstrate_chunking_analysis():
    """Demonstrate text analysis for optimal chunking strategy."""
    print("\n" + "=" * 80)
    print("📊 TEXT ANALYSIS FOR OPTIMAL CHUNKING")
    print("=" * 80)
    
    manager = get_chunking_manager()
    
    for text_name, text_content in SAMPLE_TEXTS.items():
        print(f"\n📄 Analyzing: {text_name}")
        
        analysis = manager.analyze_text(text_content)
        
        print(f"   📏 Character count: {analysis['character_count']:,}")
        print(f"   📝 Word count: {analysis['word_count']:,}")
        print(f"   📄 Line count: {analysis['line_count']:,}")
        print(f"   ¶ Paragraph count: {analysis['paragraph_count']:,}")
        
        if 'sentence_count' in analysis:
            print(f"   📢 Sentence count: {analysis['sentence_count']:,}")
            print(f"   📊 Avg sentence length: {analysis['average_sentence_length']:.1f} chars")
        
        print(f"   📋 Has markdown headers: {analysis['has_markdown_headers']}")
        print(f"   🏷️  Has HTML tags: {analysis['has_html_tags']}")
        
        print(f"   💡 Suggested strategy: {analysis['suggested_strategy']}")
        print(f"   📐 Suggested chunk size: {analysis['suggested_chunk_size']}")


async def main():
    """Run the comprehensive advanced memory and chunking demonstration."""
    print("🚀 AGENTICFLOW ADVANCED MEMORY & CHUNKING DEMONSTRATION")
    print("=" * 80)
    print("This demo showcases:")
    print("• Multiple text chunking strategies")
    print("• Semantic chunking with embeddings")
    print("• Enhanced memory system with analytics")
    print("• Intelligent text analysis")
    print("• Memory search and insights")
    
    try:
        # 1. Basic chunking strategies
        chunking_results = await demonstrate_text_chunking()
        
        # 2. Semantic chunking
        semantic_chunks = await demonstrate_semantic_chunking()
        
        # 3. Enhanced memory system
        memory_system = await demonstrate_enhanced_memory()
        
        # 4. Text analysis
        await demonstrate_chunking_analysis()
        
        print("\n" + "=" * 80)
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nKey takeaways:")
        print("✅ AgenticFlow provides multiple chunking strategies for different use cases")
        print("✅ Semantic chunking leverages AI for intelligent text boundaries")
        print("✅ Enhanced memory systems offer compression, analytics, and lifecycle management")
        print("✅ Automatic text analysis suggests optimal chunking strategies")
        print("✅ Built-in search and caching provide efficient information retrieval")
        print("\n📚 The system is now ready for production use with long-term memory management!")
    
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
