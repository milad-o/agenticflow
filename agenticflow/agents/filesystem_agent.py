"""Filesystem agent with comprehensive file operations."""

import os
import shutil
import glob
import mimetypes
from pathlib import Path
from typing import Annotated, List, Optional
from langchain_core.tools import tool
from langchain_community.tools import ShellTool
from ..core.flow import Agent

class FilesystemAgent(Agent):
    """Agent specialized in filesystem operations."""
    
    def __init__(self, name: str = "filesystem_agent", description: str = "Filesystem operations specialist"):
        tools = self._create_tools()
        super().__init__(name, tools=tools, description=description)
    
    def _create_tools(self) -> List:
        """Create filesystem tools."""
        return [
            self._create_file,
            self._read_file,
            self._write_file,
            self._append_file,
            self._delete_file,
            self._copy_file,
            self._move_file,
            self._create_directory,
            self._delete_directory,
            self._list_directory,
            self._find_files,
            self._grep_files,
            self._get_file_info,
            self._search_files,
            self._backup_file,
            self._shell_tool
        ]
    
    @tool
    def _create_file(
        self,
        content: Annotated[str, "Content to write to the file"],
        filename: Annotated[str, "Name of the file to create"],
        directory: Annotated[str, "Directory to create file in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Create a new file with content."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ Created file '{filepath}' with {len(content)} characters"
        except Exception as e:
            return f"❌ Error creating file: {e}"
    
    @tool
    def _read_file(
        self,
        filename: Annotated[str, "Name of the file to read"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Read content from a file."""
        try:
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return f"📖 File '{filepath}' content:\n{content}"
        except Exception as e:
            return f"❌ Error reading file: {e}"
    
    @tool
    def _write_file(
        self,
        content: Annotated[str, "Content to write to the file"],
        filename: Annotated[str, "Name of the file to write"],
        directory: Annotated[str, "Directory to write file in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Write content to a file (overwrites existing)."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✏️ Wrote {len(content)} characters to '{filepath}'"
        except Exception as e:
            return f"❌ Error writing file: {e}"
    
    @tool
    def _append_file(
        self,
        content: Annotated[str, "Content to append to the file"],
        filename: Annotated[str, "Name of the file to append to"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Append content to an existing file."""
        try:
            filepath = os.path.join(directory, filename)
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(content)
            return f"➕ Appended {len(content)} characters to '{filepath}'"
        except Exception as e:
            return f"❌ Error appending to file: {e}"
    
    @tool
    def _delete_file(
        self,
        filename: Annotated[str, "Name of the file to delete"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Delete a file."""
        try:
            filepath = os.path.join(directory, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return f"🗑️ Deleted file '{filepath}'"
            else:
                return f"⚠️ File '{filepath}' not found"
        except Exception as e:
            return f"❌ Error deleting file: {e}"
    
    @tool
    def _copy_file(
        self,
        source: Annotated[str, "Source file path"],
        destination: Annotated[str, "Destination file path"]
    ) -> str:
        """Copy a file from source to destination."""
        try:
            shutil.copy2(source, destination)
            return f"📋 Copied '{source}' to '{destination}'"
        except Exception as e:
            return f"❌ Error copying file: {e}"
    
    @tool
    def _move_file(
        self,
        source: Annotated[str, "Source file path"],
        destination: Annotated[str, "Destination file path"]
    ) -> str:
        """Move a file from source to destination."""
        try:
            shutil.move(source, destination)
            return f"📦 Moved '{source}' to '{destination}'"
        except Exception as e:
            return f"❌ Error moving file: {e}"
    
    @tool
    def _create_directory(
        self,
        dirname: Annotated[str, "Name of the directory to create"],
        parent_dir: Annotated[str, "Parent directory (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Create a new directory."""
        try:
            dirpath = os.path.join(parent_dir, dirname)
            os.makedirs(dirpath, exist_ok=True)
            return f"📁 Created directory '{dirpath}'"
        except Exception as e:
            return f"❌ Error creating directory: {e}"
    
    @tool
    def _delete_directory(
        self,
        dirname: Annotated[str, "Name of the directory to delete"],
        parent_dir: Annotated[str, "Parent directory (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Delete a directory and all its contents."""
        try:
            dirpath = os.path.join(parent_dir, dirname)
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath)
                return f"🗑️ Deleted directory '{dirpath}'"
            else:
                return f"⚠️ Directory '{dirpath}' not found"
        except Exception as e:
            return f"❌ Error deleting directory: {e}"
    
    @tool
    def _list_directory(
        self,
        directory: Annotated[str, "Directory to list (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """List contents of a directory."""
        try:
            if not os.path.exists(directory):
                return f"⚠️ Directory '{directory}' not found"
            
            items = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"📄 {item} ({size} bytes)")
            
            return f"📂 Contents of '{directory}':\n" + "\n".join(items)
        except Exception as e:
            return f"❌ Error listing directory: {e}"
    
    @tool
    def _find_files(
        self,
        pattern: Annotated[str, "File pattern to search for (e.g., '*.txt', '*.py')"],
        directory: Annotated[str, "Directory to search in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Find files matching a pattern."""
        try:
            search_pattern = os.path.join(directory, "**", pattern)
            files = glob.glob(search_pattern, recursive=True)
            if files:
                return f"🔍 Found {len(files)} files matching '{pattern}':\n" + "\n".join(files)
            else:
                return f"🔍 No files found matching '{pattern}' in '{directory}'"
        except Exception as e:
            return f"❌ Error finding files: {e}"
    
    @tool
    def _grep_files(
        self,
        pattern: Annotated[str, "Text pattern to search for"],
        file_pattern: Annotated[str, "File pattern to search in (e.g., '*.txt', '*.py')"],
        directory: Annotated[str, "Directory to search in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Search for text pattern in files."""
        try:
            import re
            search_pattern = os.path.join(directory, "**", file_pattern)
            files = glob.glob(search_pattern, recursive=True)
            matches = []
            
            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if re.search(pattern, content, re.IGNORECASE):
                            matches.append(f"📄 {file_path}")
                except:
                    continue
            
            if matches:
                return f"🔍 Found '{pattern}' in {len(matches)} files:\n" + "\n".join(matches)
            else:
                return f"🔍 No matches found for '{pattern}' in '{file_pattern}' files"
        except Exception as e:
            return f"❌ Error searching files: {e}"
    
    @tool
    def _get_file_info(
        self,
        filename: Annotated[str, "Name of the file to get info for"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Get detailed information about a file."""
        try:
            filepath = os.path.join(directory, filename)
            if not os.path.exists(filepath):
                return f"⚠️ File '{filepath}' not found"
            
            stat = os.stat(filepath)
            mime_type, _ = mimetypes.guess_type(filepath)
            
            info = f"📄 File: {filepath}\n"
            info += f"📏 Size: {stat.st_size} bytes\n"
            info += f"📅 Modified: {stat.st_mtime}\n"
            info += f"🔒 Permissions: {oct(stat.st_mode)[-3:]}\n"
            info += f"📋 MIME Type: {mime_type or 'Unknown'}\n"
            
            return info
        except Exception as e:
            return f"❌ Error getting file info: {e}"
    
    @tool
    def _search_files(
        self,
        query: Annotated[str, "Search query"],
        directory: Annotated[str, "Directory to search in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Search for files by name or content."""
        try:
            results = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if query.lower() in file.lower():
                        results.append(f"📄 {file_path}")
                    else:
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    results.append(f"📄 {file_path} (content match)")
                        except:
                            continue
            
            if results:
                return f"🔍 Found {len(results)} files matching '{query}':\n" + "\n".join(results)
            else:
                return f"🔍 No files found matching '{query}'"
        except Exception as e:
            return f"❌ Error searching files: {e}"
    
    @tool
    def _backup_file(
        self,
        filename: Annotated[str, "Name of the file to backup"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Create a backup of a file."""
        try:
            filepath = os.path.join(directory, filename)
            if not os.path.exists(filepath):
                return f"⚠️ File '{filepath}' not found"
            
            backup_path = f"{filepath}.backup"
            shutil.copy2(filepath, backup_path)
            return f"💾 Created backup '{backup_path}'"
        except Exception as e:
            return f"❌ Error creating backup: {e}"
    
    @property
    def _shell_tool(self):
        """Shell tool for advanced operations."""
        return ShellTool()
