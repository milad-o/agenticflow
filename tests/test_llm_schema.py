import json
import pytest

from agenticflow.agents.supervisor.llm_schema import parse_plan
from agenticflow.agents.capabilities.matcher import CapabilityMatcher


class DummyMatcher(CapabilityMatcher):
    async def find_agent_for(self, required_capability: str):
        mapping = {
            "data_analysis": "analyst",
            "report_generation": "reporter",
        }
        return mapping.get(required_capability)


@pytest.mark.asyncio
async def test_parse_plan_normalizes_tasks():
    text = json.dumps({
        "tasks": [
            {"type": "analyze", "capability": "data_analysis", "params": {"x": 1}},
            {"id": "g1", "cap": "report_generation", "deps": ["t1"]},
        ]
    })
    wf = await parse_plan(text, matcher=DummyMatcher(), default_agent="worker")
    assert len(wf.tasks) == 2
    assert wf.tasks[0].agent_id == "analyst"
    assert wf.tasks[1].agent_id == "reporter"
    assert "t1" in wf.tasks[1].dependencies


@pytest.mark.asyncio
async def test_parse_plan_handles_empty_and_missing_fields():
    text = json.dumps({"tasks": [{}]})
    wf = await parse_plan(text, matcher=DummyMatcher(), default_agent="worker")
    assert len(wf.tasks) == 1
    assert wf.tasks[0].agent_id == "worker"
    assert wf.tasks[0].task_type == "noop"
