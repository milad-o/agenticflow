"""Advanced tools for processing massive directories safely and efficiently.

These tools handle scenarios where a huge directory might crash the flow:
- Progressive directory scanning with limits and batching
- Memory-efficient file processing with streaming  
- Vector indexing of directory contents
- Knowledge graph extraction from file relationships
- Crash recovery and partial progress checkpointing
"""
from __future__ import annotations

import os
import json
import hashlib
import tempfile
from typing import Any, Dict, List, Optional, Iterator, Set
from dataclasses import dataclass
from pathlib import Path
from langchain_core.tools import BaseTool
from langchain_core.documents import Document
import time


@dataclass
class DirectoryBatch:
    """A batch of files/directories for processing."""
    paths: List[str]
    total_size: int
    batch_id: str
    parent_dir: str


@dataclass 
class ProcessingProgress:
    """Progress tracking for massive directory operations."""
    total_files: int
    processed_files: int
    total_size: int
    processed_size: int
    current_batch: str
    errors: List[str]
    start_time: float
    checkpoints: List[str]


# Shared cache across all massive directory tool instances
_SHARED_PROGRESS_CACHE: Dict[str, ProcessingProgress] = {}
_SHARED_BATCH_CACHE: Dict[str, List[DirectoryBatch]] = {}

class ProgressiveDirectoryScanTool(BaseTool):
    """Progressively scan huge directories with batching and limits."""
    
    name: str = "progressive_dir_scan"
    description: str = (
        "Scan large directories progressively with batching to avoid crashes. "
        "Args: root_path (str), batch_size (int, default=1000), max_files (int, default=10000), "
        "max_depth (int, default=10), extensions (list, optional). "
        "Returns: {'batches': [...], 'progress': {...}, 'checkpoint_id': str}"
    )

    def __init__(self):
        super().__init__()
        self._progress_cache = _SHARED_PROGRESS_CACHE
        self._batch_cache = _SHARED_BATCH_CACHE

    def _run(
        self, 
        root_path: str,
        batch_size: int = 1000,
        max_files: int = 10000, 
        max_depth: int = 10,
        extensions: Optional[List[str]] = None,
        checkpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Progressive directory scanning with crash recovery."""
        
        root = Path(root_path)
        if not root.exists() or not root.is_dir():
            return {"error": f"Directory not found or not accessible: {root_path}"}
        
        # Apply workspace guard if present
        if hasattr(self, '_path_guard') and self._path_guard:
            try:
                self._path_guard.resolve(root_path, "read")
            except Exception as e:
                return {"error": f"Workspace policy violation: {e}"}
        
        # Generate checkpoint ID
        if not checkpoint_id:
            checkpoint_id = hashlib.md5(f"{root_path}_{time.time()}".encode()).hexdigest()[:16]
        
        # Initialize or resume progress
        if checkpoint_id in self._progress_cache:
            progress = self._progress_cache[checkpoint_id]
        else:
            progress = ProcessingProgress(
                total_files=0,
                processed_files=0, 
                total_size=0,
                processed_size=0,
                current_batch="",
                errors=[],
                start_time=time.time(),
                checkpoints=[]
            )
            self._progress_cache[checkpoint_id] = progress
        
        try:
            batches = []
            current_batch_paths = []
            current_batch_size = 0
            batch_count = 0
            file_count = 0
            
            # Progressive file discovery with limits
            for file_path in self._safe_walk(root, max_depth, extensions):
                if file_count >= max_files:
                    break
                    
                try:
                    stat = file_path.stat()
                    file_size = stat.st_size
                    
                    current_batch_paths.append(str(file_path))
                    current_batch_size += file_size
                    file_count += 1
                    
                    # Create batch when size limit reached
                    if len(current_batch_paths) >= batch_size:
                        batch = DirectoryBatch(
                            paths=current_batch_paths.copy(),
                            total_size=current_batch_size,
                            batch_id=f"{checkpoint_id}_batch_{batch_count}",
                            parent_dir=str(root)
                        )
                        batches.append(batch)
                        
                        # Reset for next batch
                        current_batch_paths.clear()
                        current_batch_size = 0
                        batch_count += 1
                        
                        # Memory management checkpoint
                        if batch_count % 10 == 0:
                            progress.checkpoints.append(f"batch_{batch_count}")
                        
                except Exception as e:
                    progress.errors.append(f"Error processing {file_path}: {e}")
                    continue
            
            # Handle remaining files
            if current_batch_paths:
                batch = DirectoryBatch(
                    paths=current_batch_paths,
                    total_size=current_batch_size,
                    batch_id=f"{checkpoint_id}_batch_{batch_count}",
                    parent_dir=str(root)
                )
                batches.append(batch)
            
            # Update progress
            progress.total_files = file_count
            progress.total_size = sum(b.total_size for b in batches)
            
            # Cache batches
            self._batch_cache[checkpoint_id] = batches
            
            return {
                "checkpoint_id": checkpoint_id,
                "batches": [
                    {
                        "batch_id": b.batch_id,
                        "file_count": len(b.paths),
                        "total_size": b.total_size,
                        "sample_paths": b.paths[:3]
                    }
                    for b in batches
                ],
                "progress": {
                    "total_files": progress.total_files,
                    "total_batches": len(batches),
                    "total_size_mb": progress.total_size / (1024*1024),
                    "errors": len(progress.errors),
                    "elapsed_time": time.time() - progress.start_time
                }
            }
            
        except Exception as e:
            progress.errors.append(f"Scanning error: {e}")
            return {
                "error": f"Progressive scan failed: {e}",
                "checkpoint_id": checkpoint_id,
                "partial_progress": {
                    "errors": progress.errors,
                    "checkpoints": progress.checkpoints
                }
            }

    def _safe_walk(self, root: Path, max_depth: int, extensions: Optional[List[str]]) -> Iterator[Path]:
        """Memory-efficient directory walking with depth and extension limits."""
        ext_set = set(extensions or [])
        
        def _walk_recursive(path: Path, current_depth: int) -> Iterator[Path]:
            if current_depth > max_depth:
                return
                
            try:
                for entry in path.iterdir():
                    try:
                        if entry.is_file():
                            # Filter by extensions if specified
                            if ext_set and entry.suffix.lower() not in ext_set:
                                continue
                            yield entry
                        elif entry.is_dir() and not entry.name.startswith('.'):
                            # Recursively walk subdirectories
                            yield from _walk_recursive(entry, current_depth + 1)
                    except (PermissionError, OSError):
                        continue  # Skip inaccessible files/dirs
            except (PermissionError, OSError):
                return  # Skip inaccessible directories
        
        return _walk_recursive(root, 0)


class BatchVectorIndexTool(BaseTool):
    """Create vector indexes from directory batches using ephemeral chroma."""
    
    name: str = "batch_vector_index"
    description: str = (
        "Create vector index from a directory batch. "
        "Args: checkpoint_id (str), batch_id (str), chunk_size (int, default=1000), "
        "max_docs (int, default=100). "
        "Returns: {'index_id': str, 'indexed_files': int, 'chunks': int}"
    )

    def __init__(self):
        super().__init__()
        self._progress_cache = _SHARED_PROGRESS_CACHE
        self._batch_cache = _SHARED_BATCH_CACHE
        self._indexes: Dict[str, Any] = {}

    def _run(
        self,
        checkpoint_id: str, 
        batch_id: str,
        chunk_size: int = 1000,
        max_docs: int = 100
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Create vector index from a batch of files."""
        
        try:
            # Import vector tools
            from agenticflow.tools.ephemeral_chroma import BuildEphemeralChromaTool
            
            # Access shared batch cache
            if checkpoint_id not in self._batch_cache:
                return {"error": f"Checkpoint {checkpoint_id} not found. Run progressive_dir_scan first."}
            
            batches = self._batch_cache[checkpoint_id]
            target_batch = None
            for batch in batches:
                if batch.batch_id == batch_id:
                    target_batch = batch
                    break
                    
            if not target_batch:
                return {"error": f"Batch {batch_id} not found in checkpoint {checkpoint_id}"}
            
            # Process files in batch
            documents = []
            processed_files = 0
            
            for file_path in target_batch.paths[:max_docs]:
                try:
                    path = Path(file_path)
                    if path.suffix.lower() in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml']:
                        content = path.read_text(encoding='utf-8', errors='ignore')
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": str(path),
                                "batch_id": batch_id,
                                "file_size": path.stat().st_size,
                                "file_ext": path.suffix
                            }
                        )
                        documents.append(doc)
                        processed_files += 1
                        
                except Exception as e:
                    continue  # Skip problematic files
            
            if not documents:
                return {"error": "No indexable documents found in batch"}
            
            # Create vector index using existing chroma tool
            builder = BuildEphemeralChromaTool()
            
            # Write batch content to temp file for indexing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                for doc in documents:
                    tmp.write(f"=== {doc.metadata['source']} ===\n")
                    tmp.write(doc.page_content)
                    tmp.write("\n\n")
                tmp_path = tmp.name
            
            try:
                result = builder._run(
                    path=tmp_path,
                    index_id=f"{checkpoint_id}_{batch_id}",
                    chunk_size=chunk_size
                )
                
                # Store index reference
                self._indexes[f"{checkpoint_id}_{batch_id}"] = {
                    "builder": builder,
                    "indexed_files": processed_files,
                    "total_chunks": result.get("chunks", 0)
                }
                
                return {
                    "index_id": f"{checkpoint_id}_{batch_id}",
                    "indexed_files": processed_files,
                    "chunks": result.get("chunks", 0),
                    "batch_size_mb": target_batch.total_size / (1024*1024)
                }
                
            finally:
                os.unlink(tmp_path)  # Cleanup temp file
                
        except Exception as e:
            return {"error": f"Vector indexing failed: {e}"}


class FileRelationshipGraphTool(BaseTool):
    """Extract knowledge graph of file relationships from directory structure."""
    
    name: str = "file_relationship_graph" 
    description: str = (
        "Extract file relationships and create knowledge graph. "
        "Args: checkpoint_id (str), analysis_type (str: 'imports'|'references'|'structure'). "
        "Returns: {'nodes': [...], 'edges': [...], 'stats': {...}}"
    )
    
    def __init__(self):
        super().__init__()
        self._progress_cache = _SHARED_PROGRESS_CACHE
        self._batch_cache = _SHARED_BATCH_CACHE

    def _run(
        self,
        checkpoint_id: str,
        analysis_type: str = "structure"
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Extract file relationships into a knowledge graph."""
        
        try:
            # Access shared batch cache
            if checkpoint_id not in self._batch_cache:
                return {"error": f"Checkpoint {checkpoint_id} not found"}
            
            batches = self._batch_cache[checkpoint_id]
            all_files = []
            for batch in batches:
                all_files.extend(batch.paths)
            
            nodes = []
            edges = []
            
            if analysis_type == "structure":
                # Directory structure relationships
                dir_map = {}
                for file_path in all_files:
                    path = Path(file_path)
                    
                    # Add file node
                    nodes.append({
                        "id": str(path),
                        "type": "file",
                        "name": path.name,
                        "extension": path.suffix,
                        "size": path.stat().st_size if path.exists() else 0
                    })
                    
                    # Add directory nodes and edges
                    parent = path.parent
                    if str(parent) not in dir_map:
                        dir_map[str(parent)] = True
                        nodes.append({
                            "id": str(parent),
                            "type": "directory", 
                            "name": parent.name
                        })
                    
                    # Add contains relationship
                    edges.append({
                        "source": str(parent),
                        "target": str(path),
                        "type": "contains"
                    })
            
            elif analysis_type == "imports":
                # Code import relationships (simple heuristic)
                for file_path in all_files[:100]:  # Limit for performance
                    path = Path(file_path)
                    if path.suffix in ['.py', '.js', '.ts']:
                        try:
                            content = path.read_text(encoding='utf-8', errors='ignore')
                            
                            # Extract imports (simple regex)
                            import re
                            if path.suffix == '.py':
                                imports = re.findall(r'import\s+(\w+)|from\s+(\w+)', content)
                                for imp in imports:
                                    module = imp[0] or imp[1]
                                    edges.append({
                                        "source": str(path),
                                        "target": module,
                                        "type": "imports"
                                    })
                                    
                        except Exception:
                            continue
            
            return {
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "analysis_type": analysis_type,
                    "files_analyzed": len(all_files)
                }
            }
            
        except Exception as e:
            return {"error": f"Knowledge graph extraction failed: {e}"}