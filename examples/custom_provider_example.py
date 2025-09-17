#!/usr/bin/env python3
"""
Custom Provider Example: Adding Anthropic Claude to AgenticFlow
===============================================================

This example demonstrates how to add a custom LLM provider to AgenticFlow.
We'll add Anthropic Claude as an example, showing the complete process
from provider implementation to usage.
"""

import asyncio
from pathlib import Path
import sys

# Add the src directory to path for examples
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# Import base classes
from agenticflow.llm_providers.base import AsyncLLMProvider, EmbeddingNotSupportedError
from agenticflow.config.settings import LLMProviderConfig, LLMProvider
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage


class AnthropicProvider(AsyncLLMProvider):
    """
    Example Anthropic Claude provider implementation.
    
    NOTE: This is a demonstration. For production use, you would:
    1. Install: pip install langchain-anthropic
    2. Use: from langchain_anthropic import ChatAnthropic
    """
    
    @property
    def supports_embeddings(self) -> bool:
        """Anthropic doesn't provide embeddings currently."""
        return False
    
    def _create_llm(self) -> BaseLanguageModel:
        """Create Anthropic LLM instance."""
        # For this example, we'll simulate the ChatAnthropic interface
        # In reality, you would use:
        # from langchain_anthropic import ChatAnthropic
        # return ChatAnthropic(...)
        
        print(f"🔧 Would create ChatAnthropic with:")
        print(f"   - model: {self.config.model}")
        print(f"   - temperature: {self.config.temperature}")
        print(f"   - max_tokens: {self.config.max_tokens}")
        
        # Return a mock LLM for demonstration
        return MockAnthropicLLM(self.config)
    
    def _create_embeddings(self):
        """Anthropic doesn't provide embeddings."""
        raise EmbeddingNotSupportedError("Anthropic doesn't support embeddings")


class MockAnthropicLLM:
    """Mock LLM for demonstration purposes."""
    
    def __init__(self, config):
        self.config = config
    
    async def agenerate(self, messages, **kwargs):
        """Mock generation method."""
        from langchain_core.outputs import LLMResult, Generation
        
        # Simulate Anthropic response
        content = f"Hello! I'm Claude ({self.config.model}), simulated for this example. " \
                 f"In reality, I would process your message and respond appropriately."
        
        generation = Generation(text=content)
        return LLMResult(generations=[[generation]])


async def demonstrate_custom_provider():
    """Demonstrate adding and using a custom provider."""
    
    print("🎨 CUSTOM PROVIDER EXAMPLE: ADDING ANTHROPIC CLAUDE")
    print("=" * 60)
    print()
    
    # Step 1: Create provider configuration
    print("📋 Step 1: Create Provider Configuration")
    
    # Extend the LLMProvider enum (in practice, you'd do this in settings.py)
    # LLMProvider.ANTHROPIC = "anthropic"  # This would be added to the enum
    
    # NOTE: This would fail with current enum validation
    # config = LLMProviderConfig(
    #     provider="anthropic",  # This fails - not in enum yet
    #     model="claude-3-sonnet-20240229",
    #     temperature=0.7,
    #     max_tokens=4096
    # )
    
    # Instead, let's use an existing provider for the config demo
    config = LLMProviderConfig(
        provider=LLMProvider.OPENAI,  # Using existing provider for demo
        model="claude-3-sonnet-20240229",  # But with Claude model name
        temperature=0.7,
        max_tokens=4096
    )
    
    print("📝 Note: Using OPENAI provider enum for demo")
    print("    In production, you'd add ANTHROPIC to the enum first")
    print(f"✅ Created config for model: {config.model}")
    print()
    
    # Step 2: Create provider instance
    print("📋 Step 2: Create Provider Instance")
    provider = AnthropicProvider(config)
    print(f"✅ Created AnthropicProvider")
    print(f"   Supports embeddings: {provider.supports_embeddings}")
    print()
    
    # Step 3: Test provider functionality
    print("📋 Step 3: Test Provider Functionality")
    
    # Test LLM creation
    llm = provider.llm  # This triggers _create_llm
    print("✅ LLM instance created successfully")
    print()
    
    # Test message generation
    print("📋 Step 4: Test Message Generation")
    messages = [HumanMessage(content="Hello, how are you?")]
    
    try:
        response = await provider.agenerate(messages)
        print(f"✅ Generated response:")
        print(f"   {response[:100]}...")
    except Exception as e:
        print(f"📝 Note: {e}")
    print()
    
    # Step 5: Show how it would integrate with factory
    print("📋 Step 5: Integration with Factory Pattern")
    print("In production, you would:")
    print("1. Add ANTHROPIC to LLMProvider enum in config/settings.py")
    print("2. Import AnthropicProvider in llm_providers/factory.py")
    print("3. Add to _providers dict: LLMProvider.ANTHROPIC: AnthropicProvider")
    print("4. Export in llm_providers/__init__.py")
    print()
    
    print("🎉 Custom provider example completed!")
    print("📚 This shows how easy it is to extend AgenticFlow with new providers.")


async def show_real_world_usage():
    """Show how the custom provider would be used in practice."""
    
    print()
    print("💼 REAL-WORLD USAGE EXAMPLE")
    print("=" * 40)
    print()
    
    # Show the code that users would write
    usage_code = '''
# After adding Anthropic to the framework:

from agenticflow import Agent, AgentConfig, LLMProviderConfig, LLMProvider

# Create agent with Anthropic Claude
config = AgentConfig(
    name="claude_agent",
    llm=LLMProviderConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-sonnet-20240229",
        api_key="your-anthropic-api-key",
        temperature=0.7,
        max_tokens=4096
    )
)

agent = Agent(config)
await agent.start()

# Use exactly like any other provider
result = await agent.execute_task("Analyze this data and provide insights")
print(result["response"])

await agent.stop()
'''
    
    print("📝 User Code:")
    print(usage_code)
    
    # Show the framework benefits
    print("🚀 Framework Benefits:")
    print("✅ Consistent API across all providers")
    print("✅ Automatic failover support")
    print("✅ Built-in retry logic")
    print("✅ Same tool integration")
    print("✅ Same memory systems")
    print("✅ Same agent features")


if __name__ == "__main__":
    asyncio.run(demonstrate_custom_provider())
    asyncio.run(show_real_world_usage())