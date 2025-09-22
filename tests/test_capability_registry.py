import pytest

from agenticflow.agents.capabilities.registry import CapabilityRegistry
from agenticflow.agents.capabilities.matcher import RegistryCapabilityMatcher


def test_registry_capability_matcher():
    reg = CapabilityRegistry()
    reg.register("analyst", ["data_analysis", "etl"])
    reg.register("reporter", ["report_generation"]) 

    matcher = RegistryCapabilityMatcher(reg)

    import asyncio
    agent = asyncio.get_event_loop().run_until_complete(matcher.find_agent_for("data_analysis"))
    assert agent == "analyst"

    agent2 = asyncio.get_event_loop().run_until_complete(matcher.find_agent_for("report_generation"))
    assert agent2 == "reporter"
