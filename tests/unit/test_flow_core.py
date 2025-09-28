"""Unit tests for Flow core functionality."""

import pytest
import pytest_asyncio
import asyncio
from pathlib import Path

from agenticflow import Flow, Orchestrator
from agenticflow.core.agent import SimpleAgent


@pytest_asyncio.fixture
async def flow_instance() -> Flow:
    flow = Flow("core_test_flow")
    yield flow
    await flow.stop()


class TestFlow:
    """Test cases for Flow class."""

    def test_flow_creation(self, temp_workspace):
        flow = Flow("test_flow", workspace_path=temp_workspace.workspace_path)
        assert flow.name == "test_flow"
        assert flow.orchestrator is None
        assert not flow.is_running()

    def test_flow_with_workspace(self, temp_workspace):
        flow = Flow("test_flow", workspace_path=temp_workspace.workspace_path)
        assert flow.workspace.workspace_path == temp_workspace.workspace_path

    def test_add_orchestrator(self, flow_instance):
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        flow_instance.add_orchestrator(orchestrator)
        assert flow_instance.orchestrator == orchestrator
        assert orchestrator.flow == flow_instance

    def test_flow_method_chaining(self):
        flow = (Flow("test_flow")
                .add_orchestrator(Orchestrator("test_orchestrator", initialize_llm=False)))
        assert flow.name == "test_flow"
        assert flow.orchestrator.name == "test_orchestrator"

    @pytest.mark.asyncio
    async def test_flow_start_without_orchestrator(self, flow_instance):
        with pytest.raises(ValueError, match="No orchestrator configured"):
            await flow_instance.start("test message")

    @pytest.mark.asyncio
    async def test_flow_start_simple(self, simple_flow):
        start_task = asyncio.create_task(simple_flow.start("test message", continuous=True))
        await asyncio.sleep(0.1)
        assert simple_flow.is_running()
        await simple_flow.stop()
        start_task.cancel()

    def test_flow_context_manager(self, temp_workspace):
        orchestrator = Orchestrator("context_orchestrator", initialize_llm=False)
        orchestrator.add_agent(SimpleAgent("test_agent"))

        async def run_context():
            async with Flow("test_flow", workspace_path=temp_workspace.workspace_path) as flow:
                flow.add_orchestrator(orchestrator)
                start_task = asyncio.create_task(flow.start("Test message", continuous=True))
                await asyncio.sleep(0.1)
                assert flow.is_running()
                await flow.stop()
                start_task.cancel()
            assert not flow.is_running()

        asyncio.run(run_context())

    def test_flow_str_representation(self):
        flow = Flow("test_flow")
        assert repr(flow) == f"Flow(name='test_flow', id='{flow.id[:8]}')"

    def test_flow_repr(self):
        flow = Flow("test_flow")
        assert repr(flow) == f"Flow(name='test_flow', id='{flow.id[:8]}')"
