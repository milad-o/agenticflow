"""
Example 10: RAG Blueprint

RAG is a Blueprint - a pre-configured agent workflow that handles
retrieval-augmented generation with automatic citation formatting.

Key design:
- Blueprint uses an internal Agent (leverages our agent system)
- Agent sees collision-resistant markers: «1», «2»
- Post-processing formats citations deterministically
- No citation metadata bloat in LLM context

Usage:
    uv run python examples/10_rag.py
"""

import asyncio

from config import get_embeddings, get_model

from agenticflow.blueprints import RAG, RAGConfig, CitationStyle
from agenticflow.document import RecursiveCharacterSplitter
from agenticflow.retriever import DenseRetriever, BM25Retriever
from agenticflow.vectorstore import VectorStore, Document


# Sample text for demo (The Secret Garden excerpt)
SAMPLE_TEXT = """
The Secret Garden by Frances Hodgson Burnett

Chapter 1: There Is No One Left

When Mary Lennox was sent to Misselthwaite Manor to live with her uncle, 
everybody said she was the most disagreeable-looking child ever seen. 
It was true, too. She had a little thin face and a little thin body, 
thin light hair and a sour expression. Her hair was yellow, and her 
face was yellow because she had been born in India and had always been ill.

Chapter 3: Across the Moor

The moor was a vast stretch of wild land, covered with brown heather 
and gorse bushes. It stretched for miles in every direction. The sky 
seemed so high above, and the air was so fresh and pure.

"It's the moor," said Martha. "It's called the moor. Does tha' like it?"

Mary looked at it and thought she did not like it at all.

Chapter 4: Martha

Martha was a good-natured Yorkshire girl who had been hired to wait on Mary.
She was different from any servant Mary had ever known. She talked and 
laughed and seemed not to know that a servant should be silent.

"Th' fresh air an' th' skippin' rope will make thee strong," Martha said.
"Mother says there's naught like th' moor air."

Chapter 8: The Robin and the Key

One day, Mary was walking along the path by the wall when she heard a 
chirping sound. A robin was sitting on a branch, looking at her with 
his bright eyes. He seemed to be trying to tell her something.
"""


async def main() -> None:
    model = get_model()
    embeddings = get_embeddings()

    # =========================================================================
    # Step 1: Prepare documents (OUTSIDE blueprint)
    # =========================================================================
    print("=" * 60)
    print("Step 1: Prepare documents")
    print("=" * 60)

    doc = Document(text=SAMPLE_TEXT, metadata={"source": "the_secret_garden.txt"})
    splitter = RecursiveCharacterSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents([doc])
    print(f"Created {len(chunks)} chunks")

    store = VectorStore(embeddings=embeddings)
    await store.add_documents(chunks)
    print(f"Indexed {len(chunks)} chunks in vectorstore")

    # =========================================================================
    # Pattern 1: Simple RAG Blueprint
    # =========================================================================
    print("\n" + "=" * 60)
    print("Pattern 1: Simple RAG Blueprint")
    print("=" * 60)

    # Create blueprint with retriever and model
    dense = DenseRetriever(store)
    rag = RAG(retriever=dense, model=model)

    # Query - blueprint handles everything!
    result = await rag.run("What was Mary Lennox like when she arrived?")
    print(f"\n{result.output}")
    print(f"\n[Metadata: {result.metadata}]")

    # =========================================================================
    # Pattern 2: Multiple Retrievers with Fusion
    # =========================================================================
    print("\n" + "=" * 60)
    print("Pattern 2: Multiple Retrievers (RRF fusion)")
    print("=" * 60)

    sparse = BM25Retriever(chunks)

    rag2 = RAG(
        retrievers=[dense, sparse],
        weights=[0.6, 0.4],
        fusion="rrf",
        model=model,
    )

    result = await rag2.run("Describe the moor and Martha")
    print(f"\n{result.output}")

    # =========================================================================
    # Pattern 3: Custom Configuration
    # =========================================================================
    print("\n" + "=" * 60)
    print("Pattern 3: Custom Configuration")
    print("=" * 60)

    config = RAGConfig(
        top_k=3,
        citation_style=CitationStyle.AUTHOR_YEAR,
        include_bibliography=True,
        include_score_in_bibliography=False,
    )

    rag3 = RAG(retriever=dense, model=model, config=config)

    result = await rag3.run("What did Martha say about the moor air?")
    print(f"\n{result.output}")

    # =========================================================================
    # Direct Search (Low-level access)
    # =========================================================================
    print("\n" + "=" * 60)
    print("Direct Search (Low-level access)")
    print("=" * 60)

    passages = await rag.search("robin bird", k=2)
    for p in passages:
        print(f"  «{p.citation_id}» {p.source} (score: {p.score:.2f})")
        print(f"      {p.text[:80]}...")

    # =========================================================================
    # RAGResult Details
    # =========================================================================
    print("\n" + "=" * 60)
    print("RAGResult Details")
    print("=" * 60)

    result = await rag.run("Who is Mary?")

    print(f"Query: {result.query}")
    print(f"Passages used: {len(result.passages)}")
    print(f"\nRaw output (with «» markers):\n{result.raw_output[:200]}...")
    print(f"\nFormatted output:\n{result.output}")

    # =========================================================================
    # Advanced: Pre-configured Agent
    # =========================================================================
    print("\n" + "=" * 60)
    print("Advanced: Pre-configured Agent")
    print("=" * 60)

    from agenticflow import Agent
    from agenticflow.interceptors import BudgetGuard

    # Create agent with full configuration
    advanced_agent = Agent(
        name="research-assistant",
        model=model,
        instructions="You are a meticulous research assistant.",
        intercept=[BudgetGuard(model_calls=5)],
        # Could also add: memory=..., capabilities=..., etc.
    )

    # Pass to blueprint - it adds the search tool
    rag_advanced = RAG(retriever=dense, agent=advanced_agent)

    print("Created RAG with pre-configured agent:")
    print("  - Agent has its own instructions, interceptors, etc.")
    print("  - Blueprint adds search_documents tool")
    print("  - Blueprint handles citation post-processing")

    print("\n✓ Done")


if __name__ == "__main__":
    asyncio.run(main())
