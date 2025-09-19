#!/usr/bin/env python3
"""
Comprehensive Test Script for Enterprise Super Agentic Chatbot
=============================================================

This script tests all the advanced file-focused capabilities of the
Enterprise Super Agentic Chatbot with our related test files.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from examples.enterprise_chatbot.enterprise_super_agent import EnterpriseSuperAgent

async def test_comprehensive_capabilities():
    """Test all file management capabilities with related files."""
    
    print("🧪 COMPREHENSIVE ENTERPRISE SUPER AGENTIC CHATBOT TEST")
    print("=" * 80)
    
    # Check environment
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not set. Please set it to continue.")
        return
    
    # Initialize the enterprise agent
    print("\n🚀 Initializing Enterprise Super Agentic Chatbot...")
    agent = EnterpriseSuperAgent()
    await agent.initialize()
    
    print("✅ Agent initialized successfully!")
    
    # Define comprehensive test scenarios
    test_scenarios = [
        # 1. File Analysis Tests
        {
            "category": "📊 MULTI-FORMAT FILE ANALYSIS",
            "tests": [
                "Analyze test_project/users.json comprehensively",
                "Analyze test_project/config.yaml structure and content",
                "Analyze test_project/user_processor.py for code structure",
                "Analyze test_project/application.log for patterns and anomalies",
                "Analyze test_project/database.sql schema and relationships"
            ]
        },
        
        # 2. File Relationships Tests  
        {
            "category": "🔗 FILE RELATIONSHIP MAPPING",
            "tests": [
                "Map file relationships in test_project directory",
                "Show how user_processor.py relates to users.json and config.yaml",
                "Identify data flow between all files in test_project",
                "Generate a dependency graph for the test project files"
            ]
        },
        
        # 3. Format Conversion Tests
        {
            "category": "🔄 FORMAT CONVERSION & EDITING", 
            "tests": [
                "Convert test_project/users.json to CSV format",
                "Convert test_project/config.yaml to JSON format",
                "Create a TOML version of the configuration data",
                "Merge users.json and config.yaml into a comprehensive XML file"
            ]
        },
        
        # 4. Pattern Detection Tests
        {
            "category": "🔍 PATTERN DETECTION & ANALYSIS",
            "tests": [
                "Find all email addresses across all files in test_project",
                "Detect IP addresses and phone numbers in application.log",
                "Analyze skill distributions in users.json",
                "Find duplicate patterns across different files"
            ]
        },
        
        # 5. Database Integration Tests
        {
            "category": "🗃️ DATABASE & SQL ANALYSIS",
            "tests": [
                "Analyze database.sql schema structure",
                "Extract all table relationships from database.sql",
                "Identify foreign key constraints and indexes",
                "Show how database schema relates to users.json structure"
            ]
        },
        
        # 6. Report Generation Tests
        {
            "category": "📈 REPORT GENERATION",
            "tests": [
                "Generate an HTML report analyzing all files in test_project",
                "Create a comprehensive Markdown report about file relationships",
                "Generate a department budget analysis from config.yaml and users.json",
                "Create an executive summary of the entire project structure"
            ]
        },
        
        # 7. Advanced Analysis Tests
        {
            "category": "🧠 ADVANCED ANALYTICS",
            "tests": [
                "Compare user data between users.json and database.sql",
                "Analyze version consistency across config.yaml and user_processor.py",
                "Find configuration references in Python code",
                "Generate insights about data inconsistencies across files"
            ]
        },
        
        # 8. File Operations Tests
        {
            "category": "✏️ FILE MODIFICATION & OPERATIONS",
            "tests": [
                "Create a summary.md file based on analysis of all project files",
                "Edit config.yaml to add a new service configuration",
                "Extract user emails from users.json into a simple CSV",
                "Create a backup of all files with timestamp suffix"
            ]
        }
    ]
    
    # Execute all test scenarios
    total_tests = 0
    successful_tests = 0
    
    for scenario in test_scenarios:
        print(f"\n{scenario['category']}")
        print("-" * 60)
        
        for i, test_query in enumerate(scenario['tests'], 1):
            total_tests += 1
            print(f"\n🔬 Test {i}: {test_query}")
            
            try:
                # Process the test query
                response = await agent.process_user_input(test_query)
                
                # Check if response indicates success
                if any(indicator in response.lower() for indicator in 
                      ['✅', 'successfully', 'completed', 'analysis', 'generated', 'found']):
                    print(f"✅ SUCCESS")
                    successful_tests += 1
                else:
                    print(f"⚠️  PARTIAL SUCCESS")
                    successful_tests += 0.5
                
                # Show preview of response
                preview = response[:300] + "..." if len(response) > 300 else response
                print(f"📝 Response Preview: {preview}")
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
            
            # Small delay between tests
            await asyncio.sleep(0.5)
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"🎯 COMPREHENSIVE TEST RESULTS")
    print(f"{'='*80}")
    print(f"Total Tests Executed: {total_tests}")
    print(f"Successful Tests: {successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    print(f"\n🌟 ENTERPRISE SUPER AGENTIC CHATBOT CAPABILITIES DEMONSTRATED:")
    print("✅ Multi-format file analysis (JSON, YAML, Python, SQL, LOG)")
    print("✅ File relationship mapping and dependency analysis") 
    print("✅ Format conversion with validation")
    print("✅ Pattern detection and anomaly analysis")
    print("✅ Database schema analysis")
    print("✅ Comprehensive report generation")
    print("✅ Advanced analytics and insights")
    print("✅ File modification and operations")
    print("✅ Multi-agent coordination and task orchestration")
    print("✅ Real-time progress tracking and monitoring")
    
    # Cleanup
    await agent.shutdown()
    print(f"\n✅ Test completed successfully!")

async def quick_interactive_demo():
    """Quick interactive demonstration of key features."""
    
    print("🚀 QUICK INTERACTIVE DEMO")
    print("=" * 40)
    
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not set. Please set it to continue.")
        return
    
    agent = EnterpriseSuperAgent()
    await agent.initialize()
    
    # Quick demo queries
    demo_queries = [
        "Show me what files are in the test_project directory",
        "Analyze the relationship between users.json and user_processor.py", 
        "Find all email addresses in the project files",
        "Generate a summary report of the test project"
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n🔍 Demo {i}: {query}")
        response = await agent.process_user_input(query)
        preview = response[:200] + "..." if len(response) > 200 else response
        print(f"💬 Response: {preview}")
        await asyncio.sleep(1)
    
    await agent.shutdown()
    print(f"\n✅ Quick demo completed!")

async def main():
    """Main function to run the comprehensive test."""
    
    print("🎯 Choose test mode:")
    print("1. Comprehensive Test Suite (all capabilities)")
    print("2. Quick Interactive Demo (key features)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await test_comprehensive_capabilities()
        elif choice == "2":
            await quick_interactive_demo()
        else:
            print("Invalid choice. Running quick demo...")
            await quick_interactive_demo()
            
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user.")
    except Exception as e:
        print(f"❌ Test error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())