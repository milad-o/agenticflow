from __future__ import annotations

from typing import List, Tuple

from agenticflow.util.io import list_files, read_text_safe
from agenticflow.tools.external.llm import LLMClient, LLMResult


def _score(content: str, terms: List[str]) -> int:
    t = content.lower()
    return sum(t.count(term) for term in terms if term)


def _pick_relevant(files: List[Tuple[str, str]], question: str, k: int) -> List[Tuple[str, str]]:
    terms = [w.strip(".,!?()[]{}'\"`).:;").lower() for w in question.split()]
    scored = [(p, c, _score(c, terms)) for (p, c) in files]
    scored.sort(key=lambda x: x[2], reverse=True)
    out = [(p, c) for (p, c, s) in scored if s > 0][:k]
    return out or files[:k]


async def answer_question_over_dir(
    path: str,
    question: str,
    *,
    llm: LLMClient,
    ignore_globs: List[str] | None = None,
    max_files: int = 20,
    max_bytes_per_file: int = 2000,
) -> tuple[str, List[str]]:
    paths = list_files(path, ignore_globs=ignore_globs or ["**/artifacts/**"])
    pairs: List[Tuple[str, str]] = []
    for p in paths:
        try:
            content = read_text_safe(p, max_bytes=max_bytes_per_file)
            if content:
                pairs.append((str(p), content))
        except Exception:
            continue
    chosen = _pick_relevant(pairs, question, max_files)
    prompt_lines: List[str] = []
    prompt_lines.append("You are an expert assistant. Answer the user's question using only the provided files.")
    prompt_lines.append("Cite which files you used at the end under a 'Citations' section.")
    prompt_lines.append("\nFiles:\n")
    for (p, c) in chosen:
        prompt_lines.append(f"FILE: {p}\n" + c + "\n")
    prompt_lines.append("\nUser question:\n" + question + "\n\nReturn a concise markdown answer with bullet points and a final 'Citations' section listing the file paths used.")
    res: LLMResult = await llm.generate("\n".join(prompt_lines))
    return res.text, [p for (p, _) in chosen]