"""Analysis Agent - Specialized for data analysis and pattern recognition."""

from typing import Dict, Any, Optional, List
from agenticflow.agent.agent import Agent
from agenticflow.core.config import AgentConfig
from agenticflow.core.roles import AgentRole
from agenticflow.core.rules import AnalysisAgentRules


def create_analysis_agent(
    name: str = "analysis_agent",
    temperature: float = 0.2,
    model_name: str = "",
    **kwargs
) -> Agent:
    """Create a pre-configured Analysis agent.
    
    This agent is specialized for:
    - Data analysis and pattern recognition
    - Statistical analysis and interpretation
    - Relationship mapping and dependency analysis
    - Extracting insights from structured and unstructured data
    - Comparative analysis
    
    Args:
        name: Agent name (default: "analysis_agent")
        temperature: LLM temperature (default: 0.2 for analytical precision)
        model_name: Override default model
        **kwargs: Additional agent configuration including:
            - analysis_depth: Depth of analysis to perform (default: "comprehensive")
            - pattern_types: List of pattern types to focus on
            
    Returns:
        Configured Analysis agent
    """
    # Let the agent adopt tools from the flow instead of pre-configuring them
    # This ensures PathGuard is properly injected
    tools = []
    
    # Analysis-specific configuration
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=temperature,
        tools=[t.name for t in tools],
        tags=["analysis", "data", "patterns", "insights"],
        description="Specialized agent for data analysis, pattern recognition, and insight extraction",
        role=AgentRole.ANALYST
    )
    
    # Add additional config properties
    config.capabilities = ["analysis", "pattern_recognition", "data_interpretation", "comparison"]
    
    # General system prompt for Analysis agents
    config.system_prompt = """You are an Analysis Agent specialized in extracting insights and patterns from data.

Your primary capabilities:
- Analyze structured and unstructured data systematically
- Identify patterns, trends, and relationships
- Compare and contrast different data sources
- Extract actionable insights and recommendations
- Map dependencies and relationships between components
- Provide quantitative analysis where possible

Best practices:
- Be thorough and systematic in your analysis
- Look for both obvious and subtle patterns
- Provide quantitative insights where possible
- Identify potential risks, opportunities, and dependencies
- Support conclusions with evidence from the data
- Consider multiple perspectives and scenarios
- Focus on analysis, not final report generation"""
    
    # Add strict operational rules
    config.rules = AnalysisAgentRules(
        analysis_depth=kwargs.get('analysis_depth', 'comprehensive'),
        pattern_types=kwargs.get('pattern_types', None)
    )
    
    # Add any custom kwargs as extra fields (excluding the ones we already handled)
    rule_kwargs = {'analysis_depth', 'pattern_types'}
    for key, value in kwargs.items():
        if key not in rule_kwargs:
            setattr(config, key, value)
    
    agent = Agent(
        config=config,
        tools=tools
    )
    
    return agent


def get_analysis_agent_info() -> Dict[str, Any]:
    """Get information about the Analysis agent."""
    return {
        "description": "Specialized for data analysis, pattern recognition, and insight extraction",
        "role": AgentRole.ANALYST,
        "capabilities": ["analysis", "pattern_recognition", "data_interpretation", "comparison"],
        "use_cases": ["Data analysis", "Pattern detection", "Insight extraction", "Comparative analysis"],
        "configurable_params": {
            "analysis_depth": "Depth of analysis to perform (default: 'comprehensive')",
            "pattern_types": "List of pattern types to focus on (default: ['dependencies', 'data_flows', 'transformations', 'bottlenecks'])"
        }
    }