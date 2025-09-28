"""Test runner for AgenticFlow."""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_pytest(test_file: str, verbose: bool = True) -> bool:
    """Run pytest on a specific test file."""
    cmd = ["python", "-m", "pytest", test_file]
    if verbose:
        cmd.append("-v")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_basic_tests() -> bool:
    """Run basic tests without external dependencies."""
    print("🧪 Running basic tests...")
    
    try:
        # Test imports
        from agenticflow import Flow, Agent, Team
        from agenticflow.agents import FilesystemAgent, PythonAgent, ExcelAgent, DataAgent, SSISAnalysisAgent
        from agenticflow.tools import create_file, search_web
        from agenticflow.observability import EventLogger, ConsoleSubscriber
        print("✅ All imports successful")
        
        # Test basic creation
        flow = Flow("test_flow")
        agent = Agent("test_agent", tools=[create_file])
        team = Team("test_team")
        print("✅ Core classes creation successful")
        
        # Test specialized agents
        fs_agent = FilesystemAgent("fs_agent")
        py_agent = PythonAgent("py_agent")
        excel_agent = ExcelAgent("excel_agent")
        data_agent = DataAgent("data_agent")
        ssis_agent = SSISAnalysisAgent("ssis_agent")
        print("✅ Specialized agents creation successful")
        
        # Test observability
        flow.enable_observability(console_output=False)
        assert flow._observability_enabled == True
        print("✅ Observability enable successful")
        
        # Test tools
        from agenticflow.tools import (
            parse_dtsx_file, extract_data_flows, extract_connections,
            extract_tasks, extract_variables, create_package_summary,
            search_package_content
        )
        print("✅ SSIS tools import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

async def run_integration_tests() -> bool:
    """Run integration tests with real API calls."""
    print("🔗 Running integration tests...")
    
    try:
        from agenticflow import Flow, Agent
        from agenticflow.tools import create_file
        
        # Test basic flow execution
        flow = Flow("integration_test")
        flow.enable_observability(console_output=False, file_logging=False)
        
        agent = Agent("test_agent", tools=[create_file], description="Test agent")
        flow.add_agent(agent)
        
        # Run a simple workflow
        result = await flow.run("Create a test file with content 'Hello World'")
        
        assert "messages" in result
        assert len(result["messages"]) > 0
        print("✅ Flow execution successful")
        
        # Test observability
        events = flow._event_logger.get_events()
        assert len(events) > 0
        print("✅ Observability events captured")
        
        # Test metrics
        metrics = flow.get_metrics()
        assert "total_events" in metrics
        print("✅ Metrics collection successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False

def run_lint_checks() -> bool:
    """Run linting checks."""
    print("🔍 Running lint checks...")
    
    try:
        # Check for basic syntax errors
        result = subprocess.run([
            "python", "-m", "py_compile", 
            "agenticflow/core/flow.py",
            "agenticflow/observability/events.py",
            "agenticflow/observability/event_bus.py",
            "agenticflow/observability/subscribers.py",
            "agenticflow/observability/logger.py"
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Syntax errors found: {result.stderr}")
            return False
        
        print("✅ No syntax errors found")
        return True
        
    except Exception as e:
        print(f"❌ Lint checks failed: {e}")
        return False

def main():
    """Main test runner."""
    print("🚀 AgenticFlow Test Suite")
    print("=" * 50)
    
    # Set up environment
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-key")
    os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "test-key")
    
    all_passed = True
    
    # Run basic tests
    if not run_basic_tests():
        all_passed = False
    
    print()
    
    # Run lint checks
    if not run_lint_checks():
        all_passed = False
    
    print()
    
    # Run integration tests
    if not asyncio.run(run_integration_tests()):
        all_passed = False
    
    print()
    
    # Run pytest tests if available
    try:
        print("🧪 Running pytest tests...")
        if run_pytest("tests/test_observability.py", verbose=False):
            print("✅ Observability tests passed")
        else:
            print("❌ Observability tests failed")
            all_passed = False
        
        if run_pytest("tests/test_api_comprehensive.py", verbose=False):
            print("✅ API comprehensive tests passed")
        else:
            print("❌ API comprehensive tests failed")
            all_passed = False
            
    except Exception as e:
        print(f"⚠️ Pytest tests skipped: {e}")
    
    print()
    print("=" * 50)
    
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
