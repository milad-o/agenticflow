"""
Configuration and settings management for AgenticFlow.

Provides Pydantic models for configuration with environment variable support
and validation for LLM providers, agents, and system-wide settings.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GROQ = "groq"
    OLLAMA = "ollama"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorRecoveryStrategy(str, Enum):
    """Error recovery strategies for agents."""
    RETRY = "retry"
    ESCALATE = "escalate"
    REPHRASE = "rephrase"
    SKIP = "skip"


class ExecutionMode(str, Enum):
    """Agent execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    GRAPH = "graph"
    CONTROLLED = "controlled"


class LLMProviderConfig(BaseModel):
    """Configuration for a specific LLM provider."""
    
    provider: LLMProvider = Field(..., description="The LLM provider type")
    model: str = Field(..., description="Model name/identifier")
    api_key: Optional[SecretStr] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Custom base URL for the provider")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    timeout: int = Field(30, ge=1, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, description="Maximum number of retries")
    
    @field_validator('api_key', mode='before')
    @classmethod
    def validate_api_key(cls, v: Union[str, SecretStr, None]) -> Optional[SecretStr]:
        """Validate and convert API key to SecretStr."""
        if v is None:
            return None
        if isinstance(v, str):
            return SecretStr(v)
        return v


class EmbeddingConfig(BaseModel):
    """Configuration for embedding models."""
    
    provider: LLMProvider = Field(LLMProvider.OPENAI, description="Provider for embeddings")
    model: str = Field("text-embedding-3-small", description="Embedding model name")
    api_key: Optional[SecretStr] = Field(None, description="API key for embeddings")
    dimensions: Optional[int] = Field(None, ge=1, description="Embedding dimensions")
    batch_size: int = Field(100, ge=1, description="Batch size for embedding requests")


class MemoryConfig(BaseModel):
    """Configuration for agent memory systems."""
    
    type: str = Field("buffer", description="Memory type (buffer, retrieval, etc.)")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to store")
    max_messages: Optional[int] = Field(None, ge=1, description="Maximum messages to store")
    
    # Retrieval memory specific
    vector_store_path: Optional[str] = Field(None, description="Path for vector store persistence")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold for retrieval")
    max_retrievals: int = Field(5, ge=1, description="Maximum number of retrievals")


class ToolSelectionStrategy(str, Enum):
    """Tool selection strategies for controlled execution mode."""
    RULE_BASED = "rule_based"
    LLM_GUIDED = "llm_guided"
    CUSTOM = "custom"


class AgentConfig(BaseModel):
    """Configuration for individual agents."""
    
    name: str = Field(..., description="Agent name/identifier")
    description: Optional[str] = Field(None, description="Agent description")
    instructions: Optional[str] = Field(None, description="System prompt/instructions")
    llm: LLMProviderConfig = Field(..., description="LLM configuration")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="Memory configuration")
    
    execution_mode: ExecutionMode = Field(ExecutionMode.SEQUENTIAL, description="Execution mode")
    max_retries: int = Field(3, ge=0, description="Maximum retries for tasks")
    error_recovery: ErrorRecoveryStrategy = Field(ErrorRecoveryStrategy.RETRY, description="Error recovery strategy")
    
    tools: List[str] = Field(default_factory=list, description="List of tool names/identifiers")
    mcp_servers: List[str] = Field(default_factory=list, description="List of MCP server URLs")
    
    # Tool selection configuration for CONTROLLED execution mode
    tool_selection_strategy: ToolSelectionStrategy = Field(ToolSelectionStrategy.RULE_BASED, description="Tool selection strategy for controlled mode")
    custom_tool_selector_class: Optional[str] = Field(None, description="Custom tool selector class path (e.g., 'module.class')")
    tool_selection_rules: Optional[Dict[str, List[str]]] = Field(None, description="Custom rules for rule-based tool selection")
    
    enable_self_verification: bool = Field(True, description="Enable self-verification after actions")
    enable_a2a_communication: bool = Field(True, description="Enable agent-to-agent communication")


class SupervisorConfig(AgentConfig):
    """Configuration for supervisor agents."""
    
    max_sub_agents: int = Field(10, ge=1, description="Maximum number of sub-agents")
    task_decomposition_prompt: Optional[str] = Field(None, description="Custom task decomposition prompt")
    planning_depth: int = Field(3, ge=1, description="Maximum planning depth")
    enable_reflection: bool = Field(True, description="Enable reflection on results")


class TaskConfig(BaseModel):
    """Configuration for task management."""
    
    max_concurrent_tasks: int = Field(10, ge=1, description="Maximum concurrent tasks")
    task_timeout: int = Field(300, ge=1, description="Task timeout in seconds")
    enable_priorities: bool = Field(True, description="Enable task prioritization")
    enable_dependencies: bool = Field(True, description="Enable task dependencies")
    
    # Queue configuration
    queue_max_size: int = Field(1000, ge=1, description="Maximum queue size")
    retry_delay: int = Field(5, ge=1, description="Retry delay in seconds")




class A2AConfig(BaseModel):
    """Configuration for Agent-to-Agent communication."""
    
    enable_a2a: bool = Field(True, description="Enable A2A communication")
    message_timeout: int = Field(30, ge=1, description="Message timeout in seconds")
    max_message_size: int = Field(1024 * 1024, ge=1, description="Maximum message size in bytes")
    
    # Communication patterns
    enable_broadcast: bool = Field(True, description="Enable broadcast messages")
    enable_direct_messaging: bool = Field(True, description="Enable direct agent messaging")
    
    # Reliability
    enable_message_persistence: bool = Field(False, description="Enable message persistence")
    max_retries: int = Field(3, ge=0, description="Maximum message send retries")


class HITLConfig(BaseModel):
    """Configuration for Human-in-the-Loop functionality."""
    
    enable_hitl: bool = Field(False, description="Enable HITL globally")
    confirmation_required: bool = Field(True, description="Require confirmation for critical actions")
    timeout: int = Field(300, ge=1, description="HITL response timeout in seconds")
    
    # Notification methods
    enable_console: bool = Field(True, description="Enable console notifications")
    enable_webhook: bool = Field(False, description="Enable webhook notifications")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")


class AgenticFlowConfig(BaseSettings):
    """Main configuration class for AgenticFlow."""
    
    model_config = SettingsConfigDict(
        env_prefix="AGENTICFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Global settings
    debug: bool = Field(False, description="Enable debug mode")
    log_level: LogLevel = Field(LogLevel.INFO, description="Logging level")
    log_file: Optional[str] = Field(None, description="Log file path")
    
    # Default LLM provider
    default_llm: LLMProviderConfig = Field(
        default_factory=lambda: LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            temperature=0.0
        ),
        description="Default LLM configuration"
    )
    
    # Embedding configuration
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig, description="Embedding configuration")
    
    # Component configurations
    task_config: TaskConfig = Field(default_factory=TaskConfig, description="Task management configuration")
    a2a_config: A2AConfig = Field(default_factory=A2AConfig, description="A2A communication configuration")
    hitl_config: HITLConfig = Field(default_factory=HITLConfig, description="HITL configuration")
    
    # Agent configurations
    agents: List[AgentConfig] = Field(default_factory=list, description="Agent configurations")
    supervisor: Optional[SupervisorConfig] = Field(None, description="Supervisor configuration")
    
    # System paths
    workspace_path: Path = Field(Path.cwd(), description="Workspace directory path")
    cache_path: Optional[Path] = Field(None, description="Cache directory path")
    
    @field_validator('cache_path', mode='before')
    @classmethod
    def set_cache_path(cls, v: Optional[Union[str, Path]]) -> Optional[Path]:
        """Set cache path with default if not provided."""
        if v is None:
            return Path.home() / ".agenticflow" / "cache"
        return Path(v) if isinstance(v, str) else v
    
    @field_validator('workspace_path', mode='before')
    @classmethod
    def set_workspace_path(cls, v: Union[str, Path]) -> Path:
        """Convert workspace path to Path object."""
        return Path(v) if isinstance(v, str) else v
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to create directories and set defaults."""
        # Create cache directory if it doesn't exist
        if self.cache_path:
            self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Set API keys from environment if not provided
        self._set_api_keys_from_env()
    
    def _set_api_keys_from_env(self) -> None:
        """Set API keys from environment variables if not already set."""
        # Load .env file if it exists
        from pathlib import Path
        env_file = Path(".env")
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        env_mappings = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.GROQ: "GROQ_API_KEY", 
            LLMProvider.OLLAMA: None  # Ollama doesn't require API key
        }
        
        # Set default LLM API key
        if not self.default_llm.api_key and env_mappings.get(self.default_llm.provider):
            env_key = env_mappings[self.default_llm.provider]
            if env_key and os.getenv(env_key):
                self.default_llm.api_key = SecretStr(os.getenv(env_key))
        
        # Set embedding API key
        if not self.embedding.api_key and env_mappings.get(self.embedding.provider):
            env_key = env_mappings[self.embedding.provider]
            if env_key and os.getenv(env_key):
                self.embedding.api_key = SecretStr(os.getenv(env_key))
        
        # Set agent LLM API keys
        for agent in self.agents:
            if not agent.llm.api_key and env_mappings.get(agent.llm.provider):
                env_key = env_mappings[agent.llm.provider]
                if env_key and os.getenv(env_key):
                    agent.llm.api_key = SecretStr(os.getenv(env_key))
        
        # Set supervisor LLM API key
        if self.supervisor and not self.supervisor.llm.api_key and env_mappings.get(self.supervisor.llm.provider):
            env_key = env_mappings[self.supervisor.llm.provider]
            if env_key and os.getenv(env_key):
                self.supervisor.llm.api_key = SecretStr(os.getenv(env_key))
    
    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """Get agent configuration by name."""
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    def add_agent(self, agent_config: AgentConfig) -> None:
        """Add an agent configuration."""
        # Remove existing agent with same name
        self.agents = [a for a in self.agents if a.name != agent_config.name]
        self.agents.append(agent_config)
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent configuration by name."""
        initial_count = len(self.agents)
        self.agents = [a for a in self.agents if a.name != name]
        return len(self.agents) < initial_count


# Global configuration instance
config = AgenticFlowConfig()


def load_config(config_path: Optional[Union[str, Path]] = None) -> AgenticFlowConfig:
    """Load configuration from file."""
    global config
    
    if config_path:
        config_path = Path(config_path)
        if config_path.exists():
            if config_path.suffix.lower() in ('.yaml', '.yml'):
                import yaml
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                config = AgenticFlowConfig(**config_data)
            elif config_path.suffix.lower() == '.json':
                import json
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                config = AgenticFlowConfig(**config_data)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
    
    return config


def get_config() -> AgenticFlowConfig:
    """Get the global configuration instance."""
    return config