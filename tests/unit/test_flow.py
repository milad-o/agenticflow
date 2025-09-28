"""Tests for flow functionality."""

import pytest
import asyncio
from pathlib import Path

from agenticflow.core.flow import Flow
from agenticflow.core.orchestrator import Orchestrator
from agenticflow.core.agent import SimpleAgent
from agenticflow.core.supervisor import Supervisor
from agenticflow.core.state import MessageType


@pytest.mark.asyncio
class TestFlow:
    """Test Flow functionality."""

    async def test_flow_creation(self, temp_workspace):
        """Test basic flow creation."""
        flow = Flow(
            name="test_flow",
            workspace_path=temp_workspace.workspace_path,
            auto_create_workspace=False,
        )

        assert flow.name == "test_flow"
        assert flow.workspace.workspace_path == temp_workspace.workspace_path
        assert flow.state is not None
        assert flow.observer is not None
        assert not flow.is_running()

    async def test_flow_without_observability(self, temp_workspace):
        """Test flow creation without observability."""
        flow = Flow(
            name="test_flow",
            workspace_path=temp_workspace.workspace_path,
            enable_observability=False,
        )

        assert flow.observer is None

    async def test_flow_orchestrator_management(self, simple_flow):
        """Test adding orchestrator to flow."""
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        agent = SimpleAgent("test_agent")
        orchestrator.add_agent(agent)

        simple_flow.add_orchestrator(orchestrator)

        assert simple_flow.orchestrator == orchestrator
        assert orchestrator.flow == simple_flow

    async def test_flow_start_without_orchestrator(self):
        """Test starting flow without orchestrator raises error."""
        flow = Flow("no_orchestrator")
        with pytest.raises(ValueError, match="No orchestrator configured"):
            await flow.start("Test message")

    async def test_flow_start_and_stop(self, simple_flow):
        """Test starting and stopping flow."""
        flow = simple_flow

        start_task = asyncio.create_task(flow.start("Test message"))
        await asyncio.sleep(0.1)
        assert flow.is_running()

        await flow.stop()
        try:
            await asyncio.wait_for(start_task, timeout=1.0)
        except asyncio.TimeoutError:
            start_task.cancel()

        assert not flow.is_running()

    async def test_flow_message_sending(self, simple_flow):
        """Test sending messages during flow execution."""
        flow = simple_flow

        start_task = asyncio.create_task(flow.start("Initial message", continuous=True))
        await asyncio.sleep(0.1)

        await flow.send_message("Additional message", "user")

        messages = await flow.get_messages()
        assert isinstance(messages, list)

        await flow.stop()
        try:
            await asyncio.wait_for(start_task, timeout=1.0)
        except asyncio.TimeoutError:
            start_task.cancel()

    async def test_flow_send_message_not_running(self, simple_flow):
        """Test sending message when flow is not running raises error."""
        with pytest.raises(RuntimeError, match="Flow is not running"):
            await simple_flow.send_message("Test message")

    async def test_flow_context_management(self, simple_flow):
        """Test flow context management."""
        flow = simple_flow
        context = {"key1": "value1", "key2": 42}

        start_task = asyncio.create_task(flow.start("Test", context=context, continuous=True))
        await asyncio.sleep(0.1)

        value1 = await flow.state.get_context("key1")
        value2 = await flow.state.get_context("key2")
        assert value1 == "value1"
        assert value2 == 42

        await flow.stop()
        try:
            await asyncio.wait_for(start_task, timeout=1.0)
        except asyncio.TimeoutError:
            start_task.cancel()

    async def test_flow_workspace_files(self, simple_flow):
        """Test flow workspace file operations."""
        flow = simple_flow

        await flow.workspace.write_file("test1.txt", "content1")
        await flow.workspace.write_file("test2.txt", "content2")

        files = await flow.get_workspace_files()
        assert "test1.txt" in files
        assert "test2.txt" in files

        txt_files = await flow.get_workspace_files("*.txt")
        assert len(txt_files) >= 2

    async def test_flow_state_export(self, simple_flow):
        """Test exporting flow state."""
        flow = simple_flow

        state_dict = await flow.export_state()
        assert state_dict["flow_id"]
        assert state_dict["flow_name"] == flow.name
        assert state_dict["workspace_path"] == str(flow.workspace.workspace_path)

        await flow.export_state("flow_state.json")
        assert await flow.workspace.file_exists("flow_state.json")

    async def test_flow_metrics(self, simple_flow):
        """Test getting flow metrics."""
        flow = simple_flow
        metrics = await flow.get_metrics()
        assert "enabled" in metrics

    async def test_flow_metrics_disabled(self, temp_workspace):
        """Test metrics when observability is disabled."""
        flow = Flow(
            name="test_flow",
            workspace_path=temp_workspace.workspace_path,
            enable_observability=False,
        )

        metrics = await flow.get_metrics()
        assert metrics["observability_disabled"]

    async def test_flow_wait_for_completion(self, simple_flow):
        """Test waiting for flow completion."""
        flow = simple_flow
        start_task = asyncio.create_task(flow.start("Test message", continuous=True))
        await asyncio.sleep(0.1)

        await flow.stop()
        completed = await flow.wait_for_completion(timeout=1.0)
        assert completed

        try:
            await start_task
        except Exception:
            pass

    async def test_flow_wait_for_completion_timeout(self, simple_flow):
        """Test wait for completion with timeout."""
        flow = simple_flow
        completed = await flow.wait_for_completion(timeout=0.1)
        assert completed

    async def test_flow_context_manager(self, temp_workspace):
        """Test flow as async context manager."""
        orchestrator = Orchestrator("ctx_orchestrator", initialize_llm=False)
        agent = SimpleAgent("test_agent")
        orchestrator.add_agent(agent)

        async with Flow("test_flow", workspace_path=temp_workspace.workspace_path) as flow:
            flow.add_orchestrator(orchestrator)

            start_task = asyncio.create_task(flow.start("Test message", continuous=True))
            await asyncio.sleep(0.1)
            assert flow.is_running()

        assert not flow.is_running()

        try:
            await start_task
        except Exception:
            pass

    async def test_flow_already_running_error(self, simple_flow):
        """Test starting flow when already running raises error."""
        flow = simple_flow

        start_task = asyncio.create_task(flow.start("Test message", continuous=True))
        await asyncio.sleep(0.1)

        with pytest.raises(RuntimeError, match="Flow is already running"):
            await flow.start("Another message")

        await flow.stop()
        try:
            await start_task
        except Exception:
            pass

    async def test_flow_auto_workspace_creation(self):
        """Test automatic workspace creation."""
        flow = Flow(
            name="auto_workspace_test",
            auto_create_workspace=True,
        )

        assert flow.workspace.workspace_path.exists()

        # Cleanup
        import shutil
        shutil.rmtree(flow.workspace.workspace_path)