import os
import pytest
import httpx

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_ollama_llm_generate_integration():
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    desired = os.environ.get("OLLAMA_LLM_MODEL")

    # Discover local models and pick one (avoid embed models)
    async with httpx.AsyncClient(base_url=base) as client:
        try:
            t = await client.get("/api/tags", timeout=5.0)
            t.raise_for_status()
            data = t.json()
            names = [ (m.get("name") or m.get("model") or "") for m in data.get("models", []) ]
            if not names:
                pytest.skip("No local Ollama models found; skipping")
            # If desired provided, verify exists (supports prefix without tag)
            model = None
            if desired:
                for n in names:
                    if n == desired or n.startswith(desired):
                        model = n
                        break
                if model is None:
                    pytest.skip(f"Desired model {desired} not found locally; skipping")
            else:
                # choose the first non-embedding model
                for n in names:
                    base_name = n.split(":")[0].lower()
                    if "embed" not in base_name:
                        model = n
                        break
                if model is None:
                    pytest.skip("Only embedding models found; skipping")
        except Exception:
            pytest.skip("Ollama not reachable; skipping")

    from examples.utils.provider_factory import create_llm_from_env

    os.environ["AGENTICFLOW_LLM_PROVIDER"] = "ollama"
    os.environ["OLLAMA_LLM_MODEL"] = model

    llm = create_llm_from_env()
    res = await llm.generate("Write a 3-word phrase.")
    assert isinstance(res.text, str)
    assert len(res.text.strip()) > 0
