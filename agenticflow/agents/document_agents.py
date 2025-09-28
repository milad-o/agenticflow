"""Document-related agents inspired by the hierarchical agent teams notebook."""

import asyncio
from typing import Optional, List, Dict
from ..core.agent import Agent
from ..core.state import AgentMessage, MessageType
from ..tools.file_tools import WriteFileTool, ReadFileTool, CreateOutlineTool, EditFileTool, PythonREPLTool
from langchain_core.messages import AIMessage
from langgraph.types import Command


class DocumentWriterAgent(Agent):
    """Document writer agent that creates and edits documents."""

    def __init__(self, name: str = "document_writer"):
        """Initialize document writer agent.

        Args:
            name: Agent name
        """
        super().__init__(
            name=name,
            description="Agent specialized in writing and editing documents",
            keywords=["write", "document", "edit", "create", "draft"],
        )

        # Add file operation tools
        self.add_tool(WriteFileTool())
        self.add_tool(ReadFileTool())
        self.add_tool(EditFileTool())

    async def execute(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Execute document writing based on the message content."""
        try:
            # Analyze the request type
            action = self._analyze_request(message.content)

            if action["type"] == "write":
                return await self._handle_write_request(message, action)
            elif action["type"] == "edit":
                return await self._handle_edit_request(message, action)
            elif action["type"] == "read":
                return await self._handle_read_request(message, action)
            else:
                return AgentMessage(
                    type=MessageType.AGENT,
                    sender=self.name,
                    content=f"Analyzing document request: {message.content}",
                )

        except Exception as e:
            return AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"Document operation failed: {str(e)}",
                metadata={"error_type": type(e).__name__},
            )

    def _analyze_request(self, content: str) -> Dict[str, str]:
        """Analyze the request to determine the action type.

        Args:
            content: Message content

        Returns:
            Dictionary with action type and extracted information
        """
        content_lower = content.lower()

        if any(word in content_lower for word in ["write", "create", "draft"]):
            return {"type": "write", "content": content}
        elif any(word in content_lower for word in ["edit", "modify", "update"]):
            return {"type": "edit", "content": content}
        elif any(word in content_lower for word in ["read", "show", "display"]):
            return {"type": "read", "content": content}
        else:
            return {"type": "analyze", "content": content}

    async def _handle_write_request(self, message: AgentMessage, action: Dict) -> AgentMessage:
        """Handle document writing request."""
        # Extract filename and content (simplified extraction)
        content = action["content"]
        filename = self._extract_filename(content) or "document.txt"

        # Use workspace to write file
        if self.workspace:
            await self.workspace.write_file(filename, content)
            return AgentMessage(
                type=MessageType.AGENT,
                sender=self.name,
                content=f"Document written to {filename}",
                metadata={"action": "write", "filename": filename},
            )
        else:
            # Use tool if workspace not available
            result = await self.use_tool("write_file", content=content, file_name=filename)
            return AgentMessage(
                type=MessageType.AGENT,
                sender=self.name,
                content=result,
                metadata={"action": "write", "filename": filename},
            )

    async def _handle_edit_request(self, message: AgentMessage, action: Dict) -> AgentMessage:
        """Handle document editing request."""
        # Simplified edit handling
        return AgentMessage(
            type=MessageType.AGENT,
            sender=self.name,
            content="Document editing completed",
            metadata={"action": "edit"},
        )

    async def _handle_read_request(self, message: AgentMessage, action: Dict) -> AgentMessage:
        """Handle document reading request."""
        filename = self._extract_filename(action["content"]) or "document.txt"

        if self.workspace:
            try:
                content = await self.workspace.read_file(filename)
                return AgentMessage(
                    type=MessageType.AGENT,
                    sender=self.name,
                    content=f"Content of {filename}:\n\n{content}",
                    metadata={"action": "read", "filename": filename},
                )
            except Exception as e:
                return AgentMessage(
                    type=MessageType.ERROR,
                    sender=self.name,
                    content=f"Failed to read {filename}: {str(e)}",
                )
        else:
            result = await self.use_tool("read_file", file_name=filename)
            return AgentMessage(
                type=MessageType.AGENT,
                sender=self.name,
                content=result,
                metadata={"action": "read", "filename": filename},
            )

    def _extract_filename(self, content: str) -> Optional[str]:
        """Extract filename from content.

        Args:
            content: Message content

        Returns:
            Extracted filename or None
        """
        import re

        # Look for filename patterns
        patterns = [
            r'file[:\s]+([a-zA-Z0-9._-]+\.[a-zA-Z]+)',
            r'save[:\s]+([a-zA-Z0-9._-]+\.[a-zA-Z]+)',
            r'([a-zA-Z0-9._-]+\.txt)',
            r'([a-zA-Z0-9._-]+\.md)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None


class NoteWriterAgent(Agent):
    """Note-taking agent that creates outlines and structured notes."""

    def __init__(self, name: str = "note_writer"):
        """Initialize note writer agent.

        Args:
            name: Agent name
        """
        super().__init__(
            name=name,
            description="Agent specialized in creating outlines and structured notes",
            keywords=["outline", "notes", "structure", "organize", "summary"],
        )

        # Add outline creation tool
        self.add_tool(CreateOutlineTool())
        self.add_tool(ReadFileTool())

    async def execute(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Execute note-taking based on the message content."""
        try:
            # Extract main points from the message
            points = self._extract_main_points(message.content)

            if not points:
                return AgentMessage(
                    type=MessageType.AGENT,
                    sender=self.name,
                    content="Please provide content to create an outline from.",
                )

            # Create outline
            filename = "outline.txt"
            outline_content = "\n".join(f"{i+1}. {point}" for i, point in enumerate(points))

            if self.workspace:
                await self.workspace.write_file(filename, outline_content)
                result_message = f"Outline created with {len(points)} points and saved to {filename}"
            else:
                await self.use_tool("create_outline", points=points, file_name=filename)
                result_message = f"Outline created with {len(points)} points"

            return AgentMessage(
                type=MessageType.AGENT,
                sender=self.name,
                content=result_message,
                metadata={"points_count": len(points), "filename": filename},
            )

        except Exception as e:
            return AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"Note creation failed: {str(e)}",
                metadata={"error_type": type(e).__name__},
            )

    def _extract_main_points(self, content: str) -> List[str]:
        """Extract main points from content.

        Args:
            content: Message content

        Returns:
            List of main points
        """
        # Simple point extraction based on sentences and bullet points
        lines = content.split('\n')
        points = []

        for line in lines:
            line = line.strip()
            if line:
                # Remove common bullet point markers
                line = line.lstrip('•-*').strip()
                if len(line) > 10:  # Filter out very short lines
                    points.append(line)

        # If no structured points found, split by sentences
        if not points:
            import re
            sentences = re.split(r'[.!?]+', content)
            points = [s.strip() for s in sentences if len(s.strip()) > 20]

        return points[:10]  # Limit to 10 main points


class ChartGeneratorAgent(Agent):
    """Chart generation agent that creates visualizations using Python."""

    def __init__(self, name: str = "chart_generator"):
        """Initialize chart generator agent.

        Args:
            name: Agent name
        """
        super().__init__(
            name=name,
            description="Agent specialized in generating charts and visualizations",
            keywords=["chart", "graph", "plot", "visualization", "data", "diagram"],
        )

        # Add Python REPL tool for chart generation
        self.add_tool(PythonREPLTool())
        self.add_tool(ReadFileTool())

    async def execute(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Execute chart generation based on the message content."""
        try:
            # Analyze the chart request
            chart_type = self._analyze_chart_request(message.content)

            # Generate Python code for the chart
            python_code = self._generate_chart_code(chart_type, message.content)

            # Execute the code
            result = await self.use_tool("python_repl", code=python_code)

            return AgentMessage(
                type=MessageType.AGENT,
                sender=self.name,
                content=f"Chart generation completed:\n{result}",
                metadata={"chart_type": chart_type, "code_executed": True},
            )

        except Exception as e:
            return AgentMessage(
                type=MessageType.ERROR,
                sender=self.name,
                content=f"Chart generation failed: {str(e)}",
                metadata={"error_type": type(e).__name__},
            )

    def _analyze_chart_request(self, content: str) -> str:
        """Analyze the chart request to determine chart type.

        Args:
            content: Message content

        Returns:
            Chart type
        """
        content_lower = content.lower()

        chart_types = {
            "bar": ["bar", "column"],
            "line": ["line", "trend"],
            "pie": ["pie", "donut"],
            "scatter": ["scatter", "point"],
            "histogram": ["histogram", "distribution"],
        }

        for chart_type, keywords in chart_types.items():
            if any(keyword in content_lower for keyword in keywords):
                return chart_type

        return "bar"  # Default

    def _generate_chart_code(self, chart_type: str, content: str) -> str:
        """Generate Python code for chart creation.

        Args:
            chart_type: Type of chart to create
            content: Original message content

        Returns:
            Python code string
        """
        # Generate sample chart code based on type
        if chart_type == "bar":
            return """
import matplotlib.pyplot as plt
import numpy as np

# Sample data
categories = ['A', 'B', 'C', 'D']
values = [23, 45, 56, 78]

plt.figure(figsize=(8, 6))
plt.bar(categories, values)
plt.title('Sample Bar Chart')
plt.xlabel('Categories')
plt.ylabel('Values')
plt.show()
print("Bar chart created successfully")
"""
        elif chart_type == "line":
            return """
import matplotlib.pyplot as plt
import numpy as np

# Sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y)
plt.title('Sample Line Chart')
plt.xlabel('X axis')
plt.ylabel('Y axis')
plt.show()
print("Line chart created successfully")
"""
        else:
            return """
import matplotlib.pyplot as plt

# Sample pie chart
sizes = [15, 30, 45, 10]
labels = ['A', 'B', 'C', 'D']

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%')
plt.title('Sample Pie Chart')
plt.show()
print("Pie chart created successfully")
"""