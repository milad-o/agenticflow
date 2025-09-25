"""RPAVH-based Reporting Agent with sophisticated content generation."""

from typing import Optional, Dict, Any
from agenticflow.agent.rpavh_agent import RPAVHAgent
from agenticflow.core.config import AgentConfig
from agenticflow.core.roles import AgentRole


class ReportingAgentRules:
    """Rules for reporting agent behavior with self-correction."""
    
    def get_rules_text(self) -> str:
        return """📊 REPORTING AGENT RULES - INTELLIGENT CONTENT GENERATION

CORE MISSION:
- Generate comprehensive, well-structured reports
- Transform raw data into actionable insights  
- Create clear, professional documentation
- Complete report generation decisively without loops

REFLECTION PHASE RULES:
- Analyze input data for structure and content
- Identify key insights, patterns, and findings
- Consider report audience and purpose
- Plan appropriate report format and sections

PLANNING PHASE RULES:
- Structure report with logical flow:
  1. Executive Summary
  2. Data Overview  
  3. Detailed Analysis
  4. Key Findings
  5. Recommendations/Conclusions
- Plan content organization and formatting
- Choose appropriate level of technical detail

ACTION PHASE RULES:
- Write clear, concise, and professional content
- Use proper markdown formatting for readability
- Include relevant data, statistics, and examples
- Create well-organized sections and subsections
- Use write_text_atomic for reliable file writing

VERIFICATION PHASE RULES:
- Check report completeness and structure
- Verify all data is accurately represented
- Ensure conclusions are supported by evidence
- Confirm formatting is correct and consistent

COMPLETION RULES:
- Provide summary of report contents and location
- Include key metrics (word count, sections, insights)
- State "REPORT GENERATION COMPLETED" when done
- Do NOT rewrite or modify completed reports

FAILURE RECOVERY:
- If data is incomplete, work with available information
- If formatting issues occur, use simpler structure
- If file write fails, try alternative approaches
- Maximum 3 attempts before declaring completion

HANDOFF CONDITIONS:
- Complex data visualization needed → Hand off to visualization agent
- Statistical analysis required → Hand off to analytics agent
- Large dataset processing → Hand off to data processing agent
- Interactive dashboard creation → Hand off to web/dashboard agent"""


def create_rpavh_reporting_agent(
    name: str = "reporting_agent_rpavh", 
    report_filename: str = "analysis_report.md",
    report_format: str = "markdown",
    max_attempts: int = 3,
    model_name: str = "llama3.2:latest",
    temperature: float = 0.2
) -> RPAVHAgent:
    """
    Create a sophisticated RPAVH-based reporting agent.
    
    This agent uses the Reflect-Plan-Act-Verify-Handoff pattern for:
    - Intelligent content analysis and insight extraction
    - Well-structured report generation with proper formatting
    - Quality verification of generated content
    - Smart handoff for specialized reporting needs
    
    Args:
        name: Agent identifier
        report_filename: Output filename for generated reports
        report_format: Report format (markdown, html, txt)
        max_attempts: Maximum retry attempts for failed operations
        model_name: LLM model to use
        temperature: LLM temperature for creative content generation
    """
    
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=temperature,
        role=AgentRole.REPORTER,
        capabilities=["content_analysis", "report_writing", "data_synthesis", "documentation"],
        system_prompt=f"""You are a sophisticated reporting agent using the RPAVH execution pattern.

Your specialty: Intelligent analysis and professional report generation with self-correction.

Current Configuration:
- Report Format: {report_format}
- Output File: {report_filename}
- Max Attempts: {max_attempts}

You execute using a 5-phase cycle:
1. REFLECT: Analyze input data and determine report structure
2. PLAN: Create comprehensive content strategy and outline
3. ACT: Generate high-quality report content with proper formatting
4. VERIFY: Validate report quality, accuracy, and completeness
5. HANDOFF: Coordinate with specialized agents when needed

You excel at transforming raw data into actionable insights with professional presentation.""",
        rules=ReportingAgentRules(),
        tags=["reporting", "content_generation", "analysis", "documentation"]
    )
    
    agent = RPAVHAgent(
        config=config,
        max_attempts=max_attempts,
        reflection_enabled=True,
        verification_enabled=True,
        handoff_enabled=True
    )
    
    agent.static_resources = {
        "report_filename": report_filename,
        "report_format": report_format,
        "supported_formats": ["markdown", "html", "txt", "json"],
        "report_sections": ["executive_summary", "overview", "analysis", "findings", "recommendations"],
        "formatting_guidelines": {
            "markdown": {"headers": ["#", "##", "###"], "lists": ["- ", "1. "], "emphasis": ["**", "*"]},
            "html": {"headers": ["<h1>", "<h2>", "<h3>"], "lists": ["<ul>", "<ol>"], "emphasis": ["<b>", "<i>"]},
            "txt": {"headers": ["===", "---", "..."], "lists": ["* ", "1) "], "emphasis": ["**", "*"]}
        },
        "quality_criteria": ["clarity", "completeness", "accuracy", "professionalism", "actionability"]
    }
    
    return agent


def create_enhanced_reporting_agent(
    name: str = "enhanced_reporting_agent",
    report_types: list = None,
    output_formats: list = None,
    include_visualizations: bool = False,
    max_report_sections: int = 10,
    max_attempts: int = 3,
    model_name: str = "llama3.2:latest"
) -> RPAVHAgent:
    """
    Create an enhanced reporting agent with advanced capabilities.
    
    This version supports:
    - Multiple report types (technical, executive, summary, detailed)
    - Multiple output formats with format-specific optimization
    - Optional visualization planning and coordination
    - Flexible section structures based on content
    """
    
    if report_types is None:
        report_types = ["technical", "executive", "summary", "detailed"]
    if output_formats is None:
        output_formats = ["markdown", "html", "pdf", "docx"]
    
    class EnhancedReportingRules:
        def get_rules_text(self) -> str:
            return f"""📈 ENHANCED REPORTING AGENT - MULTI-FORMAT GENERATION

REPORT CONFIGURATION:
- Types: {report_types}
- Formats: {output_formats}
- Max Sections: {max_report_sections}
- Visualizations: {include_visualizations}

ENHANCED CAPABILITIES:
- Multi-format report generation with format optimization
- Adaptive content structure based on report type
- Advanced data visualization planning
- Cross-referencing and linking between sections
- Quality assurance with multiple validation layers

REFLECTION ENHANCEMENTS:
- Analyze content complexity and determine optimal report type
- Consider audience technical level and information needs
- Plan visualization requirements and data presentation
- Identify cross-cutting themes and relationships

PLANNING ENHANCEMENTS:
- Create adaptive section structures based on content
- Plan format-specific optimizations and features
- Design information hierarchy and flow
- Plan supporting visualizations and data presentations

ACTION ENHANCEMENTS:
- Generate format-optimized content with proper styling
- Create consistent cross-references and navigation
- Implement progressive disclosure for complex information
- Generate placeholder specifications for visualizations

VERIFICATION ENHANCEMENTS:
- Multi-layer quality validation (structure, content, format)
- Cross-section consistency and coherence checking
- Format-specific validation and compliance
- Accessibility and readability assessment

HANDOFF ENHANCEMENTS:
- Data visualization → Visualization specialist
- Interactive elements → Web development agent
- Statistical analysis → Data science agent
- Multi-language content → Translation agent
- Publication formatting → Document specialist"""
    
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=0.25,  # Slightly higher for creative report generation
        role=AgentRole.REPORTER,
        capabilities=["multi_format_reporting", "content_optimization", "visualization_planning", "quality_assurance"],
        system_prompt=f"""You are an enhanced reporting agent with advanced multi-format capabilities.

Report Configuration:
- Types: {report_types}
- Formats: {output_formats}
- Visualizations: {include_visualizations}

You excel at creating sophisticated reports adapted to different audiences, formats, and purposes with intelligent content optimization.""",
        rules=EnhancedReportingRules()
    )
    
    agent = RPAVHAgent(config=config, max_attempts=max_attempts)
    
    agent.static_resources = {
        "report_types": report_types,
        "output_formats": output_formats,
        "include_visualizations": include_visualizations,
        "max_report_sections": max_report_sections,
        "report_templates": {
            "technical": ["abstract", "introduction", "methodology", "results", "discussion", "conclusion"],
            "executive": ["executive_summary", "key_findings", "recommendations", "next_steps"],
            "summary": ["overview", "highlights", "summary", "actions"],
            "detailed": ["background", "analysis", "findings", "implications", "recommendations", "appendices"]
        },
        "format_features": {
            "markdown": {"toc": True, "code_blocks": True, "tables": True, "links": True},
            "html": {"css_styling": True, "interactive_elements": True, "media": True},
            "pdf": {"page_breaks": True, "headers_footers": True, "professional_layout": True},
            "docx": {"styles": True, "comments": True, "track_changes": True}
        },
        "visualization_types": ["charts", "graphs", "diagrams", "tables", "infographics"] if include_visualizations else [],
        "quality_metrics": ["readability_score", "completeness_percentage", "accuracy_rating", "engagement_level"]
    }
    
    return agent