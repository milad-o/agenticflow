"""Hybrid RPAVH Filesystem Agent - Fast and Reliable"""

from typing import Optional, Dict, Any
from agenticflow.agent.hybrid_rpavh_agent import HybridRPAVHAgent
from agenticflow.core.config import AgentConfig
from agenticflow.core.roles import AgentRole


class FileSystemAgentRules:
    """Optimized rules for filesystem operations."""
    
    def get_rules_text(self) -> str:
        return """🎯 FILESYSTEM AGENT - FAST & DECISIVE

MISSION: Discover, read, and analyze files efficiently with minimal delay.

APPROACH:
✅ Use rule-based planning (no LLM delays)
✅ Direct tool execution 
✅ Smart parameter inference from context
✅ Dependency-aware action sequencing

FILE DISCOVERY PATTERNS:
- "*.dtsx" → SSIS packages  
- "*.xml" → XML documents
- "*.json" → Configuration files
- Search paths: data/ssis, examples, current directory

ACTION SEQUENCING:
1. find_files → Discover matching files
2. read_text_fast → Read file contents  
3. file_stat → Get metadata (if requested)

ERROR RECOVERY:
- Path not found → Try parent directories
- Permission denied → Report and continue with accessible files
- No files found → Expand search patterns

COMPLETION CRITERIA:
✅ At least one file discovered and read
✅ Clear summary of files processed
✅ File content or metadata available"""


def create_hybrid_filesystem_agent(
    name: str = "hybrid_filesystem_agent",
    file_pattern: str = "*.dtsx", 
    search_root: str = "data/ssis",
    max_attempts: int = 2,
    use_llm_reflection: bool = False,  # Keep it fast
    model_name: str = ""
) -> HybridRPAVHAgent:
    """
    Create a fast, reliable filesystem agent using Hybrid RPAVH.
    
    Features:
    - Rule-based planning (no LLM delays)
    - Smart file discovery and reading
    - Automatic parameter inference
    - Fast error recovery
    
    Args:
        name: Agent identifier
        file_pattern: Default file pattern to search for
        search_root: Default search directory 
        max_attempts: Maximum retry attempts
        use_llm_reflection: Enable LLM reflection (adds delay but improves adaptation)
        model_name: LLM model for reflection (only used if enabled)
    """
    
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=0.0,  # Deterministic for filesystem ops
        role=AgentRole.FILE_MANAGER,
        capabilities=["file_discovery", "content_reading", "metadata_analysis"],
        system_prompt=f"""You are a high-performance filesystem agent optimized for speed and reliability.

Configuration:
- Pattern: {file_pattern}
- Search Root: {search_root} 
- Max Attempts: {max_attempts}

You use hybrid RPAVH execution:
- Fast rule-based planning
- Direct tool execution  
- Minimal LLM overhead
- Smart error recovery

Focus on speed and accuracy in file operations.""",
        rules=FileSystemAgentRules()
    )
    
    # Create hybrid agent with optimized settings
    agent = HybridRPAVHAgent(
        config=config,
        max_attempts=max_attempts,
        use_llm_reflection=use_llm_reflection,  # Usually False for speed
        use_llm_verification=False  # Keep verification fast
    )
    
    # Set static resources for rule-based planning
    agent.static_resources = {
        "file_pattern": file_pattern,
        "search_root": search_root,
        "supported_extensions": [".dtsx", ".xml", ".json", ".txt", ".md"],
        "fallback_patterns": ["*.*"],
        "search_locations": [search_root, ".", "examples", "data"],
        "max_files_to_read": 10,  # Reasonable limit
        "max_file_size_kb": 1024   # 1MB limit per file
    }
    
    # Disable auto-discovery; tools will be explicitly adopted by the flow/demo
    try:
        setattr(agent, "auto_discover", False)
    except Exception:
        pass
    return agent


def create_enhanced_hybrid_filesystem_agent(
    name: str = "enhanced_hybrid_fs",
    search_patterns: list = None,
    search_locations: list = None, 
    max_attempts: int = 3,
    enable_smart_reflection: bool = True,
    model_name: str = "llama3.2:latest"
) -> HybridRPAVHAgent:
    """
    Create an enhanced filesystem agent with smart adaptation.
    
    This version includes:
    - Multiple search patterns and locations
    - Smart LLM reflection on failures
    - Adaptive search strategies
    - Enhanced error recovery
    """
    
    if search_patterns is None:
        search_patterns = ["*.dtsx", "*.xml", "*.json", "*.txt"]
    if search_locations is None:
        search_locations = ["data/ssis", "examples", ".", "data"]
    
    class EnhancedFileSystemRules:
        def get_rules_text(self) -> str:
            return f"""🔍 ENHANCED FILESYSTEM AGENT - ADAPTIVE DISCOVERY

CONFIGURATION:
- Patterns: {search_patterns}
- Locations: {search_locations}
- Max Attempts: {max_attempts}
- Smart Reflection: {enable_smart_reflection}

ENHANCED CAPABILITIES:
- Multi-pattern discovery across locations
- Adaptive search expansion on failures  
- Smart LLM reflection for complex scenarios
- Progressive search strategy refinement

DISCOVERY STRATEGY:
1. Primary search: Use specified patterns in specified locations
2. Expansion search: Broaden patterns if nothing found
3. Fallback search: Search all locations with any pattern
4. Final search: Manual path specification

REFLECTION TRIGGERS:
- No files found after primary search
- Permission errors in multiple locations
- Unexpected file formats or structures
- User requests requiring interpretation

ADAPTATION PATTERNS:
- Empty results → Expand search scope
- Permission denied → Try alternative locations  
- Wrong file types → Adjust patterns
- Complex requests → Use LLM guidance"""
    
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=0.1,  # Slight creativity for adaptation
        role=AgentRole.DATA_COLLECTOR,
        capabilities=["multi_pattern_search", "adaptive_discovery", "smart_recovery"],
        system_prompt=f"""You are an enhanced filesystem agent with adaptive capabilities.

Search Configuration:
- Patterns: {search_patterns}
- Locations: {search_locations}

You combine fast rule-based planning with smart LLM reflection when needed for complex scenarios.""",
        rules=EnhancedFileSystemRules()
    )
    
    agent = HybridRPAVHAgent(
        config=config,
        max_attempts=max_attempts,
        use_llm_reflection=enable_smart_reflection,
        use_llm_verification=False  # Keep verification fast
    )
    
    agent.static_resources = {
        "search_patterns": search_patterns,
        "search_locations": search_locations,
        "expansion_patterns": ["*.*", "*.log", "*.cfg"],
        "fallback_locations": [".", "..", "~/"],
        "adaptation_enabled": enable_smart_reflection,
        "max_search_depth": 3,
        "concurrent_searches": len(search_locations) <= 3
    }
    
    return agent