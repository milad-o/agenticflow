"""Configuration management for AgenticFlow."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
from pydantic import BaseModel, Field
from agenticflow.agent.roles import AgentRole


class AgentConfig(BaseModel):
    """Configuration for an individual agent."""
    model_config = {"extra": "allow"}  # Allow extra fields
    
    name: str
    model: str = ""  # choose via provider/model factory (Groq or Ollama)
    temperature: float = 0.0
    tools: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    max_iterations: int = 10
    description: Optional[str] = None
    role: Optional[AgentRole] = None  # Agent's role for coordination
    
    # Additional fields commonly used by specialized agents
    capabilities: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    rules: Optional[Union[str, Dict[str, Any], object]] = None  # Operational rules for the agent


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator."""
    model: str = ""  # choose via provider/model factory (Groq or Ollama)
    temperature: float = 0.0
    max_parallel_tasks: int = 5
    retry_attempts: int = 3


class FlowConfig(BaseModel):
    """Main flow configuration."""
    name: str = "AgenticFlow"
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    tools: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    resources: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "FlowConfig":
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "FlowConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables
        if model := os.getenv("AGENTICFLOW_MODEL"):
            config.orchestrator.model = model
            
        if temp := os.getenv("AGENTICFLOW_TEMPERATURE"):
            config.orchestrator.temperature = float(temp)
            
        return config
    
    def merge_with_env(self) -> "FlowConfig":
        """Merge current config with environment variable overrides."""
        if model := os.getenv("AGENTICFLOW_MODEL"):
            self.orchestrator.model = model
            
        if temp := os.getenv("AGENTICFLOW_TEMPERATURE"):
            self.orchestrator.temperature = float(temp)
            
        return self