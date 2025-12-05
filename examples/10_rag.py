"""
Example 10: RAG (Retrieval-Augmented Generation)

RAG is a thin capability that provides search tools to agents.
Document loading/indexing happens OUTSIDE the capability.

Key design principle:
- LLM receives MINIMAL context: just [id] + content
- Citations are mapped DETERMINISTICALLY in post-processing
- No metadata bloat in LLM context (saves tokens)

Two API styles:
- Single retriever: `RAG(retriever)`
- Multiple retrievers: `RAG(retrievers=[...], fusion="rrf")`

Three access levels:
1. **High-level**: agent.run() with RAG capability (agentic RAG)
2. **Mid-level**: rag.search() with citations
3. **Low-level**: retriever.retrieve() raw results

Usage:
    uv run python examples/10_rag.py
"""

import asyncio

from config import get_embeddings, get_model

from agenticflow import Agent
from agenticflow.capabilities import RAG, CitationStyle
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
    # Step 1: Prepare documents (OUTSIDE RAG)
    # =========================================================================
    print("=" * 60)
    print("Step 1: Prepare documents (outside RAG)")
    print("=" * 60)

    # Create document and split into chunks
    doc = Document(text=SAMPLE_TEXT, metadata={"source": "the_secret_garden.txt"})
    splitter = RecursiveCharacterSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents([doc])
    print(f"Created {len(chunks)} chunks")

    # Create vectorstore and index
    store = VectorStore(embeddings=embeddings)
    await store.add_documents(chunks)
    print(f"Indexed {len(chunks)} chunks in vectorstore")

    # =========================================================================
    # Pattern 1: Single Retriever
    # =========================================================================
    print("\n" + "=" * 60)
    print("Pattern 1: Single Retriever")
    print("=" * 60)

    # Create retriever and RAG
    dense = DenseRetriever(store)
    rag = RAG(dense)

    # Add to agent
    agent = Agent(
        name="BookAssistant",
        model=model,
        capabilities=[rag],
    )

    # Agent uses search_documents tool automatically
    answer = await agent.run("What was Mary Lennox like when she arrived?")
    print(f"\n{answer}")

    # =========================================================================
    # Pattern 2: Multiple Retrievers with Fusion
    # =========================================================================
    print("\n" + "=" * 60)
    print("Pattern 2: Multiple Retrievers (RRF fusion)")
    print("=" * 60)

    # Create multiple retrievers
    dense = DenseRetriever(store)
    sparse = BM25Retriever(chunks)

    # RAG creates ensemble internally
    rag2 = RAG(
        retrievers=[dense, sparse],
        weights=[0.6, 0.4],
        fusion="rrf",  # Reciprocal Rank Fusion
    )

    # Search directly
    passages = await rag2.search("Describe the moor", k=3)
    print("Retrieved passages:")
    for p in passages:
        print(f"  {p.format_reference()} {p.source} (score: {p.score:.2f})")
        print(f"    {p.text[:80]}...")

    # =========================================================================
    # Mid-Level API: Citation-Aware Search
    # =========================================================================
    print("\n" + "=" * 60)
    print("Mid-Level API: rag.search() with citations")
    print("=" * 60)

    passages = await rag.search("Describe Martha and the moor", k=3)

    # Different citation styles
    print("\nCitation styles:")
    for style in CitationStyle:
        formatted = passages[0].format_reference(style)
        print(f"  {style.name:12} → {formatted}")

    # Bibliography
    print("\nBibliography:")
    print(rag.format_bibliography(passages))

    # =========================================================================
    # Low-Level API: Direct Retriever Access
    # =========================================================================
    print("\n" + "=" * 60)
    print("Low-Level API: Direct retriever access")
    print("=" * 60)

    # Access underlying retriever
    results = await rag.retriever.retrieve("robin bird", k=2, include_scores=True)
    for i, result in enumerate(results, 1):
        print(f"[{i}] score={result.score:.3f}")
        print(f"    {result.document.text[:80]}...")

    # =========================================================================
    # Fusion Strategies
    # =========================================================================
    print("\n" + "=" * 60)
    print("Fusion Strategies Comparison")
    print("=" * 60)

    query = "yellow hair sour expression"

    for fusion in ["rrf", "linear", "max", "voting"]:
        rag_test = RAG(
            retrievers=[dense, sparse],
            fusion=fusion,
        )
        results = await rag_test.search(query, k=1)
        if results:
            print(f"  {fusion:8} → score={results[0].score:.3f}")

    # =========================================================================
    # Deterministic Citations (LLM sees minimal, we format full)
    # =========================================================================
    print("\n" + "=" * 60)
    print("Deterministic Citations")
    print("=" * 60)

    # The tool sends MINIMAL context to LLM:
    #   [1] Mary had a thin face and thin body...
    #   [2] The moor was a vast stretch of wild land...
    #
    # The LLM just references [1], [2] in its response.
    # We then deterministically map those IDs to full citations.

    # Simulate what the agent flow looks like:
    print("\nWhat LLM receives from search tool:")
    passages = await rag.search("Describe Mary", k=2)
    for p in passages:
        preview = p.text[:60] + "..." if len(p.text) > 60 else p.text
        print(f"  [{p.citation_id}] {preview}")

    print("\nWhat we generate deterministically (post-processing):")
    # Simulate LLM response
    llm_response = "Mary had a thin face [1] and arrived at Misselthwaite Manor [1]."

    # Format with bibliography
    formatted = rag.format_response(llm_response, include_bibliography=True)
    print(formatted)

    print("\nBenefit: LLM context not wasted on metadata!")
    print("  - Source, page, score NOT sent to LLM")
    print("  - Only [id] + content (minimal tokens)")
    print("  - Full citations added deterministically after")

    print("\n✓ Done")


if __name__ == "__main__":
    asyncio.run(main())
