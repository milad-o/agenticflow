"""
Parameter extraction logic for agent-controlled orchestration.

Provides components for extracting function parameters from natural language
using LLM with structured prompting and validation.
"""

import json
from typing import Dict, Any, Type, Optional
from langchain_core.messages import HumanMessage


class ParameterExtractor:
    """Extract function parameters from natural language using LLM."""
    
    def __init__(self, llm_provider=None):
        """Initialize with LLM provider."""
        self.llm_provider = llm_provider
    
    async def extract_parameters(
        self, 
        task: str, 
        tool_name: str, 
        param_schema: Dict[str, Type],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract parameters for a specific tool using LLM.
        
        Args:
            task: The task description
            tool_name: Name of the tool
            param_schema: Dict mapping parameter names to their types
            context: Optional context from previous tool executions
            
        Returns:
            Dict of extracted parameters
        """
        if not self.llm_provider:
            raise ValueError("LLM provider required for parameter extraction")
        
        # Create example JSON with actual parameter names
        param_names = list(param_schema.keys())
        param_types = [t.__name__ for t in param_schema.values()]
        example_json = {name: f"value_{i+1}" for i, name in enumerate(param_names)}
        
        # Include context if available
        context_info = ""
        if context:
            context_info = f"\nPrevious results: {context}\n"
        
        extraction_prompt = f"""
Task: {task}{context_info}

I need to extract parameters for the '{tool_name}' function.
The function requires these parameters: {dict(zip(param_names, param_types))}

Please extract ONLY the parameter values from the task and respond with valid JSON using these EXACT parameter names:
{json.dumps(example_json)}

IMPORTANT: 
- Only provide the JSON object, no other text
- Use these exact parameter names: {param_names}
- Ensure values match the required types: {param_types}
- Extract numbers from the task text
- If a value cannot be determined from the task, use null

JSON:"""
        
        response = await self.llm_provider.agenerate([HumanMessage(content=extraction_prompt)])
        
        return self._parse_response(response, param_schema)
    
    def _parse_response(self, response: str, param_schema: Dict[str, Type]) -> Dict[str, Any]:
        """Parse LLM response and validate parameter types."""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                params = json.loads(json_str)
                
                # Type conversion and validation
                validated_params = {}
                for param_name, param_type in param_schema.items():
                    if param_name in params and params[param_name] is not None:
                        try:
                            validated_params[param_name] = self._convert_type(
                                params[param_name], param_type
                            )
                        except (ValueError, TypeError) as e:
                            raise ValueError(f"Invalid value for parameter '{param_name}': {e}")
                    else:
                        # Parameter missing or null
                        if param_name in params:
                            validated_params[param_name] = None
                        # If not present, will be missing from validated_params
                
                return validated_params
            else:
                raise ValueError("No JSON found in response")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}")
    
    def _convert_type(self, value: Any, target_type: Type) -> Any:
        """Convert value to target type with validation."""
        if target_type == int:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str) and value.isdigit():
                return int(value)
            else:
                raise ValueError(f"Cannot convert '{value}' to int")
        
        elif target_type == float:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    raise ValueError(f"Cannot convert '{value}' to float")
        
        elif target_type == str:
            return str(value)
        
        elif target_type == bool:
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(value, int):
                return bool(value)
            else:
                raise ValueError(f"Cannot convert '{value}' to bool")
        
        else:
            # Try direct type conversion
            try:
                return target_type(value)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert '{value}' to {target_type.__name__}")


class ContextualParameterExtractor(ParameterExtractor):
    """Enhanced parameter extractor that considers context from previous tool executions."""
    
    def __init__(self, llm_provider=None):
        super().__init__(llm_provider)
        self.execution_history = []
    
    async def extract_parameters(
        self, 
        task: str, 
        tool_name: str, 
        param_schema: Dict[str, Type],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Extract parameters with enhanced context awareness."""
        # Merge execution history with provided context
        full_context = {}
        if self.execution_history:
            full_context["previous_results"] = self.execution_history[-3:]  # Last 3 results
        if context:
            full_context.update(context)
        
        return await super().extract_parameters(task, tool_name, param_schema, full_context)
    
    def add_execution_result(self, tool_name: str, parameters: Dict[str, Any], result: Any):
        """Add execution result to context history."""
        self.execution_history.append({
            "tool": tool_name,
            "parameters": parameters,
            "result": result
        })
        
        # Keep only recent history (last 10 executions)
        if len(self.execution_history) > 10:
            self.execution_history = self.execution_history[-10:]
    
    def clear_history(self):
        """Clear execution history."""
        self.execution_history = []