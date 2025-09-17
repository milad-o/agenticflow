"""
Tool selection logic for agent-controlled orchestration.

Provides base classes and implementations for determining which tools
an agent should use based on task analysis, rather than letting the LLM decide.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Set, Pattern
import re
from ..tools.base_tool import ToolRegistry


class ToolSelector(ABC):
    """Base class for tool selection strategies."""
    
    def __init__(self, tool_registry: ToolRegistry):
        """Initialize with tool registry."""
        self.tool_registry = tool_registry
    
    @abstractmethod
    def select_tools(self, task: str, context: Dict[str, Any] = None) -> List[str]:
        """
        Select tools needed for a given task.
        
        Args:
            task: The task description
            context: Optional context information
            
        Returns:
            List of tool names that should be used
        """
        pass
    
    def get_available_tools(self) -> Set[str]:
        """Get set of available tool names."""
        return set(self.tool_registry.list_tools()) if self.tool_registry else set()


class RuleBasedToolSelector(ToolSelector):
    """Rule-based tool selection using pattern matching."""
    
    def __init__(self, tool_registry: ToolRegistry, rules: Dict[str, List[Pattern]] = None):
        """
        Initialize with tool registry and optional custom rules.
        
        Args:
            tool_registry: Tool registry instance
            rules: Dict mapping tool names to list of regex patterns
        """
        super().__init__(tool_registry)
        self.rules = rules or self._default_rules()
    
    def _default_rules(self) -> Dict[str, List[Pattern]]:
        """Default pattern matching rules for common mathematical operations."""
        return {
            'add': [
                re.compile(r'\badd\b', re.IGNORECASE),
                re.compile(r'\bplus\b', re.IGNORECASE),
                re.compile(r'\+', re.IGNORECASE),
                re.compile(r'\bsum\b', re.IGNORECASE),
                re.compile(r'\badding\b', re.IGNORECASE),
            ],
            'multiply': [
                re.compile(r'\bmultipl\w*\b', re.IGNORECASE),
                re.compile(r'\btimes\b', re.IGNORECASE),
                re.compile(r'×', re.IGNORECASE),
                re.compile(r'\*', re.IGNORECASE),
                re.compile(r'\bproduct\b', re.IGNORECASE),
            ],
            'square': [
                re.compile(r'\bsquare\w*\b', re.IGNORECASE),
                re.compile(r'²', re.IGNORECASE),
                re.compile(r'\^2\b', re.IGNORECASE),
            ],
            'divide': [
                re.compile(r'\bdivide\w*\b', re.IGNORECASE),
                re.compile(r'÷', re.IGNORECASE),
                re.compile(r'/', re.IGNORECASE),
                re.compile(r'\bquotient\b', re.IGNORECASE),
            ],
            'subtract': [
                re.compile(r'\bsubtract\w*\b', re.IGNORECASE),
                re.compile(r'\bminus\b', re.IGNORECASE),
                re.compile(r'-', re.IGNORECASE),
                re.compile(r'\bdifference\b', re.IGNORECASE),
            ]
        }
    
    def select_tools(self, task: str, context: Dict[str, Any] = None) -> List[str]:
        """Select tools based on pattern matching rules."""
        available_tools = self.get_available_tools()
        selected_tools = []
        
        # Apply pattern matching with fuzzy tool name matching
        for rule_name, patterns in self.rules.items():
            # Find actual tool name that matches this rule
            matching_tool = self._find_matching_tool(rule_name, available_tools)
            if matching_tool:
                for pattern in patterns:
                    if pattern.search(task):
                        if matching_tool not in selected_tools:
                            selected_tools.append(matching_tool)
                        break  # Found match for this tool, move to next
        
        # Handle complex patterns that require multiple tools
        selected_tools = self._handle_complex_patterns_with_mapping(task, selected_tools, available_tools)
        
        return selected_tools
    
    def _find_matching_tool(self, rule_name: str, available_tools: Set[str]) -> str:
        """Find actual tool name that matches a rule name."""
        # Exact match first
        if rule_name in available_tools:
            return rule_name
        
        # Pattern matching for similar names
        for tool in available_tools:
            tool_lower = tool.lower()
            rule_lower = rule_name.lower()
            
            # Check if rule name is contained in tool name
            if rule_lower in tool_lower or tool_lower.startswith(rule_lower):
                return tool
            
            # Handle common patterns
            if rule_lower == 'add' and ('add' in tool_lower or 'sum' in tool_lower):
                return tool
            elif rule_lower == 'multiply' and ('multiply' in tool_lower or 'mult' in tool_lower):
                return tool
            elif rule_lower == 'square' and 'square' in tool_lower:
                return tool
            elif rule_lower == 'divide' and ('divide' in tool_lower or 'div' in tool_lower):
                return tool
        
        return None
    
    def _handle_complex_patterns_with_mapping(self, task: str, selected_tools: List[str], available_tools: Set[str]) -> List[str]:
        """Handle complex patterns that require specific tool combinations."""
        task_lower = task.lower()
        
        # Find actual tool names for common operations
        square_tool = self._find_matching_tool('square', available_tools)
        multiply_tool = self._find_matching_tool('multiply', available_tools)
        add_tool = self._find_matching_tool('add', available_tools)
        
        # Pattern: "square of X then multiply by Y" 
        if square_tool in selected_tools and multiply_tool in selected_tools:
            if 'square' in task_lower and ('then' in task_lower or 'multiply' in task_lower):
                # Reorder to square first, then multiply
                return [square_tool, multiply_tool]
        
        # Pattern: "First add X + Y, then multiply by Z"
        if add_tool in selected_tools and multiply_tool in selected_tools:
            if any(word in task_lower for word in ['first', 'then', 'after']):
                # Sequential execution: add first, then multiply
                return [add_tool, multiply_tool]
        
        # Pattern: Mathematical expressions with parentheses
        if '(' in task and ')' in task:
            if '+' in task and any(op in task for op in ['×', '*']):
                # Expression like (a + b) × c
                tools = []
                if add_tool: tools.append(add_tool)
                if multiply_tool: tools.append(multiply_tool)
                return tools if tools else selected_tools
        
        return selected_tools
    
    def add_custom_rule(self, tool_name: str, pattern: str) -> None:
        """Add a custom pattern rule for a tool."""
        if tool_name not in self.rules:
            self.rules[tool_name] = []
        self.rules[tool_name].append(re.compile(pattern, re.IGNORECASE))


class LLMGuidedToolSelector(ToolSelector):
    """LLM-guided tool selection with structured prompting."""
    
    def __init__(self, tool_registry: ToolRegistry, llm_provider=None):
        """Initialize with tool registry and LLM provider."""
        super().__init__(tool_registry)
        self.llm_provider = llm_provider
    
    async def select_tools_async(self, task: str, context: Dict[str, Any] = None) -> List[str]:
        """Select tools using LLM guidance (async version)."""
        if not self.llm_provider:
            raise ValueError("LLM provider required for LLM-guided selection")
        
        available_tools = list(self.get_available_tools())
        if not available_tools:
            return []
        
        # Create structured prompt for tool selection only
        prompt = f"""
Task: {task}

Available tools: {', '.join(available_tools)}

Analyze the task and determine which tools are needed. Consider:
1. What operations need to be performed?
2. In what order should they be executed?
3. What are the dependencies between operations?

Respond ONLY with a JSON list of tool names in execution order:
["tool1", "tool2", "tool3"]

If no tools are needed, respond with: []

Tools needed:"""
        
        from langchain_core.messages import HumanMessage
        response = await self.llm_provider.agenerate([HumanMessage(content=prompt)])
        
        # Parse JSON response
        import json
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                tools = json.loads(json_str)
                # Filter to only available tools
                return [tool for tool in tools if tool in available_tools]
        except Exception:
            pass
        
        return []
    
    def select_tools(self, task: str, context: Dict[str, Any] = None) -> List[str]:
        """Synchronous version - raises error as LLM calls are async."""
        raise NotImplementedError("Use select_tools_async for LLM-guided selection")