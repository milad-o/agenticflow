import os
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_groq_generate_integration():
    if not os.environ.get("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set; skipping Groq integration test")

    from examples.utils.provider_factory import create_llm_from_env

    os.environ.setdefault("AGENTICFLOW_LLM_PROVIDER", "groq")
    os.environ.setdefault("GROQ_MODEL", "llama-3.1-8b-instant")

    llm = create_llm_from_env()
    res = await llm.generate("Write a 5-word greeting.")
    assert isinstance(res.text, str)
    assert len(res.text.strip()) > 0
