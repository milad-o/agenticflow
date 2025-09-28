"""Performance tests for the AgenticFlow framework."""

import pytest
import asyncio
import time
import tempfile
import shutil
from unittest.mock import patch, AsyncMock

from agenticflow import Flow, Orchestrator, Supervisor
from agenticflow.core.agent import SimpleAgent
from agenticflow.core.state import AgentMessage, MessageType
from agenticflow.agents.research_agents import SearchAgent
from agenticflow.agents.document_agents import DocumentWriterAgent


@pytest.mark.asyncio
class TestPerformance:
    """Performance tests for the framework."""

    async def test_agent_response_time(self):
        """Test agent response time under normal conditions."""
        agent = SimpleAgent("perf_agent")

        message = AgentMessage(sender="user", content="Test message")

        start_time = time.time()
        response = await agent.process_message(message)
        end_time = time.time()

        response_time = end_time - start_time

        assert response is not None
        assert response_time < 1.0  # Should respond within 1 second

    async def test_concurrent_agent_processing(self):
        """Test concurrent processing of multiple agents."""
        # Create multiple agents
        agents = [SimpleAgent(f"agent_{i}") for i in range(10)]

        message = AgentMessage(sender="user", content="Concurrent test")

        start_time = time.time()

        # Process messages concurrently
        tasks = [agent.process_message(message) for agent in agents]
        responses = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # All agents should respond
        assert len(responses) == 10
        assert all(r is not None for r in responses)

        # Concurrent processing should be faster than sequential
        assert total_time < 5.0  # Should complete within 5 seconds

    async def test_supervisor_team_performance(self):
        """Test supervisor performance with multiple agents."""
        # Create broadcast routing strategy for all agents to process message
        from agenticflow.core.supervisor import RoutingStrategy

        class BroadcastRouting(RoutingStrategy):
            async def route(self, message, agents):
                return None  # Always broadcast to all agents

        supervisor = Supervisor("perf_team", max_concurrent_agents=5, routing_strategy=BroadcastRouting())

        # Add multiple agents
        for i in range(10):
            agent = SimpleAgent(f"team_agent_{i}")
            supervisor.add_agent(agent)

        message = AgentMessage(sender="user", content="Team performance test")

        start_time = time.time()
        response = await supervisor.process_message(message)
        end_time = time.time()

        processing_time = end_time - start_time

        assert response is not None
        assert len(supervisor.completion_order) == 10
        assert processing_time < 10.0  # Should complete within 10 seconds

    async def test_workspace_file_operations_performance(self):
        """Test workspace file operations performance."""
        temp_dir = tempfile.mkdtemp()
        try:
            from agenticflow.workspace.workspace import Workspace
            workspace = Workspace(temp_dir)

            # Test writing multiple files
            start_time = time.time()

            write_tasks = []
            for i in range(100):
                task = workspace.write_file(f"file_{i}.txt", f"Content {i}")
                write_tasks.append(task)

            await asyncio.gather(*write_tasks)

            write_time = time.time() - start_time

            # Test reading multiple files
            start_time = time.time()

            read_tasks = []
            for i in range(100):
                task = workspace.read_file(f"file_{i}.txt")
                read_tasks.append(task)

            contents = await asyncio.gather(*read_tasks)

            read_time = time.time() - start_time

            # Verify all operations completed
            assert len(contents) == 100
            assert all("Content" in content for content in contents)

            # Performance benchmarks
            assert write_time < 5.0  # Writing 100 files should take < 5 seconds
            assert read_time < 5.0   # Reading 100 files should take < 5 seconds

        finally:
            shutil.rmtree(temp_dir)

    async def test_flow_message_throughput(self):
        """Test flow message processing throughput."""
        temp_dir = tempfile.mkdtemp()
        try:
            flow = Flow("throughput_test", workspace_path=temp_dir)

            # Create simple orchestrator with one agent
            agent = SimpleAgent("throughput_agent")
            orchestrator = Orchestrator()
            orchestrator.add_agent(agent)
            flow.add_orchestrator(orchestrator)

            # Start flow
            start_task = asyncio.create_task(flow.start("Initial message", continuous=True))
            await asyncio.sleep(0.1)

            # Send multiple messages rapidly
            start_time = time.time()

            message_tasks = []
            for i in range(50):
                task = flow.send_message(f"Message {i}")
                message_tasks.append(task)

            await asyncio.gather(*message_tasks)

            end_time = time.time()
            throughput_time = end_time - start_time

            # Check messages were processed
            messages = await flow.get_messages()
            assert len(messages) >= 50

            # Performance benchmark
            assert throughput_time < 10.0  # Should handle 50 messages in < 10 seconds

            await flow.stop()
            try:
                await start_task
            except:
                pass

        finally:
            shutil.rmtree(temp_dir)

    async def test_memory_usage_with_large_state(self):
        """Test memory usage with large state and message history."""
        temp_dir = tempfile.mkdtemp()
        try:
            flow = Flow("memory_test", workspace_path=temp_dir)

            agent = SimpleAgent("memory_agent")
            orchestrator = Orchestrator()
            orchestrator.add_agent(agent)
            flow.add_orchestrator(orchestrator)

            # Start flow
            start_task = asyncio.create_task(flow.start("Memory test", continuous=True))
            await asyncio.sleep(0.1)

            # Generate large number of messages
            for i in range(100):  # Reduced from 1000 to 100 for faster tests
                await flow.send_message(f"Large message {i} with lots of content " * 10)

                # Process in batches to avoid overwhelming
                if i % 50 == 0:
                    await asyncio.sleep(0.1)

            # Check state size
            messages = await flow.get_messages()
            assert len(messages) >= 100

            # Export state (this tests serialization performance)
            start_time = time.time()
            state_export = await flow.export_state()
            export_time = time.time() - start_time

            assert "state" in state_export
            assert export_time < 5.0  # Export should be fast even with large state

            await flow.stop()
            try:
                await start_task
            except:
                pass

        finally:
            shutil.rmtree(temp_dir)

    async def test_observability_overhead(self):
        """Test observability overhead on performance."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Test with observability enabled
            flow_with_obs = Flow("obs_test", workspace_path=temp_dir, enable_observability=True)
            agent_with_obs = SimpleAgent("obs_agent")
            orchestrator_with_obs = Orchestrator()
            orchestrator_with_obs.add_agent(agent_with_obs)
            flow_with_obs.add_orchestrator(orchestrator_with_obs)

            # Test without observability
            flow_without_obs = Flow("no_obs_test", workspace_path=temp_dir, enable_observability=False)
            agent_without_obs = SimpleAgent("no_obs_agent")
            orchestrator_without_obs = Orchestrator()
            orchestrator_without_obs.add_agent(agent_without_obs)
            flow_without_obs.add_orchestrator(orchestrator_without_obs)

            # Measure performance with observability
            start_time = time.time()
            start_task_obs = asyncio.create_task(flow_with_obs.start("Observability test", continuous=True))
            await asyncio.sleep(0.1)

            for i in range(10):  # Reduced from 50 to 10 for faster tests
                await flow_with_obs.send_message(f"Message {i}")

            await flow_with_obs.stop()
            try:
                await start_task_obs
            except:
                pass
            time_with_obs = time.time() - start_time

            # Measure performance without observability
            start_time = time.time()
            start_task_no_obs = asyncio.create_task(flow_without_obs.start("No observability test", continuous=True))
            await asyncio.sleep(0.1)

            for i in range(10):  # Reduced from 50 to 10 for faster tests
                await flow_without_obs.send_message(f"Message {i}")

            await flow_without_obs.stop()
            try:
                await start_task_no_obs
            except:
                pass
            time_without_obs = time.time() - start_time

            # Observability overhead should be minimal (< 50% slowdown)
            overhead_ratio = time_with_obs / time_without_obs
            assert overhead_ratio < 1.5

        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.parametrize("agent_count", [5, 10, 20])
    async def test_scalability_with_agent_count(self, agent_count):
        """Test framework scalability with varying agent counts."""
        temp_dir = tempfile.mkdtemp()
        try:
            flow = Flow(f"scale_test_{agent_count}", workspace_path=temp_dir)

            # Create supervisor with multiple agents
            supervisor = Supervisor(f"scale_team_{agent_count}")
            for i in range(agent_count):
                agent = SimpleAgent(f"scale_agent_{i}")
                supervisor.add_agent(agent)

            orchestrator = Orchestrator()
            orchestrator.add_team(supervisor)
            flow.add_orchestrator(orchestrator)

            # Measure processing time
            start_time = time.time()

            start_task = asyncio.create_task(flow.start("Scalability test", continuous=True))
            await asyncio.sleep(0.2)

            # Send test message
            await flow.send_message("Process this message")
            await asyncio.sleep(0.5)  # Allow processing time

            end_time = time.time()
            processing_time = end_time - start_time

            # Get team status
            status = await supervisor.get_status()
            completed_agents = len(status.get("completion_order", []))

            # Verify all agents processed the message
            assert completed_agents == agent_count

            # Processing time should scale reasonably (not exponentially)
            # With 20 agents, should still complete within 10 seconds
            assert processing_time < 10.0

            await flow.stop()
            try:
                await start_task
            except:
                pass

        finally:
            shutil.rmtree(temp_dir)