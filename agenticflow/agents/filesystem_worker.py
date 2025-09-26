"""
FileSystem Worker Agent

Specialized worker for file operations with direct tool assignment.
"""
import os
from typing import Any, List, Dict
from pathlib import Path


class FileSystemWorker:
    """Specialized worker for filesystem operations."""

    def __init__(self, search_root: str = ".", file_patterns: List[str] = None):
        self.search_root = search_root
        self.file_patterns = file_patterns or ["*.csv", "*.txt", "*.md"]
        self.capabilities = ["file_operations", "data_discovery", "file_reading"]

    async def arun(self, task: str) -> Dict[str, Any]:
        """Execute filesystem task."""
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute filesystem operations based on task."""

        task_lower = task.lower()

        if "find" in task_lower or "search" in task_lower:
            return self._find_files(task)
        elif "read" in task_lower:
            return self._read_files(task)
        elif "list" in task_lower:
            return self._list_directory(task)
        elif "analyze" in task_lower:
            return self._analyze_files(task)
        else:
            return self._general_file_operation(task)

    def _find_files(self, task: str) -> Dict[str, Any]:
        """Find files matching patterns."""
        root_path = Path(self.search_root)

        if not root_path.exists():
            return {
                "error": f"Search root {self.search_root} does not exist",
                "files": []
            }

        found_files = []
        for pattern in self.file_patterns:
            files = list(root_path.glob(f"**/{pattern}"))
            for file in files:
                if file.is_file():
                    found_files.append({
                        "path": str(file),
                        "name": file.name,
                        "size": file.stat().st_size,
                        "extension": file.suffix
                    })

        return {
            "action": "find_files",
            "search_root": self.search_root,
            "patterns": self.file_patterns,
            "files": found_files,
            "count": len(found_files)
        }

    def _read_files(self, task: str) -> Dict[str, Any]:
        """Read file contents."""
        # First find files, then read them
        find_result = self._find_files(task)

        if find_result.get("error"):
            return find_result

        files_content = []
        for file_info in find_result["files"][:5]:  # Limit to 5 files
            try:
                file_path = Path(file_info["path"])
                if file_path.suffix in ['.txt', '.md', '.csv']:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    files_content.append({
                        "path": file_info["path"],
                        "name": file_info["name"],
                        "content": content[:1000],  # First 1000 chars
                        "full_length": len(content)
                    })
            except Exception as e:
                files_content.append({
                    "path": file_info["path"],
                    "error": str(e)
                })

        return {
            "action": "read_files",
            "files_read": len(files_content),
            "content": files_content
        }

    def _list_directory(self, task: str) -> Dict[str, Any]:
        """List directory contents."""
        root_path = Path(self.search_root)

        if not root_path.exists():
            return {"error": f"Directory {self.search_root} does not exist"}

        items = []
        for item in root_path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })

        return {
            "action": "list_directory",
            "directory": self.search_root,
            "items": items,
            "count": len(items)
        }

    def _analyze_files(self, task: str) -> Dict[str, Any]:
        """Analyze file structure and content."""
        find_result = self._find_files(task)

        if find_result.get("error"):
            return find_result

        analysis = {
            "total_files": find_result["count"],
            "file_types": {},
            "total_size": 0,
            "sample_content": []
        }

        for file_info in find_result["files"]:
            ext = file_info["extension"] or "no_extension"
            analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
            analysis["total_size"] += file_info["size"]

        # Sample some file content
        read_result = self._read_files(task)
        if "content" in read_result:
            analysis["sample_content"] = read_result["content"][:3]

        return {
            "action": "analyze_files",
            "analysis": analysis
        }

    def _general_file_operation(self, task: str) -> Dict[str, Any]:
        """Handle general file operations."""
        return {
            "action": "general_operation",
            "message": f"FileSystemWorker processing: {task}",
            "capabilities": self.capabilities
        }