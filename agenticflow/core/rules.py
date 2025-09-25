"""Agent Rules - Specific operational constraints and procedures for specialized agents.

Rules define strict operational guidelines that agents must follow, separate from
general system prompts. They provide specific do's and don'ts, tool usage patterns,
and step-by-step procedures for different agent specializations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AgentRules(ABC):
    """Base class for agent rules."""
    
    @abstractmethod
    def get_rules_text(self) -> str:
        """Return the rules as formatted text to be included in agent prompt."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about these rules."""
        return {
            "rule_type": self.__class__.__name__,
            "description": getattr(self, "description", ""),
        }


class FileSystemAgentRules(AgentRules):
    """Strict operational rules for FileSystem agents."""
    
    description = "Rules for file discovery, reading, and filesystem operations"
    
    def __init__(self, 
                 file_pattern: str = "*.dtsx", 
                 search_root: str = "data/ssis",
                 **kwargs):
        self.file_pattern = file_pattern
        self.search_root = search_root
        self.extra_params = kwargs
    
    def get_rules_text(self) -> str:
        return f"""
1. FILE DISCOVERY RULE:
   - Start with find_files using the configured search root: {{'file_glob': '{self.file_pattern}', 'root_path': '{self.search_root}'}}
   - If path fails, try alternative approaches in this order:
     a) Try with current working directory: {{'file_glob': '{self.file_pattern}', 'root_path': '.'}}
     b) Try absolute path variations: {{'file_glob': '{self.file_pattern}', 'root_path': '/Users/miladolad/Projects/agenticflow/examples/{self.search_root}'}}
     c) Search from workspace root and subdirectories recursively
   - The find_files tool returns absolute paths in the 'files' array
   - Extract the 'path' field from each file object returned

2. PATH RESOLUTION RULE:
   - If initial search path fails with "Not a directory" error:
     a) Check if search path exists relative to current workspace
     b) Try common alternative locations (examples/, data/, etc.)
     c) Use file_stat tool to verify directory existence before using find_files
     d) Convert relative paths to absolute paths when needed
   - NEVER give up after first path failure - be persistent and intelligent

3. FILE READING RULE:
   - When reading files discovered by find_files, use the EXACT paths from the find_files results
   - Use read_text_fast tool with the full path from find_files
   - Example: If find_files returns path "/Users/.../data/ssis/file.dtsx", use that exact path
   - If reading fails, try alternative encodings or report the specific error

4. INTELLIGENT ERROR HANDLING RULE:
   - If find_files returns "Not a directory" error, immediately try alternative paths
   - If no files found with initial pattern, try broader search patterns
   - Log each attempt with clear reasoning
   - Only fail if ALL reasonable path attempts have been exhausted
   - Provide helpful suggestions for path corrections

5. WORKSPACE NAVIGATION RULE:
   - Understand that you may be operating within a workspace environment
   - Try relative paths first, then absolute paths
   - Use file_stat to explore directory structure when needed
   - Be aware of common workspace layouts (examples/, data/, src/, etc.)

6. OUTPUT RULE:
   - Provide structured output listing all discovered files with full paths
   - Include file sizes, modification times, and directory information  
   - Show which search attempts succeeded and which failed
   - CRITICAL FOR AGENT HANDOFFS: End your response with a structured summary:
     
     FILE DISCOVERY SUMMARY:
     - Total files found: X
     - Files processed: [list with paths and sizes]
     - Content extracted: [brief description of each file's content]
     - Ready for analysis: YES/NO
     
     This summary enables other agents to continue the workflow

7. COLLABORATION RULE:
   - Your primary role is file discovery and content extraction
   - DO NOT perform analysis or reporting on file contents
   - After reading all files, summarize the discovered data in your response
   - The system will automatically share your results with other agents
   - COMPLETE the task once all files are read - do not repeat file operations

8. TASK COMPLETION RULE:
   - Once you have successfully discovered and read files, your task is COMPLETE
   - Do NOT repeat file discovery or reading operations  
   - IMMEDIATELY state: "TASK COMPLETED: Found X files, read Y files, [summary]"
   - Then STOP all operations - do not continue processing
   - Provide the structured FILE DISCOVERY SUMMARY and end your response

9. PERSISTENCE RULE:
   - Be persistent in finding files - try multiple approaches before giving up
   - Use logical reasoning about likely file locations
   - Combine tools effectively (file_stat + find_files + read_text_fast)
   - Always provide actionable feedback about what was tried and what worked""".strip()


class ReportingAgentRules(AgentRules):
    """Strict operational rules for Reporting agents."""
    
    description = "Rules for content analysis, report generation, and documentation"
    
    def __init__(self, 
                 report_filename: str = "ssis_analysis_report.md",
                 focus_areas: Optional[list] = None,
                 **kwargs):
        self.report_filename = report_filename
        self.focus_areas = focus_areas or ["connections", "data_flows", "control_flows", "variables", "transformations"]
        self.extra_params = kwargs
    
    def get_rules_text(self) -> str:
        focus_list = ", ".join(self.focus_areas)
        return f"""
1. CONTENT CONSUMPTION RULE:
   - NEVER perform file discovery or direct file reading
   - ALWAYS check for context from previous tasks at the start of your work
   - Look for "=== CONTEXT FROM PREVIOUS TASKS ===" section in your task description
   - Extract file contents, metadata, and results from dependency tasks
   - If no context is provided, explicitly request data from FileSystem Agent

2. ANALYSIS SCOPE RULE:
   - Focus on analyzing SSIS package structures and components
   - Identify and extract: {focus_list}
   - Extract metadata like package names, descriptions, configurations
   - Look for patterns, dependencies, and architectural insights

3. REPORT GENERATION RULE:
   - Create comprehensive markdown reports with clear structure
   - Include executive summary, detailed findings, and recommendations
   - Use tables for structured data (connections, variables, tasks)
   - Provide insights about data flows, transformations, and dependencies

4. REPORT SAVING RULE:
   - ALWAYS save the final report using write_text_atomic tool
   - Use EXACTLY this format: {{'path': '{self.report_filename}', 'content': 'your_report_content'}}
   - Do NOT use 'workspace_root/' or any directory prefixes
   - Do NOT use 'encoding' parameter - it's handled automatically
   - ALWAYS generate substantial report content (not placeholders)
   - Confirm successful save operation with file size
   - Example: write_text_atomic(path='{self.report_filename}', content='# SSIS Analysis Report...')

5. COLLABORATION RULE:
   - Wait for FileSystem Agent to provide file contents
   - Process ALL provided file data comprehensively
   - Generate complete analysis based on all available SSIS packages
   - Do not request additional file operations

6. OUTPUT QUALITY RULE:
   - Reports must be professional and well-structured
   - Include specific examples and evidence from the data
   - Provide actionable recommendations where applicable
   - Use clear headings, bullet points, and formatting
""".strip()


class AnalysisAgentRules(AgentRules):
    """Strict operational rules for Analysis agents."""
    
    description = "Rules for data analysis, pattern recognition, and insight extraction"
    
    def __init__(self, 
                 analysis_depth: str = "comprehensive",
                 pattern_types: Optional[list] = None,
                 **kwargs):
        self.analysis_depth = analysis_depth
        self.pattern_types = pattern_types or ["dependencies", "data_flows", "transformations", "bottlenecks"]
        self.extra_params = kwargs
    
    def get_rules_text(self) -> str:
        pattern_list = ", ".join(self.pattern_types)
        return f"""
1. DATA CONSUMPTION RULE:
   - Accept data from FileSystem agents or other data collectors
   - Work with structured and unstructured data provided by other agents
   - Do NOT perform direct file operations unless specifically equipped with file tools

2. ANALYSIS FOCUS RULE:
   - Perform {self.analysis_depth} analysis of provided data
   - Look for patterns in: {pattern_list}
   - Identify relationships, dependencies, and system architecture
   - Extract quantitative metrics where possible

3. PATTERN RECOGNITION RULE:
   - Systematically analyze data for obvious and subtle patterns
   - Compare and contrast different components or data sources
   - Map relationships between system components
   - Identify potential risks, opportunities, and optimization areas

4. INSIGHT EXTRACTION RULE:
   - Provide actionable insights based on analysis
   - Support conclusions with evidence from the data
   - Consider multiple perspectives and scenarios
   - Quantify findings where possible

5. COLLABORATION RULE:
   - Provide analysis results to Reporting agents for documentation
   - Share insights with other Analysis agents for cross-validation
   - Focus on analysis, not final report generation

6. OUTPUT RULE:
   - Structure findings clearly with supporting evidence
   - Use specific examples from the analyzed data
   - Provide confidence levels for insights when applicable
   - Highlight critical findings that need immediate attention
""".strip()


# Convenience function for creating common rule combinations
def create_filesystem_rules(file_pattern: str = "*.dtsx", search_root: str = "data/ssis") -> FileSystemAgentRules:
    """Create FileSystem agent rules with common SSIS parameters."""
    return FileSystemAgentRules(file_pattern=file_pattern, search_root=search_root)


def create_reporting_rules(report_filename: str = "analysis_report.md") -> ReportingAgentRules:
    """Create Reporting agent rules with custom report filename."""
    return ReportingAgentRules(report_filename=report_filename)


def create_analysis_rules(analysis_depth: str = "comprehensive") -> AnalysisAgentRules:
    """Create Analysis agent rules with specified depth."""
    return AnalysisAgentRules(analysis_depth=analysis_depth)