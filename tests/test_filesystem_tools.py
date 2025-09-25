import os
from pathlib import Path

import pytest

from agenticflow.tools.search_tools import (
    FileStatTool,
    RegexSearchTool,
    RegexSearchDirTool,
    DirTreeTool,
    FindFilesTool,
)
from agenticflow.tools.file_tools import (
    ReadTextFastTool,
    ReadBytesFastTool,
    WriteTextAtomicTool,
)
from langchain_community.tools.file_management import ReadFileTool, WriteFileTool


@pytest.fixture()
def sample_tree(tmp_path: Path):
    # Create a small tree with mixed files
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.txt").write_text("hello world\nabc 123\nHELLO WORLD\n")
    (tmp_path / "a" / "two.md").write_text("markdown file\nhello again\n")
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "three.py").write_text("print('hello world')\n# TODO: hello\n")
    (tmp_path / "b" / "bin.dat").write_bytes(b"\x00\x01\x02\x03")
    return tmp_path


def test_file_stat_tool(tmp_path: Path):
    f = tmp_path / "x.txt"
    f.write_text("x")
    stat_tool = FileStatTool()
    res = stat_tool.run(str(f))
    assert res["exists"] is True
    assert res["is_dir"] is False
    assert res["size_bytes"] == 1

    res2 = stat_tool.run(str(tmp_path / "nope.txt"))
    assert res2["exists"] is False


def test_regex_search_file(tmp_path: Path):
    f = tmp_path / "data.txt"
    f.write_text("alpha\nBeta\nALPHA beta\nGamma\n")
    tool = RegexSearchTool()
    out = tool.run({"path": str(f), "pattern": r"alpha", "flags": "i", "context_lines": 1})
    assert out["total"] >= 2
    assert all("line" in m and "text" in m for m in out["matches"])


def test_regex_search_dir(sample_tree: Path):
    tool = RegexSearchDirTool()
    out = tool.run({
        "root_path": str(sample_tree),
        "pattern": r"hello",
        "flags": "i",
        "include_exts": [".txt", ".md", ".py"],
        "max_matches": 10,
    })
    assert out["total"] >= 3
    assert out["files_scanned"] > 0


def test_dir_tree(sample_tree: Path):
    tool = DirTreeTool()
    out = tool.run(str(sample_tree), max_depth=2, include_exts=[".txt", ".md", ".py"]) 
    assert out["total"] > 0
    entries = out["entries"]
    # Check directories and files exist in entries
    paths = {e["path"] for e in entries}
    assert str(sample_tree / "a") in paths
    assert str(sample_tree / "b" / "three.py") in paths


def test_find_files(sample_tree: Path):
    tool = FindFilesTool()
    out = tool.run(str(sample_tree), file_glob="*.txt", include_exts=[".txt"], max_files=10)
    assert out["total"] >= 1
    files = out["files"]
    assert any(f["path"].endswith("one.txt") for f in files)


def test_fast_read_write_vs_langchain(tmp_path: Path):
    target = tmp_path / "hello.txt"

    # Write via our atomic tool
    write_fast = WriteTextAtomicTool()
    msg = write_fast.run({"path": str(target), "content": "Hello Fast World!\n"})
    assert "Wrote" in msg
    assert target.exists()

    # Read via our fast tool
    read_fast = ReadTextFastTool()
    content_fast = read_fast.run(str(target))

    # Write again via LangChain tool
    write_std = WriteFileTool()
    msg2 = write_std.run({"file_path": str(target), "text": "Hello Standard World!\n"})
    assert "wrote file" in msg2.lower() or msg2

    # Read via LangChain tool
    read_std = ReadFileTool()
    content_std = read_std.run(str(target))

    assert isinstance(content_fast, str)
    assert isinstance(content_std, str)
    assert content_std.endswith("World!\n")

    # Read bytes via our tool
    read_bytes = ReadBytesFastTool()
    b = read_bytes.run(str(target))
    assert isinstance(b, (bytes, bytearray))
    assert b.endswith(b"\n")
