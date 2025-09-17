"""
Simple Unit tests for ToolRegistry
==================================

Basic tests for tool registration functionality that work with the current API.
"""

import pytest
import asyncio

from agenticflow.tools.registry import ToolRegistry


@pytest.mark.unit
class TestToolRegistrySimple:
    """Unit tests for ToolRegistry class."""
    
    def test_registry_initialization(self):
        """Test tool registry initialization."""
        registry = ToolRegistry()
        assert registry is not None
    
    def test_registry_creation(self):
        """Test that we can create multiple registries."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        
        assert registry1 is not None
        assert registry2 is not None
        assert registry1 is not registry2
    
    def test_registry_has_methods(self):
        """Test that registry has expected methods."""
        registry = ToolRegistry()
        
        # Check that expected methods exist
        assert hasattr(registry, 'register_function')
        assert callable(getattr(registry, 'register_function', None))
    
    def test_register_simple_function(self):
        """Test registering a simple function."""
        registry = ToolRegistry()
        
        def simple_func(x: int) -> int:
            """A simple test function."""
            return x * 2
        
        # This should not raise an exception
        try:
            registry.register_function(
                name="double",
                description="Double a number",
                func=simple_func
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_register_function_with_decorator(self):
        """Test using the tool decorator."""
        from agenticflow.tools.registry import tool
        
        registry = ToolRegistry()
        
        @tool(name="test_tool", description="A test tool", registry=registry)
        def test_function(value: str) -> str:
            """Test function for decoration."""
            return f"processed: {value}"
        
        # If decoration worked, function should still be callable
        result = test_function("hello")
        assert result == "processed: hello"
    
    def test_multiple_function_registration(self):
        """Test registering multiple functions."""
        registry = ToolRegistry()
        
        def func1():
            return "func1"
        
        def func2():
            return "func2"
        
        # Register multiple functions
        try:
            registry.register_function("tool1", "Tool 1", func1)
            registry.register_function("tool2", "Tool 2", func2)
            success = True
        except Exception:
            success = False
        
        assert success is True