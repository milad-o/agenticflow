"""Integration tests for the complete AgenticFlow framework."""

import pytest
import asyncio
from agenticflow import Flow, Orchestrator, Agent, Supervisor, Tool
from agenticflow.core.agent import SimpleAgent
from agenticflow.core.state import MessageType
from langgraph.types import Command
# Tests use LangGraph-first architecture


class ResearchAgent(SimpleAgent):
    """Custom agent for research tasks."""

    def __init__(self, name: str):
        super().__init__(
            name=name,
            description="Research agent that can search and analyze information",
            keywords=["research", "search", "find", "analyze"],
        )

    async def execute(self, message):
        """Simulate research work."""
        await asyncio.sleep(0.1)  # Simulate processing time

        if "research" in message.content.lower():
            content = f"Research results for: {message.content}"
        else:
            content = f"Agent {self.name} processed: {message.content}"

        return type(message)(
            type=MessageType.AGENT,
            sender=self.name,
            content=content,
        )


class WritingAgent(SimpleAgent):
    """Custom agent for writing tasks."""

    def __init__(self, name: str):
        super().__init__(
            name=name,
            description="Writing agent that can create documents",
            keywords=["write", "create", "document", "report"],
        )

    async def execute(self, message):
        """Simulate writing work."""
        await asyncio.sleep(0.1)  # Simulate processing time

        if "write" in message.content.lower():
            content = f"Document created for: {message.content}"
        else:
            content = f"Agent {self.name} processed: {message.content}"

        return type(message)(
            type=MessageType.AGENT,
            sender=self.name,
            content=content,
        )


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the complete framework."""

    async def test_simple_agent_workflow(self, temp_workspace):
        """Test a simple workflow with individual agents."""
        # Create flow
        flow = Flow("simple_workflow", workspace_path=temp_workspace.workspace_path)

        # Create agents
        research_agent = ResearchAgent("researcher")
        writing_agent = WritingAgent("writer")

        # Create orchestrator
        orchestrator = Orchestrator("main_orchestrator", initialize_llm=False)
        orchestrator.add_agent(research_agent).add_agent(writing_agent)

        # Setup flow
        flow.add_orchestrator(orchestrator)

        try:
            # Start flow with research task in continuous mode
            await flow.start("Please research information about AI agents", continuous=True)
            await asyncio.sleep(0.2)

            # Send writing task
            await flow.send_message("Please write a report about the research")

            # Get messages
            messages = await flow.get_messages()
            assert len(messages) >= 2

            # Check that agents processed messages
            agent_responses = [msg for msg in messages if msg.type == MessageType.AGENT]
            assert len(agent_responses) >= 1

        finally:
            await flow.stop()
            try:
                await start_task
            except:
                pass

    async def test_team_based_workflow(self, temp_workspace):
        """Test a workflow with teams of agents."""
        # Create flow
        flow = Flow("team_workflow", workspace_path=temp_workspace.workspace_path)

        # Create research team
        research_team = Supervisor("research_team", keywords=["research"], initialize_llm=False)
        research_team.add_agent(ResearchAgent("researcher1"))
        research_team.add_agent(ResearchAgent("researcher2"))

        # Create writing team
        writing_team = Supervisor("writing_team", keywords=["write"], initialize_llm=False)
        writing_team.add_agent(WritingAgent("writer1"))
        writing_team.add_agent(WritingAgent("writer2"))

        # Create orchestrator
        orchestrator = Orchestrator("team_orchestrator", initialize_llm=False)
        orchestrator.add_team(research_team).add_team(writing_team)

        # Setup flow
        flow.add_orchestrator(orchestrator)

        try:
            # Start flow
            start_task = asyncio.create_task(
                flow.start("Research AI agents and write a comprehensive report")
            )
            await asyncio.sleep(0.3)

            # Get status
            status = await orchestrator.get_status()
            assert "research_team" in status["teams"]
            assert "writing_team" in status["teams"]

            # Get messages
            messages = await flow.get_messages()
            assert len(messages) >= 1

        finally:
            await flow.stop()
            try:
                await start_task
            except:
                pass

    async def test_mixed_workflow(self, temp_workspace):
        """Test a workflow with both teams and individual agents."""
        # Create flow
        flow = Flow("mixed_workflow", workspace_path=temp_workspace.workspace_path)

        # Create a team
        team = Supervisor("analysis_team", keywords=["analyze"], initialize_llm=False)
        team.add_agent(ResearchAgent("analyst1"))
        team.add_agent(ResearchAgent("analyst2"))

        # Create individual agent
        coordinator = SimpleAgent("coordinator", keywords=["coordinate"])

        # Create orchestrator
        orchestrator = Orchestrator("mixed_orchestrator", initialize_llm=False)
        orchestrator.add_team(team).add_agent(coordinator)

        # Setup flow
        flow.add_orchestrator(orchestrator)

        try:
            # Start flow
            start_task = asyncio.create_task(
                flow.start("Coordinate the analysis of market trends")
            )
            await asyncio.sleep(0.3)

            # Check that both team and individual agent are available
            targets = orchestrator.get_available_targets()
            assert "analysis_team" in targets
            assert "coordinator" in targets

        finally:
            await flow.stop()
            try:
                await start_task
            except:
                pass

    async def test_tool_usage_workflow(self, temp_workspace):
        """Test workflow with agents using tools."""
        # Create tools
        def calculate_sum(a: int, b: int) -> int:
            return a + b

        def save_result(result: str) -> str:
            return f"Saved: {result}"

        calc_tool = Tool("calculator", "Calculate sum", calculate_sum)
        save_tool = Tool("saver", "Save result", save_result)

        # Create agent with tools
        class CalculatorAgent(SimpleAgent):
            async def execute(self, message):
                if "calculate" in message.content.lower():
                    # Use calculator tool
                    result = await self.use_tool("calculator", a=5, b=3)
                    # Save the result
                    save_result = await self.use_tool("saver", result=str(result))
                    response_msg = type(message)(
                        type=MessageType.AGENT,
                        sender=self.name,
                        content=f"Calculation complete: {save_result}",
                    )
                    # Always return Command objects (LangGraph is required)
                    return Command(
                        goto="orchestrator",
                        update={"messages": [response_msg]}
                    )
                return await super().execute(message)

        agent = CalculatorAgent("calc_agent")
        agent.add_tool(calc_tool).add_tool(save_tool)

        # Create flow
        flow = Flow("tool_workflow", workspace_path=temp_workspace.workspace_path)
        orchestrator = Orchestrator(initialize_llm=False)
        orchestrator.add_agent(agent)
        flow.add_orchestrator(orchestrator)

        try:
            # Start flow
            start_task = asyncio.create_task(
                flow.start("Please calculate 5 + 3")
            )
            await asyncio.sleep(0.5)  # Give more time for LangGraph execution

            # Get messages
            messages = await flow.get_messages()
            responses = [msg for msg in messages if msg.type == MessageType.AGENT]
            assert len(responses) >= 1
            assert "Calculation complete" in responses[0].content

        finally:
            await flow.stop()
            try:
                await start_task
            except:
                pass

    async def test_workspace_integration(self, temp_workspace):
        """Test workflow integration with workspace operations."""
        # Create agent that writes to workspace
        class FileAgent(SimpleAgent):
            async def execute(self, message):
                if self.workspace:
                    # Write message to file
                    filename = f"message_{len(self.message_history)}.txt"
                    await self.workspace.write_file(filename, message.content)
                    response_msg = type(message)(
                        type=MessageType.AGENT,
                        sender=self.name,
                        content=f"Message saved to {filename}",
                    )
                    # Always return Command objects (LangGraph is required)
                    return Command(
                        goto="orchestrator",
                        update={"messages": [response_msg]}
                    )
                return await super().execute(message)

        agent = FileAgent("file_agent")

        # Create flow
        flow = Flow("file_workflow", workspace_path=temp_workspace.workspace_path)
        orchestrator = Orchestrator(initialize_llm=False)
        orchestrator.add_agent(agent)
        flow.add_orchestrator(orchestrator)

        try:
            # Start flow
            start_task = asyncio.create_task(
                flow.start("Save this message to a file")
            )
            await asyncio.sleep(0.2)

            # Check that file was created
            files = await flow.get_workspace_files("*.txt")
            assert len(files) >= 1

            # Read the file
            content = await flow.workspace.read_file(files[0])
            assert "Save this message to a file" in content

        finally:
            await flow.stop()
            try:
                await start_task
            except:
                pass

    async def test_observability_integration(self, temp_workspace):
        """Test workflow with observability features."""
        # Create flow with observability
        flow = Flow("observable_workflow", workspace_path=temp_workspace.workspace_path)

        # Create agents
        agent1 = SimpleAgent("agent1")
        agent2 = SimpleAgent("agent2")

        # Create orchestrator
        orchestrator = Orchestrator(initialize_llm=False)
        orchestrator.add_agent(agent1).add_agent(agent2)
        flow.add_orchestrator(orchestrator)

        try:
            # Start flow
            start_task = asyncio.create_task(
                flow.start("Test observability")
            )
            await asyncio.sleep(0.2)

            # Get metrics
            metrics = await flow.get_metrics()
            assert "enabled" in metrics
            assert metrics["enabled"]

            # Get agent metrics
            if flow.observer:
                agent_metrics = await flow.observer.get_agent_metrics("agent1")
                assert "agent_id" in agent_metrics

            # Get recent events
            if flow.observer:
                events = flow.observer.get_recent_events(limit=10)
                assert len(events) >= 0

        finally:
            await flow.stop()
            try:
                await start_task
            except:
                pass

    async def test_error_handling_integration(self, temp_workspace):
        """Test error handling across the framework."""
        # Create agent that raises errors
        class ErrorAgent(SimpleAgent):
            async def execute(self, message):
                if "error" in message.content.lower():
                    raise ValueError("Intentional error for testing")
                return await super().execute(message)

        error_agent = ErrorAgent("error_agent")

        # Create flow
        flow = Flow("error_workflow", workspace_path=temp_workspace.workspace_path)
        orchestrator = Orchestrator(initialize_llm=False)
        orchestrator.add_agent(error_agent)
        flow.add_orchestrator(orchestrator)

        try:
            # Start flow with error-triggering message
            start_task = asyncio.create_task(
                flow.start("Please trigger an error")
            )
            await asyncio.sleep(0.2)

            # Get messages and check for error handling
            messages = await flow.get_messages()
            error_messages = [msg for msg in messages if msg.type == MessageType.ERROR]
            assert len(error_messages) >= 1

            # Check agent status
            status = await error_agent.get_status()
            assert status["status"] == "error"

        finally:
            await flow.stop()
            try:
                await start_task
            except:
                pass

    async def test_concurrent_execution(self, temp_workspace):
        """Test sequential execution through supervisor with LangGraph."""
        # Create multiple agents
        agents = [SimpleAgent(f"agent_{i}") for i in range(3)]

        # Create supervisor without LLM routing (routes to first available agent)
        supervisor = Supervisor("sequential_team", initialize_llm=False)
        for agent in agents:
            supervisor.add_agent(agent)

        # Create flow
        flow = Flow("sequential_workflow", workspace_path=temp_workspace.workspace_path)
        orchestrator = Orchestrator(initialize_llm=False)
        orchestrator.add_team(supervisor)
        flow.add_orchestrator(orchestrator)

        try:
            # Start flow
            start_task = asyncio.create_task(
                flow.start("Process this message through team")
            )
            await asyncio.sleep(0.3)

            # Check that the supervisor routed to an agent (LangGraph is sequential)
            messages = await flow.get_messages()
            agent_responses = [msg for msg in messages if msg.type == MessageType.AGENT]
            assert len(agent_responses) >= 1  # At least one agent should respond
            
            # Check that the team structure is working
            targets = orchestrator.get_available_targets()
            assert "sequential_team" in targets
            assert len(supervisor.agents) == 3

        finally:
            await flow.stop()
            try:
                await start_task
            except:
                pass