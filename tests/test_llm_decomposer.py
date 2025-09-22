import json
import pytest

from agenticflow.agents.supervisor.decomposition import LLMTaskDecomposer
from agenticflow.agents.capabilities.matcher import DictCapabilityMatcher
from agenticflow.tools.external.llm import LLMClient, LLMResult
from agenticflow.orchestration.core.orchestrator import WorkflowDefinition


class FakeLLM(LLMClient):
    def __init__(self, text: str):
        self._text = text

    async def generate(self, prompt: str, *, model: str | None = None, **params) -> LLMResult:
        return LLMResult(text=self._text, model=model)

    async def chat(self, messages, *, model: str | None = None, **params) -> LLMResult:
        return LLMResult(text=self._text, model=model)


@pytest.mark.asyncio
async def test_llm_decomposer_parses_tasks_and_matches_agents():
    plan = {
        "tasks": [
            {"id": "t1", "type": "analyze", "capability": "data_analysis", "params": {"ds": "sales.csv"}, "deps": []},
            {"id": "t2", "type": "report", "capability": "report_generation", "params": {}, "deps": ["t1"]},
        ]
    }
    llm = FakeLLM(text=json.dumps(plan))
    matcher = DictCapabilityMatcher({
        "data_analysis": "analyst",
        "report_generation": "reporter",
    })

    dec = LLMTaskDecomposer(llm=llm, matcher=matcher)
    wf = await dec.decompose("analyze and report", context={"default_agent": "worker"})

    assert isinstance(wf, WorkflowDefinition)
    assert len(wf.tasks) == 2
    assert wf.tasks[0].agent_id == "analyst"
    assert wf.tasks[1].agent_id == "reporter"
    assert "t1" in wf.tasks[1].dependencies
