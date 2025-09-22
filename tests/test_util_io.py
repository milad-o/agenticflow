import os
import tempfile
from pathlib import Path

from agenticflow.util.io import list_files, read_text_safe, chunk_text


def test_list_files_and_ignore(tmp_path: Path):
    base = tmp_path / "root"
    (base / "a").mkdir(parents=True)
    (base / "artifacts").mkdir(parents=True)
    (base / "a" / "note.md").write_text("hello")
    (base / "artifacts" / "out.md").write_text("ignore me")

    files = list_files(base, ignore_globs=["**/artifacts/**"])
    rels = {str(p.relative_to(base)) for p in files}
    assert "a/note.md" in rels
    assert "artifacts/out.md" not in rels


def test_read_and_chunk(tmp_path: Path):
    p = tmp_path / "big.txt"
    p.write_text("x" * 5000)
    text = read_text_safe(p, max_bytes=2000)
    assert len(text) == 2000

    chunks = chunk_text("hello world" * 100, chunk_size=50, overlap=10)
    assert len(chunks) > 1
