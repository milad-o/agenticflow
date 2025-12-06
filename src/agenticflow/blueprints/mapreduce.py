"""
MapReduce Blueprint.

Process large documents by splitting into chunks, processing each,
and aggregating results.

Example:
    ```python
    from agenticflow.blueprints import MapReduce

    map_reduce = MapReduce(
        model=model,
        map_prompt="Extract key points from this text:\n\n{chunk}",
        reduce_prompt="Synthesize these key points into a summary:\n\n{results}",
    )

    result = await map_reduce.run(huge_document)
    print(result)
    ```

Usage in Flow:
    ```python
    flow = Flow(
        agents=[map_reduce, writer],
        topology="pipeline",
    )
    ```
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agenticflow.agent import Agent
from agenticflow.blueprints.base import BaseBlueprint, BlueprintResult
from agenticflow.blueprints.context import BlueprintContext

if TYPE_CHECKING:
    from agenticflow.models import BaseChatModel


@dataclass(frozen=True, slots=True, kw_only=True)
class MapReduceConfig:
    """Configuration for MapReduce blueprint.

    Attributes:
        chunk_size: Size of each chunk in characters.
        chunk_overlap: Overlap between chunks in characters.
        max_parallel: Maximum chunks to process in parallel (0 = all).
        include_chunk_metadata: Include chunk index in results.
    """

    chunk_size: int = 2000
    chunk_overlap: int = 200
    max_parallel: int = 0  # 0 = unlimited
    include_chunk_metadata: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class MapReduceResult(BlueprintResult):
    """Result from MapReduce blueprint execution.

    Attributes:
        output: Final synthesized output.
        chunk_results: Individual chunk results.
        num_chunks: Number of chunks processed.
        document_length: Original document length.
    """

    chunk_results: tuple[str, ...] = ()
    num_chunks: int = 0
    document_length: int = 0


class MapReduce(BaseBlueprint):
    """MapReduce blueprint for processing large documents.

    Splits documents into chunks, processes each with a "map" prompt,
    then aggregates results with a "reduce" prompt.

    Flow-compatible: can be used as a resident in Flow topologies.
    Tool-compatible: can be converted to tool via `as_tool()`.

    Example - Summarization:
        ```python
        map_reduce = MapReduce(
            model=model,
            map_prompt="Extract key points:\n\n{chunk}",
            reduce_prompt="Synthesize into summary:\n\n{results}",
        )
        summary = await map_reduce.run(long_document)
        ```

    Example - Entity Extraction:
        ```python
        map_reduce = MapReduce(
            model=model,
            map_prompt="Extract all person names from:\n\n{chunk}",
            reduce_prompt="Deduplicate and list all names:\n\n{results}",
        )
        names = await map_reduce.run(document)
        ```

    Example - Custom Config:
        ```python
        map_reduce = MapReduce(
            model=model,
            map_prompt="Analyze:\n\n{chunk}",
            reduce_prompt="Combine:\n\n{results}",
            config=MapReduceConfig(
                chunk_size=4000,
                chunk_overlap=400,
                max_parallel=5,  # Limit concurrent API calls
            ),
        )
        ```
    """

    DEFAULT_MAP_PROMPT = """Analyze the following text and extract the key information:

{chunk}

Provide a concise summary of the main points."""

    DEFAULT_REDUCE_PROMPT = """You have been given summaries from different sections of a document.
Synthesize these into a coherent final summary:

{results}

Provide a unified summary that captures all the key information."""

    def __init__(
        self,
        model: BaseChatModel,
        *,
        map_prompt: str | None = None,
        reduce_prompt: str | None = None,
        config: MapReduceConfig | None = None,
    ) -> None:
        """Create MapReduce blueprint.

        Args:
            model: LLM model for processing.
            map_prompt: Prompt template for processing each chunk.
                        Must contain {chunk} placeholder.
            reduce_prompt: Prompt template for aggregating results.
                           Must contain {results} placeholder.
            config: MapReduce configuration options.

        Example:
            ```python
            map_reduce = MapReduce(
                model=model,
                map_prompt="Summarize:\n\n{chunk}",
                reduce_prompt="Combine summaries:\n\n{results}",
            )
            ```
        """
        super().__init__()

        self._model = model
        self._map_prompt = map_prompt or self.DEFAULT_MAP_PROMPT
        self._reduce_prompt = reduce_prompt or self.DEFAULT_REDUCE_PROMPT
        self._config = config or MapReduceConfig()

        # Validate prompts
        if "{chunk}" not in self._map_prompt:
            raise ValueError("map_prompt must contain {chunk} placeholder")
        if "{results}" not in self._reduce_prompt:
            raise ValueError("reduce_prompt must contain {results} placeholder")

        # Create internal agent for LLM calls
        self._agent = Agent(
            name="mapreduce-agent",
            model=model,
            instructions="You are a helpful assistant that processes text accurately.",
        )

    @property
    def name(self) -> str:
        return "mapreduce"

    @property
    def config(self) -> MapReduceConfig:
        """Current configuration."""
        return self._config

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into overlapping chunks.

        Args:
            text: Text to split.

        Returns:
            List of text chunks.
        """
        cfg = self._config
        chunks = []
        start = 0

        while start < len(text):
            end = start + cfg.chunk_size

            # Find a good break point (sentence end, paragraph, etc.)
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + cfg.chunk_size // 2:
                    end = para_break + 2
                else:
                    # Look for sentence end
                    for sep in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                        sent_break = text.rfind(sep, start, end)
                        if sent_break > start + cfg.chunk_size // 2:
                            end = sent_break + len(sep)
                            break

            chunks.append(text[start:end].strip())
            start = end - cfg.chunk_overlap

            # Avoid tiny last chunk
            if len(text) - start < cfg.chunk_size // 4:
                if chunks:
                    chunks[-1] = text[start - cfg.chunk_overlap + cfg.chunk_size :].strip()
                break

        return [c for c in chunks if c]  # Filter empty chunks

    async def _process_chunk(
        self,
        chunk: str,
        index: int,
    ) -> str:
        """Process a single chunk with the map prompt.

        Args:
            chunk: Text chunk to process.
            index: Chunk index (for metadata).

        Returns:
            Processed result for this chunk.
        """
        prompt = self._map_prompt.format(chunk=chunk)
        result = await self._agent.run(prompt)

        if self._config.include_chunk_metadata:
            return f"[Chunk {index + 1}]\n{result}"
        return result

    async def _aggregate_results(self, results: list[str]) -> str:
        """Aggregate chunk results with the reduce prompt.

        Args:
            results: List of chunk processing results.

        Returns:
            Final aggregated output.
        """
        combined = "\n\n---\n\n".join(results)
        prompt = self._reduce_prompt.format(results=combined)
        return await self._agent.run(prompt)

    async def run(self, input: str, **kwargs: Any) -> str:
        """Execute MapReduce and return final output (Flow-compatible).

        Args:
            input: The document to process.
            **kwargs: Additional arguments (unused).

        Returns:
            Final synthesized output string.
        """
        result = await self.run_detailed(input, **kwargs)
        return result.output

    async def run_detailed(
        self,
        input: str,
        **kwargs: Any,
    ) -> MapReduceResult:
        """Execute MapReduce with full metadata.

        Args:
            input: The document to process.
            **kwargs: Additional arguments (unused).

        Returns:
            MapReduceResult with output and chunk details.
        """
        # Pre-processing: split into chunks
        chunks = self._split_into_chunks(input)

        if not chunks:
            return MapReduceResult(
                output="No content to process.",
                chunk_results=(),
                num_chunks=0,
                document_length=len(input),
            )

        # Map phase: process each chunk
        cfg = self._config
        if cfg.max_parallel > 0:
            # Process in batches
            chunk_results = []
            for i in range(0, len(chunks), cfg.max_parallel):
                batch = chunks[i : i + cfg.max_parallel]
                batch_tasks = [
                    self._process_chunk(chunk, i + j)
                    for j, chunk in enumerate(batch)
                ]
                batch_results = await asyncio.gather(*batch_tasks)
                chunk_results.extend(batch_results)
        else:
            # Process all in parallel
            tasks = [
                self._process_chunk(chunk, i)
                for i, chunk in enumerate(chunks)
            ]
            chunk_results = await asyncio.gather(*tasks)

        # Reduce phase: aggregate results
        if len(chunk_results) == 1:
            # Single chunk, no need to reduce
            final_output = chunk_results[0]
            if self._config.include_chunk_metadata:
                # Remove chunk metadata for single chunk
                final_output = final_output.replace("[Chunk 1]\n", "")
        else:
            final_output = await self._aggregate_results(list(chunk_results))

        return MapReduceResult(
            output=final_output,
            chunk_results=tuple(chunk_results),
            num_chunks=len(chunks),
            document_length=len(input),
            metadata={
                "chunk_size": cfg.chunk_size,
                "chunk_overlap": cfg.chunk_overlap,
            },
        )


__all__ = [
    "MapReduce",
    "MapReduceConfig",
    "MapReduceResult",
]
