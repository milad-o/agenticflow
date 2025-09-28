"""Workspace management for shared file operations."""

import asyncio
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import shutil


class Workspace:
    """Shared workspace for all agents to interact with the filesystem."""

    def __init__(self, workspace_path: Union[str, Path], create_if_not_exists: bool = True):
        """Initialize workspace.

        Args:
            workspace_path: Path to the workspace directory
            create_if_not_exists: Whether to create the workspace if it doesn't exist
        """
        self.workspace_path = Path(workspace_path).resolve()
        self._lock = asyncio.Lock()

        if create_if_not_exists:
            self.workspace_path.mkdir(parents=True, exist_ok=True)

    async def write_file(self, file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> str:
        """Write content to a file asynchronously.

        Args:
            file_path: Relative path within workspace
            content: Content to write
            encoding: File encoding

        Returns:
            Absolute path of the written file
        """
        full_path = self._resolve_path(file_path)

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with self._lock:
            async with aiofiles.open(full_path, 'w', encoding=encoding) as f:
                await f.write(content)

        return str(full_path)

    async def read_file(self, file_path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read content from a file asynchronously.

        Args:
            file_path: Relative path within workspace
            encoding: File encoding

        Returns:
            File content
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        async with aiofiles.open(full_path, 'r', encoding=encoding) as f:
            return await f.read()

    async def append_file(self, file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> str:
        """Append content to a file asynchronously.

        Args:
            file_path: Relative path within workspace
            content: Content to append
            encoding: File encoding

        Returns:
            Absolute path of the file
        """
        full_path = self._resolve_path(file_path)

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with self._lock:
            async with aiofiles.open(full_path, 'a', encoding=encoding) as f:
                await f.write(content)

        return str(full_path)

    async def delete_file(self, file_path: Union[str, Path]) -> bool:
        """Delete a file asynchronously.

        Args:
            file_path: Relative path within workspace

        Returns:
            True if file was deleted, False if it didn't exist
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            return False

        async with self._lock:
            await aiofiles.os.remove(full_path)

        return True

    async def list_files(self, directory: Union[str, Path] = ".", pattern: str = "*", recursive: bool = True) -> List[str]:
        """List files in a directory asynchronously.

        Args:
            directory: Relative directory path within workspace
            pattern: Glob pattern for file matching
            recursive: Whether to search recursively

        Returns:
            List of relative file paths
        """
        full_path = self._resolve_path(directory)

        if not full_path.exists():
            return []

        files = []
        glob_pattern = f"**/{pattern}" if recursive else pattern
        for file_path in full_path.glob(glob_pattern):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.workspace_path)
                files.append(str(relative_path))

        return sorted(files)

    async def create_directory(self, directory: Union[str, Path]) -> str:
        """Create a directory asynchronously.

        Args:
            directory: Relative directory path within workspace

        Returns:
            Absolute path of the created directory
        """
        full_path = self._resolve_path(directory)

        async with self._lock:
            await aiofiles.os.makedirs(full_path, exist_ok=True)

        return str(full_path)

    async def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if a file exists.

        Args:
            file_path: Relative path within workspace

        Returns:
            True if file exists
        """
        full_path = self._resolve_path(file_path)
        return full_path.exists()

    async def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get file information.

        Args:
            file_path: Relative path within workspace

        Returns:
            Dictionary with file information
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        stat = full_path.stat()
        return {
            "path": str(file_path),
            "absolute_path": str(full_path),
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "is_file": full_path.is_file(),
            "is_directory": full_path.is_dir(),
        }

    async def write_json(self, file_path: Union[str, Path], data: Any, **kwargs) -> str:
        """Write data as JSON to a file.

        Args:
            file_path: Relative path within workspace
            data: Data to serialize as JSON
            **kwargs: Additional arguments for json.dumps

        Returns:
            Absolute path of the written file
        """
        content = json.dumps(data, indent=2, default=str, **kwargs)
        return await self.write_file(file_path, content)

    async def read_json(self, file_path: Union[str, Path]) -> Any:
        """Read and parse JSON from a file.

        Args:
            file_path: Relative path within workspace

        Returns:
            Parsed JSON data
        """
        content = await self.read_file(file_path)
        return json.loads(content)

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve a relative path within the workspace.

        Args:
            path: Relative path within workspace

        Returns:
            Absolute path within workspace
        """
        relative_path = Path(path)

        # Ensure the path is relative (no absolute paths allowed)
        if relative_path.is_absolute():
            raise ValueError(f"Absolute paths not allowed: {path}")

        # Prevent directory traversal
        full_path = (self.workspace_path / relative_path).resolve()
        if not str(full_path).startswith(str(self.workspace_path)):
            raise ValueError(f"Path outside workspace not allowed: {path}")

        return full_path

    async def copy_file(self, source: Union[str, Path], destination: Union[str, Path]) -> str:
        """Copy a file within the workspace.

        Args:
            source: Source file path (relative to workspace)
            destination: Destination file path (relative to workspace)

        Returns:
            Absolute path of the destination file
        """
        source_path = self._resolve_path(source)
        dest_path = self._resolve_path(destination)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        async with self._lock:
            await asyncio.to_thread(shutil.copy2, source_path, dest_path)

        return str(dest_path)

    async def get_workspace_info(self) -> Dict[str, Any]:
        """Get information about the workspace.

        Returns:
            Dictionary with workspace information
        """
        total_files = 0
        total_size = 0

        for file_path in self.workspace_path.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        return {
            "workspace_path": str(self.workspace_path),
            "total_files": total_files,
            "total_size": total_size,
            "exists": self.workspace_path.exists(),
        }