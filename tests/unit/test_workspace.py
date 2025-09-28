"""Tests for workspace functionality."""

import pytest
import json
from pathlib import Path

from agenticflow.workspace.workspace import Workspace


@pytest.mark.asyncio
class TestWorkspace:
    """Test Workspace functionality."""

    async def test_workspace_creation(self, temp_workspace):
        """Test workspace creation."""
        assert temp_workspace.workspace_path.exists()
        assert temp_workspace.workspace_path.is_dir()

    async def test_write_and_read_file(self, temp_workspace):
        """Test writing and reading files."""
        content = "Hello, world!"
        file_path = "test.txt"

        # Write file
        written_path = await temp_workspace.write_file(file_path, content)
        assert Path(written_path).exists()

        # Read file
        read_content = await temp_workspace.read_file(file_path)
        assert read_content == content

    async def test_append_file(self, temp_workspace):
        """Test appending to files."""
        file_path = "append_test.txt"

        await temp_workspace.write_file(file_path, "Line 1\n")
        await temp_workspace.append_file(file_path, "Line 2\n")

        content = await temp_workspace.read_file(file_path)
        assert content == "Line 1\nLine 2\n"

    async def test_delete_file(self, temp_workspace):
        """Test deleting files."""
        file_path = "delete_test.txt"

        await temp_workspace.write_file(file_path, "To be deleted")
        assert await temp_workspace.file_exists(file_path)

        deleted = await temp_workspace.delete_file(file_path)
        assert deleted
        assert not await temp_workspace.file_exists(file_path)

        # Try deleting non-existent file
        deleted_again = await temp_workspace.delete_file(file_path)
        assert not deleted_again

    async def test_list_files(self, temp_workspace):
        """Test listing files."""
        # Create some test files
        await temp_workspace.write_file("file1.txt", "content1")
        await temp_workspace.write_file("file2.txt", "content2")
        await temp_workspace.write_file("subdir/file3.txt", "content3")

        # List all files
        all_files = await temp_workspace.list_files()
        assert "file1.txt" in all_files
        assert "file2.txt" in all_files
        assert "subdir/file3.txt" in all_files

        # List with pattern
        txt_files = await temp_workspace.list_files(pattern="*.txt")
        assert len(txt_files) >= 2

    async def test_create_directory(self, temp_workspace):
        """Test directory creation."""
        dir_path = "test_directory/nested"

        created_path = await temp_workspace.create_directory(dir_path)
        assert Path(created_path).exists()
        assert Path(created_path).is_dir()

    async def test_file_info(self, temp_workspace):
        """Test getting file information."""
        file_path = "info_test.txt"
        content = "Test content"

        await temp_workspace.write_file(file_path, content)

        file_info = await temp_workspace.get_file_info(file_path)

        assert file_info["path"] == file_path
        assert file_info["size"] == len(content)
        assert file_info["is_file"]
        assert not file_info["is_directory"]
        assert "created" in file_info
        assert "modified" in file_info

    async def test_json_operations(self, temp_workspace):
        """Test JSON read/write operations."""
        file_path = "test.json"
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        # Write JSON
        await temp_workspace.write_json(file_path, data)

        # Read JSON
        read_data = await temp_workspace.read_json(file_path)
        assert read_data == data

    async def test_copy_file(self, temp_workspace):
        """Test copying files."""
        source_path = "source.txt"
        dest_path = "destination.txt"
        content = "Content to copy"

        await temp_workspace.write_file(source_path, content)
        copied_path = await temp_workspace.copy_file(source_path, dest_path)

        assert Path(copied_path).exists()
        read_content = await temp_workspace.read_file(dest_path)
        assert read_content == content

    async def test_workspace_info(self, temp_workspace):
        """Test getting workspace information."""
        # Create some test files
        await temp_workspace.write_file("file1.txt", "content1")
        await temp_workspace.write_file("file2.txt", "content2")

        info = await temp_workspace.get_workspace_info()

        assert info["workspace_path"] == str(temp_workspace.workspace_path)
        assert info["total_files"] >= 2
        assert info["total_size"] > 0
        assert info["exists"]

    async def test_path_security(self, temp_workspace):
        """Test path security - prevent directory traversal."""
        with pytest.raises(ValueError):
            await temp_workspace.write_file("/etc/passwd", "malicious content")

        with pytest.raises(ValueError):
            await temp_workspace.write_file("../../../etc/passwd", "malicious content")

    async def test_file_not_found_error(self, temp_workspace):
        """Test proper error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            await temp_workspace.read_file("nonexistent.txt")

        with pytest.raises(FileNotFoundError):
            await temp_workspace.get_file_info("nonexistent.txt")

        with pytest.raises(FileNotFoundError):
            await temp_workspace.copy_file("nonexistent.txt", "dest.txt")