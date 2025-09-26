"""
Analysis Agent - Fast CSV Analytics and Data Processing

Provides analysis agents optimized for data processing, especially CSV analytics.
Uses chunked processing to handle large files efficiently without loading everything into memory.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from ..base import Agent
from ..roles import AgentRole

if TYPE_CHECKING:
    from agenticflow.core.config import AgentConfig


class AnalysisAgentRules:
    def get_rules_text(self) -> str:
        return """📊 ANALYSIS AGENT - FAST DATA PROCESSING

MISSION: Compute aggregates and analyze data efficiently with minimal memory usage.

APPROACH:
✅ Chunked processing for large files
✅ Direct tool execution for performance
✅ Memory-efficient aggregations
✅ Structured output for downstream processing

ANALYSIS PATTERNS:
- CSV aggregation: Use csv_chunk_aggregate for group-by operations
- Statistical analysis: Compute means, sums, counts per category
- Memory management: Process files in chunks, not all at once
- Output format: Structured results for easy consumption

TOOL PREFERENCES:
- csv_chunk_aggregate: For computing group-wise statistics
- pandas_chunk_aggregate: Alternative for complex operations
- file_stat: For metadata and validation

ERROR RECOVERY:
- File not found → Validate path and try alternatives
- Memory issues → Reduce chunk size
- Format errors → Skip invalid rows and continue

COMPLETION CRITERIA:
✅ Aggregations computed successfully
✅ Results in structured format
✅ Memory usage kept reasonable
✅ Clear summary of processed data"""


class AnalysisAgent(Agent):
    """
    Fast data analysis agent specialized in CSV analytics.

    Features:
    - Direct tool execution avoiding unnecessary LLM calls
    - Chunked CSV processing for large files
    - Group-wise aggregations
    - Memory efficient processing
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        name: str = "analysis_agent",
        max_attempts: int = 2,
        csv_path: Optional[str] = None,
        group_by: Optional[str] = None,
        value_column: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs
    ):
        """
        Initialize Analysis Agent.

        Args:
            llm: LangChain LLM instance for reflection (optional)
            tools: List of tools to use
            name: Agent identifier
            max_attempts: Maximum retry attempts
            csv_path: Default CSV file path to analyze
            group_by: Default grouping column
            value_column: Default value column for aggregations
            temperature: LLM temperature (0.0 for deterministic analysis)
        """
        from agenticflow.core.config import AgentConfig
        config = AgentConfig(
            name=name,
            model="",  # Model name not needed when LLM instance is provided
            temperature=temperature,
            role=AgentRole.ANALYST if hasattr(AgentRole, "ANALYST") else AgentRole.REPORTER,
            capabilities=["data_analysis", "csv_aggregate"],
            system_prompt=(
                "You are a fast data analysis agent specialized in CSV analytics.\n"
                "Prefer direct tool execution and avoid unnecessary LLM calls."
            ),
            rules=AnalysisAgentRules(),
        )

        # Initialize parent with LangChain LLM
        super().__init__(
            config=config,
            tools=tools,
            model=llm,
            max_attempts=max_attempts,
            use_llm_reflection=False,
            use_llm_verification=False,
            **kwargs
        )

        self.static_resources.update(
            {
                "csv_path": csv_path or "",
                "group_by": group_by or "",
                "value_column": value_column or "",
            }
        )

        # Disable auto discovery; demo will adopt tools explicitly
        try:
            setattr(self, "auto_discover", False)
        except Exception:
            pass