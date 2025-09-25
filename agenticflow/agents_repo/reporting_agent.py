"""Reporting Agent - Specialized for generating reports and documentation."""

from typing import Dict, Any, Optional, List
from agenticflow.agent.agent import Agent
from agenticflow.core.config import AgentConfig
from agenticflow.core.roles import AgentRole
from agenticflow.core.rules import ReportingAgentRules


def create_reporting_agent(
    name: str = "reporting_agent", 
    temperature: float = 0.3,
    model_name: str = "",
    **kwargs
) -> Agent:
    """Create a pre-configured Reporting agent.
    
    This agent is specialized for:
    - Generating structured reports and documentation
    - Summarizing and analyzing data
    - Creating markdown, text, and formatted content
    - Synthesizing information from multiple sources
    - Content organization and presentation
    
    Args:
        name: Agent name (default: "reporting_agent")
        temperature: LLM temperature for creativity (default: 0.3 for balanced creativity)
        model_name: Override default model
        **kwargs: Additional agent configuration including:
            - report_filename: Name of the output report file (default: "ssis_analysis_report.md")
            - focus_areas: List of areas to focus analysis on
            
    Returns:
        Configured Reporting agent
    """
    # Pre-configure specialized tools for Reporting operations
    # This agent should ONLY have content creation tools, NOT file discovery tools
    tools = []  # Will be populated when added to flow with specific tools
    
    # Reporting-specific configuration
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=temperature,
        tools=[t.name for t in tools],
        tags=["reporting", "content", "analysis", "documentation"],
        description="Specialized agent for generating reports, summaries, and documentation",
        role=AgentRole.REPORTER
    )
    
    # Add additional config properties
    config.capabilities = ["content_creation", "analysis", "summarization", "markdown", "reporting"]
    
    # General system prompt for Reporting agents
    config.system_prompt = """You are a Reporting Agent specialized in creating clear, structured reports and documentation.

Your primary capabilities:
- Generate well-structured markdown reports
- Summarize complex information clearly
- Analyze data and extract key insights
- Create executive summaries and detailed documentation
- Organize information logically and accessibly
- Transform raw data into actionable insights

Best practices:
- Use clear headings and structure in reports
- Include executive summaries for complex topics
- Provide actionable insights and recommendations
- Use tables, lists, and formatting for readability
- Cite sources and provide context for findings
- Write for your intended audience (technical vs. business)"""
    
    # Add strict operational rules
    config.rules = ReportingAgentRules(
        report_filename=kwargs.get('report_filename', 'ssis_analysis_report.md'),
        focus_areas=kwargs.get('focus_areas', None)
    )
    
    # Add any custom kwargs as extra fields (excluding the ones we already handled)
    rule_kwargs = {'report_filename', 'focus_areas'}
    for key, value in kwargs.items():
        if key not in rule_kwargs:
            setattr(config, key, value)
    
    agent = Agent(
        config=config,
        tools=tools
    )
    
    return agent


def get_reporting_agent_info() -> Dict[str, Any]:
    """Get information about the Reporting agent."""
    return {
        "description": "Specialized for generating reports and documentation",
        "role": AgentRole.REPORTER,
        "capabilities": ["content_creation", "analysis", "summarization", "markdown", "reporting"],
        "use_cases": ["Report generation", "Documentation", "Summarization", "Content creation"],
        "configurable_params": {
            "report_filename": "Name of the output report file (default: 'ssis_analysis_report.md')",
            "focus_areas": "List of areas to focus analysis on (default: ['connections', 'data_flows', 'control_flows', 'variables', 'transformations'])"
        }
    }