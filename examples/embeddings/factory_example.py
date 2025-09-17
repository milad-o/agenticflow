#!/usr/bin/env python3
"""
Embedding Factory Example
=========================

This example demonstrates how to use the embedding factory functions
to easily create and manage embedding providers.
"""

import asyncio
import sys
import os

# Add the src directory to the path so we can import agenticflow
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

try:
    from agenticflow.embeddings import (
        create_embedding_provider,
        create_auto_provider,
        list_available_providers,
        get_default_model,
        auto_select_provider,
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure AgenticFlow is properly installed")
    sys.exit(1)


async def demonstrate_provider_listing():
    """Demonstrate listing available providers."""
    print("🔍 Available Embedding Providers:")
    print("=" * 50)
    
    providers = list_available_providers()
    
    for name, info in providers.items():
        status = "✅" if info['available'] else "❌"
        local_indicator = "🏠" if info['local'] else "☁️"
        
        print(f"{status} {local_indicator} {name.upper()}")
        print(f"   Default model: {info['default_model']}")
        print(f"   Status: {info['reason']}")
        print()


async def demonstrate_auto_selection():
    """Demonstrate automatic provider selection."""
    print("\n🤖 Automatic Provider Selection:")
    print("=" * 50)
    
    # Try different selection criteria
    scenarios = [
        {
            "name": "Default (any available)",
            "preferred_providers": None,
            "requirements": None,
        },
        {
            "name": "Local only",
            "preferred_providers": None,
            "requirements": {"local_only": True},
        },
        {
            "name": "Cloud preferred",
            "preferred_providers": ["openai", "cohere", "huggingface"],
            "requirements": None,
        },
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        try:
            selection = auto_select_provider(
                preferred_providers=scenario['preferred_providers'],
                requirements=scenario['requirements']
            )
            print(f"   ✅ Selected: {selection['provider']} with model {selection['model']}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")


async def demonstrate_factory_creation():
    """Demonstrate using factory to create providers."""
    print("\n🏭 Factory Provider Creation:")
    print("=" * 50)
    
    # List of providers to try
    provider_configs = [
        {"provider": "openai", "model": "text-embedding-3-small"},
        {"provider": "huggingface", "model": "sentence-transformers/all-MiniLM-L6-v2"},
        {"provider": "cohere", "model": "embed-english-light-v3.0"},
        {"provider": "ollama", "model": "nomic-embed-text"},
    ]
    
    for config in provider_configs:
        provider_name = config["provider"]
        model_name = config["model"]
        
        print(f"\n🔧 Trying {provider_name.upper()} provider...")
        try:
            provider = create_embedding_provider(
                provider=provider_name,
                model=model_name
            )
            
            # Test availability
            is_available = await provider.is_available()
            if is_available:
                print(f"   ✅ Provider created and available")
                
                # Get model info
                info = provider.get_model_info()
                print(f"   📊 Model: {info['model']}")
                print(f"   📐 Dimension: {info.get('dimension', 'Unknown')}")
                print(f"   🔢 Max batch size: {info['max_batch_size']}")
                
                # Test a simple embedding
                try:
                    embedding = await provider.embed_text("Hello, world!")
                    print(f"   🧪 Test embedding dimension: {len(embedding)}")
                except Exception as e:
                    print(f"   ⚠️ Test embedding failed: {e}")
            else:
                print(f"   ❌ Provider created but not available")
                
            # Cleanup
            if hasattr(provider, 'close'):
                await provider.close()
                
        except Exception as e:
            print(f"   ❌ Failed to create provider: {e}")


async def demonstrate_auto_provider():
    """Demonstrate automatic provider creation."""
    print("\n🎯 Auto Provider Creation:")
    print("=" * 50)
    
    try:
        provider = create_auto_provider()
        print("✅ Auto provider created successfully!")
        
        # Test the provider
        is_available = await provider.is_available()
        if is_available:
            info = provider.get_model_info()
            print(f"   🏷️ Provider: {info['provider']}")
            print(f"   📊 Model: {info['model']}")
            print(f"   📐 Dimension: {info.get('dimension', 'Unknown')}")
            
            # Test embedding
            embedding = await provider.embed_text("This is a test sentence.")
            print(f"   🧪 Embedding dimension: {len(embedding)}")
            print(f"   🔢 First 5 values: {embedding[:5]}")
        else:
            print("   ❌ Auto provider not available")
            
        # Cleanup
        if hasattr(provider, 'close'):
            await provider.close()
            
    except Exception as e:
        print(f"❌ Auto provider creation failed: {e}")


async def demonstrate_default_models():
    """Demonstrate getting default models for providers."""
    print("\n📋 Default Models:")
    print("=" * 30)
    
    providers = ['openai', 'huggingface', 'cohere', 'ollama']
    
    for provider in providers:
        default = get_default_model(provider)
        print(f"{provider.upper():12}: {default}")


async def main():
    """Run all demonstrations."""
    print("🚀 AgenticFlow Embedding Factory Example")
    print("=" * 60)
    
    try:
        await demonstrate_provider_listing()
        await demonstrate_default_models()
        await demonstrate_auto_selection()
        await demonstrate_factory_creation()
        await demonstrate_auto_provider()
        
        print("\n" + "=" * 60)
        print("✅ All factory demonstrations completed!")
        
    except KeyboardInterrupt:
        print("\n❌ Example interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())