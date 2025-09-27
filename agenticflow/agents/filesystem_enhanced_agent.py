"""
Enhanced FileSystem Agent - Advanced File and Folder Operations
===============================================================

Comprehensive file system operations with security, monitoring, and advanced features.
"""

import os
import shutil
import pathlib
import tempfile
import zipfile
import tarfile
import json
import yaml
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import mimetypes
import subprocess
import fnmatch


class FileSystemEnhancedAgent:
    """Enhanced agent for comprehensive file system operations."""

    def __init__(self, base_path: str = None, safe_mode: bool = True):
        self.capabilities = [
            "file_creation",
            "folder_creation",
            "file_reading",
            "file_writing",
            "file_deletion",
            "folder_operations",
            "file_search",
            "file_monitoring",
            "compression_operations",
            "file_metadata",
            "permissions_management",
            "backup_operations",
            "bulk_operations"
        ]
        self.base_path = base_path or os.getcwd()
        self.safe_mode = safe_mode
        self.operation_history = []

    async def arun(self, task: str) -> Dict[str, Any]:
        """Async execution wrapper."""
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute file system operations."""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ["create folder", "make directory", "mkdir"]):
            return self._create_folder_task(task)
        elif any(keyword in task_lower for keyword in ["create file", "make file", "touch"]):
            return self._create_file_task(task)
        elif any(keyword in task_lower for keyword in ["read file", "show content", "cat"]):
            return self._read_file_task(task)
        elif any(keyword in task_lower for keyword in ["write to", "save to", "write file"]):
            return self._write_file_task(task)
        elif any(keyword in task_lower for keyword in ["delete", "remove", "rm"]):
            return self._delete_task(task)
        elif any(keyword in task_lower for keyword in ["search", "find", "locate"]):
            return self._search_task(task)
        elif any(keyword in task_lower for keyword in ["copy", "cp"]):
            return self._copy_task(task)
        elif any(keyword in task_lower for keyword in ["move", "mv", "rename"]):
            return self._move_task(task)
        elif any(keyword in task_lower for keyword in ["list", "ls", "dir"]):
            return self._list_task(task)
        elif any(keyword in task_lower for keyword in ["compress", "zip", "archive"]):
            return self._compress_task(task)
        elif any(keyword in task_lower for keyword in ["extract", "unzip", "decompress"]):
            return self._extract_task(task)
        elif any(keyword in task_lower for keyword in ["permissions", "chmod", "access"]):
            return self._permissions_task(task)
        elif any(keyword in task_lower for keyword in ["backup", "sync"]):
            return self._backup_task(task)
        elif any(keyword in task_lower for keyword in ["metadata", "info", "stat"]):
            return self._metadata_task(task)
        else:
            return self._general_filesystem_task(task)

    def _create_folder_task(self, task: str) -> Dict[str, Any]:
        """Create folders/directories."""
        folder_paths = self._extract_folder_paths(task)

        if not folder_paths:
            return {
                "action": "folder_creation",
                "success": False,
                "error": "No folder path specified"
            }

        results = []
        for folder_path in folder_paths:
            try:
                full_path = self._get_safe_path(folder_path)

                # Create folder with parents if needed
                os.makedirs(full_path, exist_ok=True)

                results.append({
                    "path": full_path,
                    "success": True,
                    "created": not os.path.exists(full_path)
                })

                self._log_operation("create_folder", full_path, True)

            except Exception as e:
                results.append({
                    "path": folder_path,
                    "success": False,
                    "error": str(e)
                })
                self._log_operation("create_folder", folder_path, False, str(e))

        return {
            "action": "folder_creation",
            "results": results,
            "success": all(r["success"] for r in results)
        }

    def _create_file_task(self, task: str) -> Dict[str, Any]:
        """Create files."""
        file_info = self._extract_file_creation_info(task)

        if not file_info.get("path"):
            return {
                "action": "file_creation",
                "success": False,
                "error": "No file path specified"
            }

        try:
            file_path = self._get_safe_path(file_info["path"])
            content = file_info.get("content", "")

            # Create parent directories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self._log_operation("create_file", file_path, True)

            return {
                "action": "file_creation",
                "success": True,
                "file_path": file_path,
                "content_length": len(content),
                "created": True
            }

        except Exception as e:
            self._log_operation("create_file", file_info["path"], False, str(e))
            return {
                "action": "file_creation",
                "success": False,
                "error": str(e)
            }

    def _read_file_task(self, task: str) -> Dict[str, Any]:
        """Read file contents."""
        file_path = self._extract_file_path(task)

        if not file_path:
            return {
                "action": "file_reading",
                "success": False,
                "error": "No file path specified"
            }

        try:
            full_path = self._get_safe_path(file_path)

            if not os.path.exists(full_path):
                return {
                    "action": "file_reading",
                    "success": False,
                    "error": f"File not found: {full_path}"
                }

            # Detect file type and read accordingly
            mime_type, _ = mimetypes.guess_type(full_path)

            if mime_type and mime_type.startswith('text'):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # Binary file - read as bytes and encode
                with open(full_path, 'rb') as f:
                    content = f.read()
                content = f"<Binary file: {len(content)} bytes>"

            file_stats = os.stat(full_path)

            self._log_operation("read_file", full_path, True)

            return {
                "action": "file_reading",
                "success": True,
                "file_path": full_path,
                "content": content,
                "file_size": file_stats.st_size,
                "mime_type": mime_type,
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            }

        except Exception as e:
            self._log_operation("read_file", file_path, False, str(e))
            return {
                "action": "file_reading",
                "success": False,
                "error": str(e)
            }

    def _write_file_task(self, task: str) -> Dict[str, Any]:
        """Write content to files."""
        write_info = self._extract_write_info(task)

        if not write_info.get("path") or not write_info.get("content"):
            return {
                "action": "file_writing",
                "success": False,
                "error": "File path and content are required"
            }

        try:
            file_path = self._get_safe_path(write_info["path"])
            content = write_info["content"]
            mode = write_info.get("mode", "w")  # 'w' for overwrite, 'a' for append

            # Create parent directories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)

            self._log_operation("write_file", file_path, True)

            return {
                "action": "file_writing",
                "success": True,
                "file_path": file_path,
                "content_length": len(content),
                "mode": mode
            }

        except Exception as e:
            self._log_operation("write_file", write_info["path"], False, str(e))
            return {
                "action": "file_writing",
                "success": False,
                "error": str(e)
            }

    def _delete_task(self, task: str) -> Dict[str, Any]:
        """Delete files or folders."""
        if self.safe_mode and "force" not in task.lower():
            return {
                "action": "deletion",
                "success": False,
                "error": "Safe mode enabled. Add 'force' to the request to confirm deletion."
            }

        paths = self._extract_paths(task)

        if not paths:
            return {
                "action": "deletion",
                "success": False,
                "error": "No paths specified for deletion"
            }

        results = []
        for path in paths:
            try:
                full_path = self._get_safe_path(path)

                if not os.path.exists(full_path):
                    results.append({
                        "path": full_path,
                        "success": False,
                        "error": "Path does not exist"
                    })
                    continue

                if os.path.isfile(full_path):
                    os.remove(full_path)
                    item_type = "file"
                else:
                    shutil.rmtree(full_path)
                    item_type = "directory"

                results.append({
                    "path": full_path,
                    "success": True,
                    "type": item_type
                })

                self._log_operation("delete", full_path, True)

            except Exception as e:
                results.append({
                    "path": path,
                    "success": False,
                    "error": str(e)
                })
                self._log_operation("delete", path, False, str(e))

        return {
            "action": "deletion",
            "results": results,
            "success": all(r["success"] for r in results)
        }

    def _search_task(self, task: str) -> Dict[str, Any]:
        """Search for files and folders."""
        search_info = self._extract_search_info(task)

        search_path = self._get_safe_path(search_info.get("path", "."))
        pattern = search_info.get("pattern", "*")
        file_type = search_info.get("type", "all")  # file, directory, all
        content_search = search_info.get("content")

        try:
            results = []

            for root, dirs, files in os.walk(search_path):
                # Search directories
                if file_type in ["directory", "all"]:
                    for dir_name in dirs:
                        if fnmatch.fnmatch(dir_name, pattern):
                            full_path = os.path.join(root, dir_name)
                            results.append({
                                "path": full_path,
                                "type": "directory",
                                "name": dir_name,
                                "size": self._get_directory_size(full_path)
                            })

                # Search files
                if file_type in ["file", "all"]:
                    for file_name in files:
                        if fnmatch.fnmatch(file_name, pattern):
                            full_path = os.path.join(root, file_name)
                            file_stats = os.stat(full_path)

                            file_info = {
                                "path": full_path,
                                "type": "file",
                                "name": file_name,
                                "size": file_stats.st_size,
                                "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                            }

                            # Content search if specified
                            if content_search and self._file_contains_text(full_path, content_search):
                                file_info["content_match"] = True

                            if not content_search or file_info.get("content_match"):
                                results.append(file_info)

            self._log_operation("search", search_path, True)

            return {
                "action": "file_search",
                "success": True,
                "search_path": search_path,
                "pattern": pattern,
                "results": results,
                "total_found": len(results)
            }

        except Exception as e:
            self._log_operation("search", search_path, False, str(e))
            return {
                "action": "file_search",
                "success": False,
                "error": str(e)
            }

    def _copy_task(self, task: str) -> Dict[str, Any]:
        """Copy files or directories."""
        copy_info = self._extract_copy_info(task)

        if not copy_info.get("source") or not copy_info.get("destination"):
            return {
                "action": "copy_operation",
                "success": False,
                "error": "Source and destination paths are required"
            }

        try:
            source = self._get_safe_path(copy_info["source"])
            destination = self._get_safe_path(copy_info["destination"])

            if not os.path.exists(source):
                return {
                    "action": "copy_operation",
                    "success": False,
                    "error": f"Source does not exist: {source}"
                }

            if os.path.isfile(source):
                # Create destination directory if needed
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                shutil.copy2(source, destination)
                operation_type = "file"
            else:
                shutil.copytree(source, destination, dirs_exist_ok=True)
                operation_type = "directory"

            self._log_operation("copy", f"{source} -> {destination}", True)

            return {
                "action": "copy_operation",
                "success": True,
                "source": source,
                "destination": destination,
                "type": operation_type
            }

        except Exception as e:
            self._log_operation("copy", f"{copy_info['source']} -> {copy_info['destination']}", False, str(e))
            return {
                "action": "copy_operation",
                "success": False,
                "error": str(e)
            }

    def _compress_task(self, task: str) -> Dict[str, Any]:
        """Create compressed archives."""
        compress_info = self._extract_compress_info(task)

        if not compress_info.get("source"):
            return {
                "action": "compression",
                "success": False,
                "error": "Source path is required"
            }

        try:
            source = self._get_safe_path(compress_info["source"])
            archive_name = compress_info.get("archive_name", f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            format_type = compress_info.get("format", "zip")

            if format_type == "zip":
                archive_path = f"{archive_name}.zip"
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if os.path.isfile(source):
                        zipf.write(source, os.path.basename(source))
                    else:
                        for root, dirs, files in os.walk(source):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_name = os.path.relpath(file_path, source)
                                zipf.write(file_path, arc_name)

            elif format_type == "tar":
                archive_path = f"{archive_name}.tar.gz"
                with tarfile.open(archive_path, 'w:gz') as tarf:
                    tarf.add(source, arcname=os.path.basename(source))

            self._log_operation("compress", f"{source} -> {archive_path}", True)

            return {
                "action": "compression",
                "success": True,
                "source": source,
                "archive_path": archive_path,
                "format": format_type,
                "archive_size": os.path.getsize(archive_path)
            }

        except Exception as e:
            self._log_operation("compress", source, False, str(e))
            return {
                "action": "compression",
                "success": False,
                "error": str(e)
            }

    def _list_task(self, task: str) -> Dict[str, Any]:
        """List directory contents."""
        path = self._extract_path_from_task(task) or "."
        show_hidden = "hidden" in task.lower() or "all" in task.lower()
        detailed = "detailed" in task.lower() or "long" in task.lower()

        try:
            full_path = self._get_safe_path(path)

            if not os.path.exists(full_path):
                return {
                    "action": "directory_listing",
                    "success": False,
                    "error": f"Path does not exist: {full_path}"
                }

            items = []
            for item_name in os.listdir(full_path):
                if not show_hidden and item_name.startswith('.'):
                    continue

                item_path = os.path.join(full_path, item_name)
                item_stats = os.stat(item_path)

                item_info = {
                    "name": item_name,
                    "path": item_path,
                    "type": "directory" if os.path.isdir(item_path) else "file"
                }

                if detailed:
                    item_info.update({
                        "size": item_stats.st_size,
                        "modified": datetime.fromtimestamp(item_stats.st_mtime).isoformat(),
                        "permissions": oct(item_stats.st_mode)[-3:]
                    })

                items.append(item_info)

            # Sort by type, then name
            items.sort(key=lambda x: (x["type"], x["name"]))

            self._log_operation("list", full_path, True)

            return {
                "action": "directory_listing",
                "success": True,
                "path": full_path,
                "items": items,
                "total_items": len(items),
                "detailed": detailed
            }

        except Exception as e:
            self._log_operation("list", path, False, str(e))
            return {
                "action": "directory_listing",
                "success": False,
                "error": str(e)
            }

    def _metadata_task(self, task: str) -> Dict[str, Any]:
        """Get file/directory metadata."""
        path = self._extract_path_from_task(task)

        if not path:
            return {
                "action": "metadata_retrieval",
                "success": False,
                "error": "No path specified"
            }

        try:
            full_path = self._get_safe_path(path)

            if not os.path.exists(full_path):
                return {
                    "action": "metadata_retrieval",
                    "success": False,
                    "error": f"Path does not exist: {full_path}"
                }

            stats = os.stat(full_path)
            is_file = os.path.isfile(full_path)

            metadata = {
                "path": full_path,
                "type": "file" if is_file else "directory",
                "size": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stats.st_atime).isoformat(),
                "permissions": oct(stats.st_mode)[-3:]
            }

            if is_file:
                # Additional file metadata
                mime_type, encoding = mimetypes.guess_type(full_path)
                metadata.update({
                    "mime_type": mime_type,
                    "encoding": encoding,
                    "hash_md5": self._calculate_file_hash(full_path)
                })
            else:
                # Directory metadata
                metadata.update({
                    "total_size": self._get_directory_size(full_path),
                    "item_count": len(os.listdir(full_path))
                })

            self._log_operation("metadata", full_path, True)

            return {
                "action": "metadata_retrieval",
                "success": True,
                "metadata": metadata
            }

        except Exception as e:
            self._log_operation("metadata", path, False, str(e))
            return {
                "action": "metadata_retrieval",
                "success": False,
                "error": str(e)
            }

    def _general_filesystem_task(self, task: str) -> Dict[str, Any]:
        """Handle general filesystem tasks."""
        return {
            "action": "filesystem_assistance",
            "success": True,
            "message": "I can help with file system operations. Try asking me to:",
            "capabilities": [
                "Create folders and files",
                "Read and write file contents",
                "Search for files and folders",
                "Copy, move, and delete items",
                "List directory contents",
                "Compress and extract archives",
                "Get file metadata and permissions",
                "Backup and sync operations"
            ],
            "examples": [
                "Create a folder named 'projects'",
                "Read the content of 'config.txt'",
                "Search for all .py files",
                "Copy 'data.csv' to 'backup/data.csv'",
                "List all files in the current directory",
                "Compress the 'documents' folder"
            ]
        }

    # Helper methods
    def _get_safe_path(self, path: str) -> str:
        """Get safe, absolute path within base directory."""
        if self.safe_mode:
            # Resolve path and ensure it's within base_path
            abs_path = os.path.abspath(os.path.join(self.base_path, path))
            if not abs_path.startswith(os.path.abspath(self.base_path)):
                raise ValueError(f"Path outside safe directory: {path}")
            return abs_path
        else:
            return os.path.abspath(path)

    def _log_operation(self, operation: str, path: str, success: bool, error: str = None):
        """Log file system operation."""
        self.operation_history.append({
            "operation": operation,
            "path": path,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def _extract_folder_paths(self, task: str) -> List[str]:
        """Extract folder paths from task."""
        # Simple extraction - in practice, you'd use more sophisticated NLP
        words = task.split()
        paths = []

        for i, word in enumerate(words):
            if word.lower() in ["folder", "directory"] and i + 1 < len(words):
                next_word = words[i + 1]
                if not next_word.lower() in ["named", "called"]:
                    paths.append(next_word.strip('"\''))
            elif word.lower() in ["named", "called"] and i + 1 < len(words):
                paths.append(words[i + 1].strip('"\''))

        return paths

    def _extract_file_path(self, task: str) -> str:
        """Extract file path from task."""
        # Look for quoted paths first
        import re
        quoted_match = re.search(r'["\']([^"\']+)["\']', task)
        if quoted_match:
            return quoted_match.group(1)

        # Look for file extensions
        words = task.split()
        for word in words:
            if '.' in word and not word.startswith('.'):
                return word

        return None

    def _extract_file_creation_info(self, task: str) -> Dict[str, Any]:
        """Extract file creation information."""
        info = {}

        # Extract file path
        info["path"] = self._extract_file_path(task)

        # Extract content if specified
        if "content" in task.lower() or "with" in task.lower():
            # Simple content extraction
            content_match = task.split("content")[-1].strip()
            if content_match:
                info["content"] = content_match.strip('"\'')

        return info

    def _file_contains_text(self, file_path: str, search_text: str) -> bool:
        """Check if file contains specific text."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return search_text.lower() in f.read().lower()
        except:
            return False

    def _get_directory_size(self, path: str) -> int:
        """Calculate total size of directory."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except:
            pass
        return total_size

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get operation history."""
        return self.operation_history