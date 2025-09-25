#!/usr/bin/env python3
"""
Simple filesystem benchmark for AgenticFlow tools.

Usage:
  python scripts/bench_fs.py --files 200 --size-kb 64 --pattern hello

It compares:
- LangChain ReadFileTool (read_file)
- Our ReadTextFastTool (read_text_fast)
- RegexSearchDirTool for scanning/searching

The benchmark uses a temporary directory and reports wall-clock durations.
"""
from __future__ import annotations

import argparse
import os
import random
import string
import tempfile
from pathlib import Path
from time import perf_counter

from agenticflow.tools.search_tools import RegexSearchDirTool
from agenticflow.tools.file_tools import ReadTextFastTool
from langchain_community.tools.file_management import ReadFileTool


def make_files(root: Path, n_files: int, size_kb: int, include_pattern: str) -> list[Path]:
    root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    line = ("This is a sample line with pattern: %s\n" % include_pattern).encode()
    filler = ("".join(random.choices(string.ascii_letters + string.digits, k=80)) + "\n").encode()
    bytes_per_file = size_kb * 1024
    for i in range(n_files):
        p = root / f"file_{i:05d}.txt"
        with open(p, "wb") as f:
            written = 0
            while written < bytes_per_file:
                if written % (len(line) * 5) == 0:
                    f.write(line)
                    written += len(line)
                else:
                    f.write(filler)
                    written += len(filler)
        paths.append(p)
    return paths


def time_read_all(tool, files: list[Path], runner) -> float:
    # Warmup
    for p in files[:5]:
        runner(tool, p)
    t0 = perf_counter()
    for p in files:
        runner(tool, p)
    t1 = perf_counter()
    return t1 - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", type=int, default=200)
    ap.add_argument("--size-kb", type=int, default=64)
    ap.add_argument("--pattern", type=str, default="hello")
    args = ap.parse_args()

    read_std = ReadFileTool()
    read_fast = ReadTextFastTool()
    search_dir = RegexSearchDirTool()

    def run_read_std(tool, p: Path):
        return tool.run({"file_path": str(p)})

    def run_read_fast(tool, p: Path):
        return tool.run({"path": str(p)})

    with tempfile.TemporaryDirectory(prefix="agenticflow_fs_bench_") as d:
        root = Path(d)
        data_dir = root / "data"
        files = make_files(data_dir, args.files, args.size_kb, args.pattern)

        # Timings
        t_std = time_read_all(read_std, files, run_read_std)
        t_fast = time_read_all(read_fast, files, run_read_fast)

        # Search timing
        # Warmup
        search_dir.run({
            "root_path": str(data_dir),
            "pattern": args.pattern,
            "flags": "i",
            "include_exts": [".txt"],
            "max_matches": args.files,
        })
        t0 = perf_counter()
        out = search_dir.run({
            "root_path": str(data_dir),
            "pattern": args.pattern,
            "flags": "i",
            "include_exts": [".txt"],
            "max_matches": args.files,
        })
        t1 = perf_counter()
        t_search = t1 - t0

        print("Filesystem benchmark results:")
        print(f"  Files:        {args.files}")
        print(f"  Size per file:{args.size_kb} KB")
        print(f"  Pattern:      {args.pattern}")
        print(f"  Read (std):   {t_std:.3f} s")
        print(f"  Read (fast):  {t_fast:.3f} s")
        print(f"  Search (dir): {t_search:.3f} s  (matches={out.get('total')})")


if __name__ == "__main__":
    main()
