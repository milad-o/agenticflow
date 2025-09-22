import os
import pytest

from agenticflow.ai.file_qa import answer_question_over_dir
from examples.utils.provider_factory import create_llm_from_env


@pytest.mark.asyncio
async def test_file_qa_noop_provider(tmp_path):
    # Prepare small corpus
    base = tmp_path / "docs"
    base.mkdir()
    (base / "a.md").write_text("Science uses hypothesis and test")
    (base / "b.md").write_text("Law uses precedent and due process")

    # Use noop provider to avoid network calls
    os.environ["AGENTICFLOW_LLM_PROVIDER"] = "noop"
    llm = create_llm_from_env()

    answer, citations = await answer_question_over_dir(str(base), "Compare science and law", llm=llm, max_files=5)
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert any("a.md" in c or "b.md" in c for c in citations)
