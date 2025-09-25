"""FileSystem Agent - Specialized for file system operations and data discovery."""

from typing import Dict, Any
from agenticflow.agent.agent import Agent
from agenticflow.core.config import AgentConfig
from agenticflow.core.roles import AgentRole
from agenticflow.core.rules import FileSystemAgentRules


def create_filesystem_agent(
    name: str = "filesystem_agent",
    temperature: float = 0.1,
    model_name: str = "",
    **kwargs
) -> Agent:
    """Create a pre-configured FileSystem agent.
    
    This agent is specialized for:
    - Finding and discovering files and directories
    - Reading file contents and metadata
    - Writing and creating files
    - Directory tree navigation
    - File system operations
    
    Args:
        name: Agent name (default: "filesystem_agent")
        temperature: LLM temperature for creativity (default: 0.1 for precision)
        model_name: Override default model
        **kwargs: Additional agent configuration including:
            - file_pattern: Pattern for file discovery (default: "*.dtsx")
            - search_root: Root directory for searches (default: "data/ssis")
            
    Returns:
        Configured FileSystem agent
    """
    # Pre-configure specialized tools for FileSystem operations
    # This agent should ONLY have file-related tools for specialization
    tools = []  # Will be populated when added to flow with specific tools
    
    # Filesystem-specific configuration
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=temperature,
        tools=[t.name for t in tools],
        tags=["filesystem", "data_discovery", "file_ops"],
        description="Specialized agent for file system operations, discovery, and data access",
        role=AgentRole.DATA_COLLECTOR
    )
    
    # Add additional config properties (these will be stored as extra fields)
    config.capabilities = ["file_read", "file_write", "dir_walk", "search", "file_meta"]
    
    # General system prompt for FileSystem agents
    config.system_prompt = """You are a FileSystem Agent specialized in file and directory operations.
    
Your primary capabilities:
- Discover and navigate file systems efficiently
- Read and analyze file contents with precision
- Gather file metadata and statistics
- Search for files matching specific patterns
- Provide structured file information to other agents

Best practices:
- Always use relative paths when working within a workspace
- Be precise with file operations to avoid errors
- Provide clear feedback about file operations
- Use appropriate tools for each task
- Handle errors gracefully and continue with valid operations"""
    
    # Add strict operational rules
    config.rules = FileSystemAgentRules(
        file_pattern=kwargs.get('file_pattern', '*.dtsx'),
        search_root=kwargs.get('search_root', 'data/ssis')
    )
    
    # Add any custom kwargs as extra fields (excluding the ones we already handled)
    rule_kwargs = {'file_pattern', 'search_root'}
    for key, value in kwargs.items():
        if key not in rule_kwargs:
            setattr(config, key, value)
    
    agent = Agent(
        config=config,
        tools=tools
    )
    
    return agent


def get_filesystem_agent_info() -> Dict[str, Any]:
    """Get information about the FileSystem agent."""
    return {
        "description": "Specialized for file system operations and data discovery",
        "role": AgentRole.DATA_COLLECTOR,
        "capabilities": ["file_read", "file_write", "dir_walk", "search", "file_meta"],
        "use_cases": ["File discovery", "Data extraction", "File operations", "Directory navigation"],
        "configurable_params": {
            "file_pattern": "Pattern for file discovery (default: '*.dtsx')",
            "search_root": "Root directory for searches (default: 'data/ssis')"
        }
    }