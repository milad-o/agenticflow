"""Unit tests for Flow core functionality."""

import pytest
import asyncio
from pathlib import Path

from agenticflow import Flow, Orchestrator, Supervisor, SimpleAgent


class TestFlow:
    """Test cases for Flow class."""

    def test_flow_creation(self):
        """Test basic flow creation."""
        flow = Flow("test_flow")
        assert flow.name == "test_flow"
        assert flow.orchestrator is None
        assert not flow._running

    def test_flow_with_workspace(self, temp_workspace):
        """Test flow creation with workspace."""
        flow = Flow("test_flow", workspace_path=str(temp_workspace))
        assert flow.workspace is not None
        assert flow.workspace.path == temp_workspace

    def test_add_orchestrator(self):
        """Test adding orchestrator to flow."""
        flow = Flow("test_flow")
        orchestrator = Orchestrator("test_orchestrator", initialize_llm=False)
        
        flow.add_orchestrator(orchestrator)
        assert flow.orchestrator == orchestrator
        assert orchestrator.flow == flow

    def test_flow_method_chaining(self):
        """Test method chaining on flow."""
        flow = (Flow("test_flow")
                .add_orchestrator(Orchestrator("test_orchestrator", initialize_llm=False)))
        
        assert flow.name == "test_flow"
        assert flow.orchestrator.name == "test_orchestrator"

    @pytest.mark.asyncio
    async def test_flow_start_without_orchestrator(self):
        """Test starting flow without orchestrator raises error."""
        flow = Flow("test_flow")
        
        with pytest.raises(ValueError, match="No orchestrator configured"):
            await flow.start("test message")

    @pytest.mark.asyncio
    async def test_flow_start_simple(self, simple_flow):
        """Test starting a simple flow."""
        flow = simple_flow
        
        # This should not raise an error
        await flow.start("test message")
        
        # Check that flow state was updated
        assert flow.state is not None
        assert len(flow.state.messages) > 0

    def test_flow_context_manager(self):
        """Test flow as context manager."""
        with Flow("test_flow") as flow:
            assert flow.name == "test_flow"
            assert not flow._running

    @pytest.mark.asyncio
    async def test_flow_async_context_manager(self):
        """Test flow as async context manager."""
        async with Flow("test_flow") as flow:
            assert flow.name == "test_flow"
            assert not flow._running

    def test_flow_str_representation(self):
        """Test string representation of flow."""
        flow = Flow("test_flow")
        flow_str = str(flow)
        assert "test_flow" in flow_str
        assert "Flow" in flow_str

    def test_flow_repr(self):
        """Test repr of flow."""
        flow = Flow("test_flow")
        flow_repr = repr(flow)
        assert "test_flow" in flow_repr
        assert "Flow" in flow_repr
