"""
Tool Card

Enhanced metadata layer for tools that integrates with existing ToolRegistry.
Provides intelligent matching and performance tracking for tools.
"""

import re
from typing import Dict, List, Any, Set, Optional
from langchain_core.tools import BaseTool

from .base_card import BaseCard, CardType, CardMetadata, MatchingCriteria
from ...registries import ToolRegistry


class ToolCard(BaseCard):
    """
    Enhanced metadata card for tools.
    
    Integrates with existing ToolRegistry to provide intelligent matching,
    performance tracking, and capability discovery.
    """
    
    def __init__(
        self,
        tool_name: str,
        description: str,
        tool_instance: Optional[BaseTool] = None,
        resource_types: List[str] = None,
        operation_type: str = "general",
        input_requirements: Dict[str, List[str]] = None,
        output_type: str = "mixed",
        performance_profile: Dict[str, str] = None,
        dependencies: List[str] = None,
        metadata: CardMetadata = None
    ):
        # Generate card_id from tool name
        card_id = f"tool:{tool_name}"
        
        super().__init__(
            card_id=card_id,
            name=tool_name,
            description=description,
            card_type=CardType.TOOL,
            metadata=metadata
        )
        
        self.tool_instance = tool_instance
        self.resource_types = resource_types or ["generic"]
        self.operation_type = operation_type
        self.input_requirements = input_requirements or {"required": [], "optional": []}
        self.output_type = output_type
        self.performance_profile = performance_profile or {}
        self.dependencies = dependencies or []
        
        # Auto-extract capabilities from tool properties
        self.capabilities = self._extract_capabilities()
    
    def _extract_capabilities(self) -> List[str]:
        """Extract capabilities from tool properties."""
        capabilities = []
        
        # Base capability from operation type
        capabilities.append(f"operation:{self.operation_type}")
        
        # Resource type capabilities
        for resource_type in self.resource_types:
            capabilities.append(f"resource:{resource_type}")
        
        # Output type capability
        capabilities.append(f"output:{self.output_type}")
        
        # Performance capabilities
        for perf_key, perf_value in self.performance_profile.items():
            if perf_value in ["fast", "high", "excellent"]:
                capabilities.append(f"performance:{perf_key}:high")
            elif perf_value in ["slow", "low", "poor"]:
                capabilities.append(f"performance:{perf_key}:low")
            else:
                capabilities.append(f"performance:{perf_key}:medium")
        
        # Tool-specific capabilities from name and description
        name_lower = self.name.lower()
        desc_lower = self.description.lower()
        
        # File operations
        if any(keyword in name_lower for keyword in ["file", "read", "write"]):
            capabilities.append("file_operations")
        
        # Search and discovery
        if any(keyword in name_lower for keyword in ["find", "search", "scan"]):
            capabilities.append("discovery")
        
        # Analysis and processing
        if any(keyword in name_lower for keyword in ["analyze", "process", "parse"]):
            capabilities.append("analysis")
        
        # Data operations
        if any(keyword in desc_lower for keyword in ["csv", "json", "data", "table"]):
            capabilities.append("data_processing")
        
        return capabilities
    
    def calculate_match_score(self, criteria: MatchingCriteria) -> float:
        """Calculate match score based on criteria."""
        score = 0.0
        
        # Required capabilities - must have all
        tool_capabilities = set(self.get_capabilities())
        required = criteria.required_capabilities
        
        if required and not required.issubset(tool_capabilities):
            return 0.0  # Missing required capabilities
        
        if required:
            score += 0.4  # Base score for meeting requirements
        
        # Preferred capabilities - bonus points
        preferred = criteria.preferred_capabilities
        if preferred:
            overlap = len(preferred.intersection(tool_capabilities))
            score += 0.3 * (overlap / len(preferred))
        
        # Excluded capabilities - penalty
        excluded = criteria.excluded_capabilities
        if excluded:
            excluded_present = len(excluded.intersection(tool_capabilities))
            score -= 0.2 * (excluded_present / len(excluded))
        
        # Performance requirements
        perf_req = criteria.performance_requirements
        if perf_req:
            perf_score = 0.0
            for req_key, req_value in perf_req.items():
                tool_value = self.performance_profile.get(req_key, "medium")
                if self._compare_performance(tool_value, req_value):
                    perf_score += 1.0
            if perf_req:
                score += 0.2 * (perf_score / len(perf_req))
        
        # Resource type compatibility
        if hasattr(criteria, 'resource_type'):
            if criteria.resource_type in self.resource_types or "generic" in self.resource_types:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _compare_performance(self, tool_value: str, required_value: str) -> bool:
        """Compare performance values."""
        performance_order = ["poor", "low", "medium", "high", "excellent"]
        
        try:
            tool_idx = performance_order.index(tool_value.lower())
            req_idx = performance_order.index(required_value.lower())
            return tool_idx >= req_idx
        except ValueError:
            return tool_value == required_value
    
    def get_capabilities(self) -> Set[str]:
        """Get all capabilities provided by this tool."""
        return set(self.capabilities)
    
    def get_dependencies(self) -> List[str]:
        """Get dependencies required by this tool."""
        return self.dependencies.copy()
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for this tool."""
        required_params = self.input_requirements.get("required", [])
        
        # Check all required parameters are present
        for param in required_params:
            if param not in parameters:
                return False
        
        # If tool instance is available, use its validation
        if self.tool_instance and hasattr(self.tool_instance, 'args_schema'):
            try:
                schema = self.tool_instance.args_schema
                if schema:
                    schema.model_validate(parameters)
                    return True
            except Exception:
                return False
        
        return True
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for this tool."""
        if self.tool_instance and hasattr(self.tool_instance, 'args_schema'):
            schema = self.tool_instance.args_schema
            if schema:
                return schema.model_json_schema()
        
        # Fallback to basic schema from input requirements
        return {
            "required": self.input_requirements.get("required", []),
            "optional": self.input_requirements.get("optional", []),
            "type": "object"
        }
    
    def can_handle_resource_type(self, resource_type: str) -> bool:
        """Check if tool can handle a specific resource type."""
        return resource_type in self.resource_types or "generic" in self.resource_types
    
    def get_estimated_execution_time(self) -> float:
        """Get estimated execution time based on performance profile and history."""
        # Use historical average if available
        if self._usage_stats["avg_execution_time"] > 0:
            return self._usage_stats["avg_execution_time"]
        
        # Fallback to performance profile
        speed = self.performance_profile.get("speed", "medium")
        speed_estimates = {
            "fast": 1.0,
            "medium": 3.0,
            "slow": 10.0
        }
        
        return speed_estimates.get(speed, 3.0)
    
    def is_compatible_with(self, other_tool: 'ToolCard') -> bool:
        """Check if this tool is compatible with another tool."""
        # Check if output of other tool matches our input requirements
        if other_tool.output_type in self.resource_types:
            return True
        
        # Check for complementary capabilities
        our_caps = self.get_capabilities()
        their_caps = other_tool.get_capabilities()
        
        # Look for producer/consumer relationships
        if "data_processing" in our_caps and "discovery" in their_caps:
            return True
        if "file_operations" in our_caps and "analysis" in their_caps:
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with tool-specific information."""
        base_dict = super().to_dict()
        base_dict.update({
            "resource_types": self.resource_types,
            "operation_type": self.operation_type,
            "input_requirements": self.input_requirements,
            "output_type": self.output_type,
            "performance_profile": self.performance_profile,
            "dependencies": self.dependencies,
            "parameter_schema": self.get_parameter_schema(),
            "estimated_execution_time": self.get_estimated_execution_time()
        })
        return base_dict
    
    @classmethod
    def create_from_tool(
        cls, 
        tool: BaseTool, 
        tool_registry: Optional[ToolRegistry] = None
    ) -> 'ToolCard':
        """
        Create a ToolCard from an existing BaseTool instance.
        
        Args:
            tool: The tool instance to create a card for
            tool_registry: Optional registry to get additional metadata
            
        Returns:
            ToolCard instance
        """
        # Extract basic information
        name = tool.name
        description = getattr(tool, 'description', f"Tool for {name} operations")
        
        # Analyze tool to extract metadata
        analyzer = ToolAnalyzer()
        resource_types = analyzer.infer_resource_types(name, description)
        operation_type = analyzer.infer_operation_type(name, description)
        input_requirements = analyzer.infer_input_requirements(name, description, tool)
        output_type = analyzer.infer_output_type(name, description)
        performance_profile = analyzer.infer_performance_profile(name, description)
        dependencies = analyzer.infer_dependencies(name)
        
        # Create metadata
        metadata = CardMetadata(
            source="tool_instance",
            confidence=0.9,
            tags={"auto_generated", "tool_registry"}
        )
        
        return cls(
            tool_name=name,
            description=description,
            tool_instance=tool,
            resource_types=resource_types,
            operation_type=operation_type,
            input_requirements=input_requirements,
            output_type=output_type,
            performance_profile=performance_profile,
            dependencies=dependencies,
            metadata=metadata
        )


class ToolAnalyzer:
    """Helper class for analyzing tools and extracting metadata."""
    
    def infer_resource_types(self, tool_name: str, description: str) -> List[str]:
        """Infer what resource types this tool can handle."""
        name_desc = (tool_name + " " + description).lower()
        resource_types = []
        
        patterns = {
            "file": ["file", "read", "write", "text"],
            "csv": ["csv", "comma", "spreadsheet"],
            "json": ["json", "javascript"],
            "xml": ["xml", "markup"],
            "pdf": ["pdf", "document"],
            "image": ["image", "png", "jpg", "visual"],
            "directory": ["directory", "folder", "find", "search"],
            "url": ["url", "web", "http", "fetch"]
        }
        
        for resource_type, keywords in patterns.items():
            if any(keyword in name_desc for keyword in keywords):
                resource_types.append(resource_type)
        
        return resource_types or ["generic"]
    
    def infer_operation_type(self, tool_name: str, description: str) -> str:
        """Infer the type of operation this tool performs."""
        name_desc = (tool_name + " " + description).lower()
        
        operations = {
            "read": ["read", "get", "fetch", "load", "extract"],
            "write": ["write", "save", "create", "generate"],
            "discovery": ["find", "search", "list", "scan"],
            "analysis": ["analyze", "process", "transform", "convert"],
            "validation": ["validate", "check", "verify", "test"]
        }
        
        for operation, keywords in operations.items():
            if any(keyword in name_desc for keyword in keywords):
                return operation
        
        return "utility"
    
    def infer_input_requirements(
        self, 
        tool_name: str, 
        description: str, 
        tool: BaseTool
    ) -> Dict[str, List[str]]:
        """Infer input requirements for this tool."""
        requirements = {"required": [], "optional": []}
        
        # Try to get from tool schema first
        if hasattr(tool, 'args_schema') and tool.args_schema:
            try:
                schema = tool.args_schema.model_json_schema()
                if 'required' in schema:
                    requirements['required'] = schema['required']
                properties = schema.get('properties', {})
                optional = [k for k in properties.keys() if k not in requirements['required']]
                requirements['optional'] = optional
                return requirements
            except Exception:
                pass
        
        # Fallback to heuristic analysis
        name_desc = (tool_name + " " + description).lower()
        
        if any(word in name_desc for word in ["file", "path"]):
            requirements["required"].append("path")
        if any(word in name_desc for word in ["pattern", "glob"]):
            requirements["required"].append("pattern")
        if any(word in name_desc for word in ["content", "text"]):
            requirements["required"].append("content")
        if any(word in name_desc for word in ["root", "directory"]):
            requirements["required"].append("root_path")
        
        return requirements
    
    def infer_output_type(self, tool_name: str, description: str) -> str:
        """Infer output type of this tool."""
        name_desc = (tool_name + " " + description).lower()
        
        if any(word in name_desc for word in ["list", "files", "array"]):
            return "list"
        elif any(word in name_desc for word in ["text", "content", "string"]):
            return "text"
        elif any(word in name_desc for word in ["json", "dict", "object"]):
            return "structured"
        elif any(word in name_desc for word in ["bool", "success", "valid"]):
            return "boolean"
        
        return "mixed"
    
    def infer_performance_profile(self, tool_name: str, description: str) -> Dict[str, str]:
        """Infer performance characteristics."""
        name_desc = (tool_name + " " + description).lower()
        
        speed = "medium"
        if any(word in name_desc for word in ["fast", "quick", "rapid"]):
            speed = "fast"
        elif any(word in name_desc for word in ["slow", "heavy", "complex"]):
            speed = "slow"
        
        scalability = "medium"
        if any(word in name_desc for word in ["chunk", "stream", "batch"]):
            scalability = "high"
        elif any(word in name_desc for word in ["atomic", "single"]):
            scalability = "low"
        
        return {
            "speed": speed,
            "scalability": scalability,
            "resource_usage": "medium"
        }
    
    def infer_dependencies(self, tool_name: str) -> List[str]:
        """Infer typical dependencies for this tool."""
        dependencies = []
        
        if tool_name == "read_text_fast":
            dependencies.append("find_files")
        elif tool_name == "write_text_atomic":
            dependencies.extend(["find_files", "read_text_fast"])
        elif "analyze" in tool_name:
            dependencies.extend(["find_files", "read_text_fast"])
        
        return dependencies