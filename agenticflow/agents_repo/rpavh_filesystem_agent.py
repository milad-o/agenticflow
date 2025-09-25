"""RPAVH-based Filesystem Agent with sophisticated self-correction."""

from typing import Optional, Dict, Any
from agenticflow.agent.rpavh_agent import RPAVHAgent
from agenticflow.core.config import AgentConfig
from agenticflow.core.roles import AgentRole


class FileSystemAgentRules:
    """Rules for filesystem agent behavior with self-correction."""
    
    def get_rules_text(self) -> str:
        return """🎯 FILESYSTEM AGENT RULES - DECISIVE EXECUTION

CORE MISSION:
- Discover and read files efficiently
- Provide complete file content and metadata  
- Use proper tool parameters and error handling
- Complete tasks decisively without loops

REFLECTION PHASE RULES:
- Analyze file search requirements carefully
- Consider path resolution (absolute vs relative)
- Identify potential access or permission issues
- Plan fallback strategies for file discovery

PLANNING PHASE RULES:
- Break file operations into clear steps:
  1. File discovery (find_files with proper parameters)
  2. Content reading (read_text_fast for each file)
  3. Metadata collection if needed (file_stat)
- Plan fallback paths for file access failures
- Always plan verification of results

ACTION PHASE RULES:
- Use find_files with correct glob patterns (*.dtsx, *.xml, etc.)
- Handle both absolute and relative paths appropriately
- Use read_text_fast for efficient content reading
- If find_files fails, try alternative discovery methods
- Log all file operations and results clearly

VERIFICATION PHASE RULES:
- Confirm all requested files were found and read
- Verify content is complete and not truncated
- Check for any file access errors or issues
- Ensure metadata is accurate when requested

COMPLETION RULES:
- Provide comprehensive summary of files processed
- Include file count, total size, and key insights
- State "FILE OPERATIONS COMPLETED" when done
- Do NOT attempt additional verification after completion

FAILURE RECOVERY:
- If path not found, try alternative path resolution
- If permission denied, report clearly and suggest solutions
- If files not found, expand search patterns or suggest alternatives
- Maximum 3 attempts before declaring task complete or failed

HANDOFF CONDITIONS:
- Large file processing (>10MB total) → Hand off to specialized agent
- Binary file analysis needed → Hand off to analysis agent  
- Complex file transformations → Hand off to processing agent
- Report generation needed → Hand off to reporting agent"""


def create_rpavh_filesystem_agent(
    name: str = "filesystem_agent_rpavh",
    file_pattern: str = "*.dtsx",
    search_root: str = ".",
    max_attempts: int = 3,
    model_name: str = "llama3.2:latest",
    temperature: float = 0.1
) -> RPAVHAgent:
    """
    Create a sophisticated RPAVH-based filesystem agent.
    
    This agent uses the Reflect-Plan-Act-Verify-Handoff pattern for:
    - Intelligent file discovery with fallback strategies
    - Robust content reading with error recovery
    - Quality verification of results
    - Smart handoff to other agents when needed
    
    Args:
        name: Agent identifier
        file_pattern: Glob pattern for file discovery (*.dtsx, *.xml, etc.)
        search_root: Root directory for file search
        max_attempts: Maximum retry attempts for failed operations
        model_name: LLM model to use
        temperature: LLM temperature setting
    """
    
    # Create agent configuration with rules
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=temperature,
        role=AgentRole.FILE_MANAGER,
        capabilities=["file_discovery", "content_reading", "metadata_analysis", "path_resolution"],
        system_prompt=f"""You are a sophisticated filesystem agent using the RPAVH execution pattern.

Your specialty: Intelligent file discovery and content reading with self-correction capabilities.

Current Configuration:
- File Pattern: {file_pattern}
- Search Root: {search_root}
- Max Attempts: {max_attempts}

You execute using a 5-phase cycle:
1. REFLECT: Analyze file requirements and potential issues
2. PLAN: Create strategic file operation plan with fallbacks
3. ACT: Execute file operations with error handling  
4. VERIFY: Validate results for completeness and accuracy
5. HANDOFF: Coordinate with other agents when appropriate

Your tools will be set by the orchestrator. Use them intelligently with proper error recovery.""",
        rules=FileSystemAgentRules(),
        tags=["filesystem", "file_read", "search", "discovery"]
    )
    
    # Create the RPAVH agent
    agent = RPAVHAgent(
        config=config,
        max_attempts=max_attempts,
        reflection_enabled=True,
        verification_enabled=True,
        handoff_enabled=True
    )
    
    # Set static resources for agent context
    agent.static_resources = {
        "file_pattern": file_pattern,
        "search_root": search_root,
        "supported_extensions": [".dtsx", ".xml", ".txt", ".json", ".md", ".py"],
        "max_file_size_mb": 50,
        "encoding_fallbacks": ["utf-8", "utf-16", "latin-1"]
    }
    
    return agent


def create_enhanced_filesystem_agent(
    name: str = "enhanced_filesystem_agent",
    search_patterns: list = None,
    search_roots: list = None,
    max_file_size_mb: int = 100,
    max_attempts: int = 3,
    model_name: str = "llama3.2:latest"
) -> RPAVHAgent:
    """
    Create an enhanced filesystem agent with multiple search capabilities.
    
    This version supports:
    - Multiple file patterns and search roots
    - Large file handling with size limits
    - Advanced content analysis
    - Intelligent path resolution
    """
    
    if search_patterns is None:
        search_patterns = ["*.dtsx", "*.xml", "*.json", "*.txt"]
    if search_roots is None:
        search_roots = [".", "data", "examples"]
    
    # Enhanced rules for multi-pattern search
    class EnhancedFileSystemRules:
        def get_rules_text(self) -> str:
            return f"""🔍 ENHANCED FILESYSTEM AGENT - MULTI-PATTERN DISCOVERY

SEARCH CONFIGURATION:
- Patterns: {search_patterns}
- Search Roots: {search_roots}  
- Max File Size: {max_file_size_mb}MB
- Max Attempts: {max_attempts}

ENHANCED CAPABILITIES:
- Multi-pattern file discovery across multiple roots
- Intelligent path resolution and fallback
- Large file handling with size checks
- Content type detection and appropriate handling
- Metadata extraction and analysis

REFLECTION ENHANCEMENTS:
- Analyze search complexity and expected file count
- Consider system resources and file sizes
- Plan optimal search strategy across roots
- Identify potential performance bottlenecks

PLANNING ENHANCEMENTS:
- Prioritize search patterns by importance
- Plan parallel search strategies when beneficial
- Create size-based processing strategies
- Plan content sampling for large files

ACTION ENHANCEMENTS:
- Use parallel search across multiple roots
- Implement progressive file discovery
- Handle large files with streaming or sampling
- Use appropriate encodings for different file types

VERIFICATION ENHANCEMENTS:
- Validate search coverage across all patterns/roots
- Check file size limits and content completeness
- Verify content integrity and encoding correctness
- Ensure all expected file types were processed

HANDOFF ENHANCEMENTS:
- Large dataset processing → Data processing agent
- Complex file analysis → Analysis specialist
- Batch processing needs → Batch processing agent
- Visualization needs → Reporting/visualization agent"""
    
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=0.1,
        role=AgentRole.DATA_COLLECTOR,
        capabilities=["multi_pattern_search", "large_file_handling", "content_analysis", "metadata_extraction"],
        system_prompt=f"""You are an enhanced filesystem agent with advanced discovery capabilities.

Search Configuration:
- Patterns: {search_patterns}
- Roots: {search_roots}
- Max File Size: {max_file_size_mb}MB

You excel at complex file discovery scenarios with multiple patterns, large files, and intelligent content handling.

Execute using RPAVH pattern with enhanced capabilities for robust file operations.""",
        rules=EnhancedFileSystemRules()
    )
    
    agent = RPAVHAgent(config=config, max_attempts=max_attempts)
    
    agent.static_resources = {
        "search_patterns": search_patterns,
        "search_roots": search_roots,
        "max_file_size_mb": max_file_size_mb,
        "supported_encodings": ["utf-8", "utf-16", "latin-1", "ascii"],
        "content_types": ["xml", "json", "text", "sql", "dtsx"],
        "sampling_strategy": "head_tail_middle",  # For large files
        "parallel_search": True
    }
    
    return agent