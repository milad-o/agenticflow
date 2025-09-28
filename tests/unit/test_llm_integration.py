"""Integration tests for LLM-powered functionalities."""

import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import patch, AsyncMock

from agenticflow import Flow, Orchestrator, Supervisor
from agenticflow.agents.research_agents import SearchAgent, WebScraperAgent
from agenticflow.agents.document_agents import DocumentWriterAgent, NoteWriterAgent, ChartGeneratorAgent
from agenticflow.core.state import MessageType
from agenticflow.workspace.workspace import Workspace


@pytest.mark.asyncio
class TestLLMIntegration:
    """Test LLM integration and specialized agents."""

    async def test_search_agent_with_mock_api(self):
        """Test search agent with mocked Tavily API."""
        # Mock the Tavily search
        with patch('tavily.TavilyClient') as mock_client_class:
            from unittest.mock import Mock
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.search.return_value = {
                "results": [
                    {
                        "title": "Test Result",
                        "url": "https://example.com",
                        "content": "This is test content about AI agents."
                    }
                ]
            }

            from agenticflow.core.state import AgentMessage, MessageType

            agent = SearchAgent()
            input_message = AgentMessage(
                type=MessageType.USER,
                sender="user",
                content="search for AI agents"
            )
            message = await agent.process_message(input_message)

            assert message.type == MessageType.AGENT
            assert "AI agents" in message.content
            assert "Test Result" in message.content

    async def test_document_writer_agent_with_workspace(self):
        """Test document writer agent with workspace integration."""
        temp_dir = tempfile.mkdtemp()
        try:
            workspace = Workspace(temp_dir)
            agent = DocumentWriterAgent()
            agent.workspace = workspace

            # Test writing a document
            from agenticflow.core.state import AgentMessage
            message = AgentMessage(
                sender="user",
                content="Write a document about machine learning to ml_doc.txt"
            )

            response = await agent.process_message(message)

            assert response.type == MessageType.AGENT
            assert "ml_doc.txt" in response.content

            # Verify file was created
            files = await workspace.list_files()
            assert "ml_doc.txt" in files

        finally:
            shutil.rmtree(temp_dir)

    async def test_research_team_workflow(self):
        """Test a complete research team workflow."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create flow with research team
            flow = Flow("research_flow", workspace_path=temp_dir)

            # Create research team
            research_team = Supervisor("research_team", keywords=["research"])
            search_agent = SearchAgent()
            scraper_agent = WebScraperAgent()

            research_team.add_agent(search_agent).add_agent(scraper_agent)

            # Create orchestrator
            orchestrator = Orchestrator()
            orchestrator.add_team(research_team)

            flow.add_orchestrator(orchestrator)

            # Mock the external APIs
            with patch('tavily.TavilyClient') as mock_tavily, \
                 patch('aiohttp.ClientSession') as mock_session:

                # Mock Tavily
                from unittest.mock import Mock
                mock_client = Mock()
                mock_tavily.return_value = mock_client
                mock_client.search.return_value = {"results": []}

                # Mock web scraping
                mock_session_instance = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_session_instance

                # Start flow
                start_task = asyncio.create_task(
                    flow.start("Research information about AI safety")
                )

                await asyncio.sleep(0.3)  # Let it process

                # Get messages
                messages = await flow.get_messages()
                assert len(messages) >= 1

                # Check that research team processed the message
                agent_responses = [msg for msg in messages if msg.type == MessageType.AGENT]
                assert len(agent_responses) >= 1

                await flow.stop()
                try:
                    await start_task
                except:
                    pass

        finally:
            shutil.rmtree(temp_dir)

    async def test_document_team_workflow(self):
        """Test a complete document writing team workflow."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create flow with document team
            flow = Flow("document_flow", workspace_path=temp_dir)

            # Create document team
            doc_team = Supervisor("document_team", keywords=["write", "document"])
            writer_agent = DocumentWriterAgent()
            note_agent = NoteWriterAgent()

            # Set workspace for agents
            writer_agent.workspace = flow.workspace
            note_agent.workspace = flow.workspace

            doc_team.add_agent(writer_agent).add_agent(note_agent)

            # Create orchestrator
            orchestrator = Orchestrator()
            orchestrator.add_team(doc_team)

            flow.add_orchestrator(orchestrator)

            # Start flow
            start_task = asyncio.create_task(
                flow.start("Create a document about AI ethics with outline")
            )

            await asyncio.sleep(0.3)  # Let it process

            # Check that files were created
            files = await flow.get_workspace_files()
            assert len(files) >= 1

            # Get status
            status = await orchestrator.get_status()
            assert "document_team" in status["teams"]

            await flow.stop()
            try:
                await start_task
            except:
                pass

        finally:
            shutil.rmtree(temp_dir)

    async def test_chart_generator_with_mock_repl(self):
        """Test chart generator with mocked Python REPL."""
        with patch('langchain_experimental.utilities.PythonREPL') as mock_repl_class:
            mock_repl = AsyncMock()
            mock_repl_class.return_value = mock_repl
            mock_repl.run.return_value = "Chart created successfully"

            agent = ChartGeneratorAgent()

            from agenticflow.core.state import AgentMessage
            message = AgentMessage(
                sender="user",
                content="Create a bar chart showing sales data"
            )

            response = await agent.process_message(message)

            assert response.type == MessageType.AGENT
            assert "Chart generation completed" in response.content

    async def test_web_scraper_url_extraction(self):
        """Test web scraper agent URL extraction."""
        agent = WebScraperAgent()

        from agenticflow.core.state import AgentMessage
        message = AgentMessage(
            sender="user",
            content="Please scrape these pages: https://example.com and https://test.com"
        )

        # Mock the web scraping
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "<html><body>Test content</body></html>"

            mock_session_instance.get.return_value.__aenter__.return_value = mock_response

            with patch('bs4.BeautifulSoup') as mock_soup:
                mock_soup_instance = AsyncMock()
                mock_soup.return_value = mock_soup_instance
                mock_soup_instance.get_text.return_value = "Scraped test content"

                response = await agent.process_message(message)

                assert response.type == MessageType.AGENT
                assert "2 URL(s)" in response.content
                assert response.metadata["url_count"] == 2

    async def test_note_writer_point_extraction(self):
        """Test note writer agent point extraction."""
        temp_dir = tempfile.mkdtemp()
        try:
            workspace = Workspace(temp_dir)
            agent = NoteWriterAgent()
            agent.workspace = workspace

            from agenticflow.core.state import AgentMessage
            message = AgentMessage(
                sender="user",
                content="""
                Here are the key points about AI:
                • Machine learning is a subset of AI
                • Deep learning uses neural networks
                • AI can be applied to many domains
                • Ethical considerations are important
                """
            )

            response = await agent.process_message(message)

            assert response.type == MessageType.AGENT
            assert "outline.txt" in response.content
            assert response.metadata["points_count"] >= 3

            # Check file was created
            files = await workspace.list_files()
            assert "outline.txt" in files

        finally:
            shutil.rmtree(temp_dir)

    async def test_hierarchical_workflow_with_observability(self):
        """Test hierarchical workflow with full observability."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create flow with observability
            flow = Flow("hierarchical_flow", workspace_path=temp_dir, enable_observability=True)

            # Create research team
            research_team = Supervisor("research_team")
            research_team.add_agent(SearchAgent())

            # Create document team
            doc_team = Supervisor("document_team")
            doc_team.add_agent(DocumentWriterAgent())

            # Create top-level orchestrator
            orchestrator = Orchestrator()
            orchestrator.add_team(research_team).add_team(doc_team)

            flow.add_orchestrator(orchestrator)

            # Mock external APIs
            with patch('tavily.TavilyClient') as mock_tavily:
                from unittest.mock import Mock
                mock_client = Mock()
                mock_tavily.return_value = mock_client
                mock_client.search.return_value = {"results": []}

                # Start flow
                start_task = asyncio.create_task(
                    flow.start("Research AI and write a summary")
                )

                await asyncio.sleep(0.3)

                # Check observability metrics
                metrics = await flow.get_metrics()
                assert metrics["enabled"]

                # Get recent events
                if flow.observer:
                    events = flow.observer.get_recent_events(limit=10)
                    assert len(events) >= 1

                await flow.stop()
                try:
                    await start_task
                except:
                    pass

        finally:
            shutil.rmtree(temp_dir)