"""Hybrid RPAVH Reporting Agent - Fast and Professional"""

from typing import Optional, Dict, Any
from agenticflow.agent.hybrid_rpavh_agent import HybridRPAVHAgent
from agenticflow.core.config import AgentConfig
from agenticflow.core.roles import AgentRole


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


def create_hybrid_reporting_agent(
    name: str = "hybrid_reporting_agent",
    report_filename: str = "analysis_report.md",
    report_format: str = "markdown",
    max_attempts: int = 2,
    use_llm_reflection: bool = False,  # Keep it fast
    model_name: str = ""
) -> HybridRPAVHAgent:
    """
    Create a fast, reliable reporting agent using Hybrid RPAVH.
    
    Features:
    - Template-based report generation
    - Direct content assembly (no LLM delays)
    - Professional formatting
    - Smart data organization
    
    Args:
        name: Agent identifier
        report_filename: Output report filename
        report_format: Report format (markdown, html, txt)
        max_attempts: Maximum retry attempts
        use_llm_reflection: Enable LLM reflection for complex reports
        model_name: LLM model for reflection (only used if enabled)
    """
    
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=0.1,  # Slight creativity for report writing
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
    
    # Create hybrid agent with optimized settings
    agent = HybridRPAVHAgent(
        config=config,
        max_attempts=max_attempts,
        use_llm_reflection=use_llm_reflection,  # Usually False for speed
        use_llm_verification=False  # Keep verification fast
    )
    
    # Set static resources for rule-based report generation
    agent.static_resources = {
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
        setattr(agent, "auto_discover", False)
    except Exception:
        pass
    return agent


def create_enhanced_hybrid_reporting_agent(
    name: str = "enhanced_hybrid_reporter",
    output_formats: list = None,
    report_types: list = None,
    max_attempts: int = 3,
    enable_smart_content: bool = True,
    model_name: str = "llama3.2:latest"
) -> HybridRPAVHAgent:
    """
    Create an enhanced reporting agent with adaptive content generation.
    
    This version includes:
    - Multiple output formats
    - Adaptive report types based on content
    - Smart LLM assistance for complex analysis
    - Enhanced content organization
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
    
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=0.2,  # More creativity for adaptive content
        role=AgentRole.REPORTER,
        capabilities=["multi_format_reporting", "adaptive_content", "smart_analysis"],
        system_prompt=f"""You are an enhanced reporting agent with adaptive content capabilities.

Report Configuration:
- Formats: {output_formats}
- Types: {report_types}

You combine fast template-based generation with smart LLM assistance for complex content.""",
        rules=EnhancedReportingRules()
    )
    
    agent = HybridRPAVHAgent(
        config=config,
        max_attempts=max_attempts,
        use_llm_reflection=enable_smart_content,  # Enable for complex reports
        use_llm_verification=False  # Keep verification fast
    )
    
    agent.static_resources = {
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
    
    return agent