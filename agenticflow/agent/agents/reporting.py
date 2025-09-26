"""
Reporting Agent - Fast and Professional Report Generation

Provides reporting agents optimized for generating high-quality reports quickly.
All agents use the Hybrid RPAVH approach combining template-based generation with selective LLM usage.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from ..base import Agent
from ..roles import AgentRole

if TYPE_CHECKING:
    from agenticflow.core.config import AgentConfig


class ReportingAgentRules:
    """Optimized rules for fast report generation."""

    def get_rules_text(self) -> str:
        return """📊 REPORTING AGENT - FAST & PROFESSIONAL

MISSION: Generate high-quality reports quickly using rule-based content assembly.

APPROACH:
✅ Template-based report structure
✅ Direct content generation from data
✅ Minimal LLM overhead for speed
✅ Smart content organization

REPORT STRUCTURE:
1. Executive Summary (auto-generated from key data)
2. Data Overview (file counts, sizes, types)
3. Key Findings (extracted from content analysis)
4. Detailed Analysis (structured data presentation)
5. Conclusion (summary of outcomes)

CONTENT GENERATION:
- File data → Structured markdown tables
- Statistics → Summary sections with metrics
- Content snippets → Formatted code blocks
- Metadata → Professional information displays

FORMATTING RULES:
- Use clear markdown headers (##, ###)
- Include data tables for structured info
- Add code blocks for file content samples
- Provide executive summary with key metrics
- End with actionable conclusions

QUALITY CRITERIA:
✅ Clear structure and formatting
✅ Relevant data and insights included
✅ Professional presentation
✅ Actionable conclusions"""


class ReportingAgent(Agent):
    """
    Fast, reliable reporting agent using Hybrid RPAVH.

    Features:
    - Template-based report generation
    - Direct content assembly (no LLM delays)
    - Professional formatting
    - Smart data organization
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        name: str = "reporting_agent",
        report_filename: str = "analysis_report.md",
        report_format: str = "markdown",
        max_attempts: int = 2,
        use_llm_reflection: bool = False,
        temperature: float = 0.1,
        **kwargs
    ):
        """
        Initialize Reporting Agent.

        Args:
            llm: LangChain LLM instance for report synthesis (optional)
            tools: List of tools to use
            name: Agent identifier
            report_filename: Output report filename
            report_format: Report format (markdown, html, txt)
            max_attempts: Maximum retry attempts
            use_llm_reflection: Enable LLM reflection for complex reports
            temperature: LLM temperature for slight creativity in report writing
        """
        from agenticflow.core.config import AgentConfig
        config = AgentConfig(
            name=name,
            model="",  # Model name not needed when LLM instance is provided
            temperature=temperature,
            role=AgentRole.REPORTER,
            capabilities=["content_generation", "report_formatting", "data_synthesis"],
            system_prompt=f"""You are a high-performance reporting agent optimized for speed and quality.

Configuration:
- Output: {report_filename}
- Format: {report_format}
- Max Attempts: {max_attempts}

You use hybrid RPAVH execution:
- Template-based content generation
- Direct data assembly
- Minimal LLM overhead
- Professional formatting

Focus on creating clear, actionable reports quickly.""",
            rules=ReportingAgentRules()
        )

        # Initialize parent with LangChain LLM
        super().__init__(
            config=config,
            tools=tools,
            model=llm,
            max_attempts=max_attempts,
            use_llm_reflection=use_llm_reflection,
            use_llm_verification=False,  # Keep verification fast
            **kwargs
        )

        # Set static resources for rule-based report generation
        self.static_resources = {
            "use_llm_for_report": True,
            "report_filename": report_filename,
            "report_format": report_format,
            "template_sections": [
                "executive_summary",
                "data_overview",
                "key_findings",
                "detailed_analysis",
                "conclusion"
            ],
            "formatting_rules": {
                "markdown": {
                    "title": "# ",
                    "section": "## ",
                    "subsection": "### ",
                    "table_header": "| Column | Value |",
                    "table_separator": "|--------|-------|",
                    "code_block": "```",
                    "emphasis": "**",
                    "list_item": "- "
                }
            },
            "content_limits": {
                "max_file_content_chars": 1000,
                "max_files_to_include": 10,
                "max_report_sections": 5
            },
            "quality_metrics": [
                "clear_structure",
                "relevant_data",
                "professional_format",
                "actionable_insights"
            ]
        }

        # Disable auto-discovery in Flow.add_agent; we will adopt tools explicitly
        try:
            setattr(self, "auto_discover", False)
        except Exception:
            pass


class EnhancedReportingAgent(Agent):
    """
    Enhanced reporting agent with adaptive content generation.

    This version includes:
    - Multiple output formats
    - Adaptive report types based on content
    - Smart LLM assistance for complex analysis
    - Enhanced content organization
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        name: str = "enhanced_reporting_agent",
        output_formats: Optional[List[str]] = None,
        report_types: Optional[List[str]] = None,
        max_attempts: int = 3,
        enable_smart_content: bool = True,
        temperature: float = 0.2,
        **kwargs
    ):
        """
        Initialize Enhanced Reporting Agent.

        Args:
            llm: LangChain LLM instance for adaptive content generation
            tools: List of tools to use
            name: Agent identifier
            output_formats: Supported output formats
            report_types: Available report types
            max_attempts: Maximum retry attempts
            enable_smart_content: Enable smart LLM assistance
            temperature: LLM temperature for more creativity in adaptive content
        """
        if output_formats is None:
            output_formats = ["markdown", "html"]
        if report_types is None:
            report_types = ["technical", "executive", "summary"]

        class EnhancedReportingRules:
            def get_rules_text(self) -> str:
                return f"""📈 ENHANCED REPORTING AGENT - ADAPTIVE CONTENT

CONFIGURATION:
- Formats: {output_formats}
- Types: {report_types}
- Max Attempts: {max_attempts}
- Smart Content: {enable_smart_content}

ENHANCED CAPABILITIES:
- Multi-format output generation
- Adaptive report type selection based on content
- Smart LLM assistance for complex analysis
- Dynamic content organization and insights

REPORT TYPE SELECTION:
- Technical: Detailed analysis with code/data specifics
- Executive: High-level summary with key metrics
- Summary: Concise overview with main findings

ADAPTIVE CONTENT FEATURES:
- Auto-detect content complexity
- Choose appropriate report type
- Generate format-specific styling
- Include relevant visualizations (text-based)

SMART CONTENT TRIGGERS:
- Complex data relationships → Use LLM analysis
- Multiple data sources → Generate synthesis
- Unclear patterns → Add LLM interpretation
- Executive audience → Focus on business impact"""

        from agenticflow.core.config import AgentConfig
        config = AgentConfig(
            name=name,
            model="",  # Model name not needed when LLM instance is provided
            temperature=temperature,
            role=AgentRole.REPORTER,
            capabilities=["multi_format_reporting", "adaptive_content", "smart_analysis"],
            system_prompt=f"""You are an enhanced reporting agent with adaptive content capabilities.

Report Configuration:
- Formats: {output_formats}
- Types: {report_types}

You combine fast template-based generation with smart LLM assistance for complex content.""",
            rules=EnhancedReportingRules()
        )

        # Initialize parent with LangChain LLM
        super().__init__(
            config=config,
            tools=tools,
            model=llm,
            max_attempts=max_attempts,
            use_llm_reflection=enable_smart_content,  # Enable for complex reports
            use_llm_verification=False,  # Keep verification fast
            **kwargs
        )

        self.static_resources = {
            "output_formats": output_formats,
            "report_types": report_types,
            "adaptive_content": enable_smart_content,
            "format_templates": {
                "markdown": {
                    "extension": ".md",
                    "title_format": "# {title}",
                    "section_format": "## {section}",
                    "table_support": True,
                    "code_blocks": True
                },
                "html": {
                    "extension": ".html",
                    "title_format": "<h1>{title}</h1>",
                    "section_format": "<h2>{section}</h2>",
                    "table_support": True,
                    "styling": True
                }
            },
            "report_templates": {
                "technical": {
                    "sections": ["methodology", "data_analysis", "technical_findings", "implementation_details"],
                    "detail_level": "high",
                    "include_code": True
                },
                "executive": {
                    "sections": ["executive_summary", "key_metrics", "strategic_insights", "recommendations"],
                    "detail_level": "low",
                    "include_code": False
                },
                "summary": {
                    "sections": ["overview", "main_findings", "next_steps"],
                    "detail_level": "medium",
                    "include_code": False
                }
            },
            "content_intelligence": {
                "auto_type_selection": True,
                "smart_insights": enable_smart_content,
                "adaptive_formatting": True
            }
        }