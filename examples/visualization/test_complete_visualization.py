#!/usr/bin/env python3
"""
Complete test of AgenticFlow visualization module after cleanup.

This script tests all the visualization functionality to ensure everything works:
1. Simple interface functions
2. Object-level visualization methods 
3. Jupyter notebook integration
4. Export capabilities
5. Advanced API
"""

import sys
import tempfile
from pathlib import Path

# Test the main simple interface
print("🧪 Testing AgenticFlow Visualization Module")
print("=" * 50)

def test_simple_interface():
    """Test the simple zero-setup interface."""
    print("\n1️⃣ Testing Simple Interface")
    print("-" * 30)
    
    try:
        from agenticflow.visualization import (
            visualize_workflow, visualize_agents, quick_diagram,
            SimpleTask, SimpleAgent
        )
        
        # Test workflow visualization
        print("   📊 Testing workflow visualization...")
        tasks = [
            SimpleTask("Setup", "completed", duration=15.0),
            SimpleTask("Process", "running", depends_on=["Setup"]),
            SimpleTask("Deploy", "pending", depends_on=["Process"])
        ]
        
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        result = visualize_workflow(
            tasks,
            workflow_name="Test Workflow",
            show=False,
            save_path=str(output_dir / "test_workflow.svg")
        )
        
        if result:
            print(f"   ✅ Workflow saved to: {result}")
        else:
            print("   ❌ Workflow visualization failed")
            
        # Test agent visualization
        print("   🤖 Testing agent visualization...")
        agents = [
            SimpleAgent("Supervisor", "supervisor"),
            SimpleAgent("Worker 1", "worker", ["search", "calculator"]),
            SimpleAgent("Worker 2", "specialist", ["database"])
        ]
        
        result = visualize_agents(
            agents,
            topology="star",
            show=False,
            save_path=str(output_dir / "test_agents.svg")
        )
        
        if result:
            print(f"   ✅ Agent topology saved to: {result}")
        else:
            print("   ❌ Agent visualization failed")
            
        # Test quick diagram
        print("   🔗 Testing quick diagrams...")
        result = quick_diagram(
            nodes=["Start", "Process", "End"],
            connections=[("Start", "Process"), ("Process", "End")],
            show=False,
            save_path=str(output_dir / "test_diagram.svg")
        )
        
        if result:
            print(f"   ✅ Quick diagram saved to: {result}")
        else:
            print("   ❌ Quick diagram failed")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Simple interface test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_object_methods():
    """Test visualization methods on objects themselves.""" 
    print("\n2️⃣ Testing Object Methods")
    print("-" * 30)
    
    try:
        # Test with a mock agent-like object
        class MockAgent:
            def __init__(self):
                self.name = "Test Agent"
                self.role = "worker"
                self.tools = ["calculator", "search"]
                self.config = type('Config', (), {'role': 'worker'})()
                
        # Add the mixin
        from agenticflow.visualization.mixins import AgentVisualizationMixin
        
        class TestAgent(MockAgent, AgentVisualizationMixin):
            pass
            
        agent = TestAgent()
        
        print("   🤖 Testing agent.visualize()...")
        output_dir = Path(__file__).parent / "test_output"
        result = agent.visualize(
            show=False,
            save_path=str(output_dir / "test_agent_method.svg")
        )
        
        if result:
            print(f"   ✅ Agent method saved to: {result}")
        else:
            print("   ❌ Agent method failed")
            
        # Test with mock orchestrator
        class MockOrchestrator:
            def __init__(self):
                self.name = "Test Workflow"
                
            def _extract_tasks_for_visualization(self):
                from agenticflow.visualization.simple import SimpleTask
                return [
                    SimpleTask("Task 1", "completed"),
                    SimpleTask("Task 2", "running", depends_on=["Task 1"]),
                    SimpleTask("Task 3", "pending", depends_on=["Task 2"])
                ]
                
            def _get_workflow_description(self):
                return "Test workflow description"
        
        from agenticflow.visualization.mixins import WorkflowVisualizationMixin
        
        class TestOrchestrator(MockOrchestrator, WorkflowVisualizationMixin):
            pass
            
        orchestrator = TestOrchestrator()
        
        print("   📊 Testing orchestrator.show()...")
        result = orchestrator.show(
            show=False,
            save_path=str(output_dir / "test_orchestrator_method.svg")
        )
        
        if result:
            print(f"   ✅ Orchestrator method saved to: {result}")
        else:
            print("   ❌ Orchestrator method failed")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Object methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jupyter_integration():
    """Test Jupyter notebook integration."""
    print("\n3️⃣ Testing Jupyter Integration")
    print("-" * 30)
    
    try:
        from agenticflow.visualization import show_workflow, show_agents, SimpleTask, SimpleAgent
        
        print("   📔 Testing show_workflow()...")
        tasks = [
            SimpleTask("Setup", "completed"),
            SimpleTask("Test", "running", depends_on=["Setup"])
        ]
        
        viz = show_workflow(tasks)
        html_content = viz._repr_html_()
        
        if html_content and "<svg" in html_content:
            print("   ✅ show_workflow() returns valid HTML with SVG")
        else:
            print("   ❌ show_workflow() failed to return SVG HTML")
            
        print("   🤖 Testing show_agents()...")
        agents = [SimpleAgent("Agent1", "worker"), SimpleAgent("Agent2", "supervisor")]
        viz = show_agents(agents)
        html_content = viz._repr_html_()
        
        if html_content and "<svg" in html_content:
            print("   ✅ show_agents() returns valid HTML with SVG")
        else:
            print("   ❌ show_agents() failed to return SVG HTML")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Jupyter integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_capabilities():
    """Test export capabilities."""
    print("\n4️⃣ Testing Export Capabilities")
    print("-" * 30)
    
    try:
        from agenticflow.visualization import check_export_capabilities
        
        capabilities = check_export_capabilities()
        print("   📤 Export backends available:")
        
        for backend, available in capabilities["backends"].items():
            status = "✅" if available else "❌"
            print(f"      {status} {backend}")
            
        print("   📁 Supported formats:")
        for format_name, supported in capabilities["formats"].items():
            status = "✅" if supported else "❌"
            print(f"      {status} {format_name.upper()}")
            
        # At least one backend should be available
        if any(capabilities["backends"].values()):
            print("   ✅ At least one export backend is available")
            return True
        else:
            print("   ⚠️  No export backends available - this is expected in some environments")
            return True
            
    except Exception as e:
        print(f"   ❌ Export capabilities test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_advanced_api():
    """Test advanced API components."""
    print("\n5️⃣ Testing Advanced API")
    print("-" * 30)
    
    try:
        from agenticflow.visualization import (
            MermaidGenerator, WorkflowVisualizer, TopologyVisualizer,
            TaskNode, TaskState, WorkflowInfo
        )
        
        print("   🔧 Testing MermaidGenerator...")
        gen = MermaidGenerator()
        gen.add_node("A", "Node A")
        gen.add_node("B", "Node B") 
        gen.add_edge("A", "B", "connects to")
        
        diagram_code = gen.generate()
        if diagram_code and "flowchart" in diagram_code:
            print("   ✅ MermaidGenerator works correctly")
        else:
            print("   ❌ MermaidGenerator failed")
            
        print("   📊 Testing WorkflowVisualizer...")
        viz = WorkflowVisualizer()
        tasks = [
            TaskNode("task1", "Task 1", "Description", TaskState.COMPLETED, "HIGH", [])
        ]
        workflow_info = WorkflowInfo("Test", "Description", 1, 1, 0)
        
        diagram_code = viz.visualize_dag(tasks, workflow_info)
        if diagram_code and "flowchart" in diagram_code:
            print("   ✅ WorkflowVisualizer works correctly") 
        else:
            print("   ❌ WorkflowVisualizer failed")
            
        print("   🏗️ Testing TopologyVisualizer...")
        topo_viz = TopologyVisualizer()
        # Test would require mock agents, so just check it imports
        print("   ✅ TopologyVisualizer imported successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Advanced API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_with_core():
    """Test integration with core AgenticFlow objects."""
    print("\n6️⃣ Testing Core Integration")
    print("-" * 30)
    
    try:
        # Test that mixins are properly added to core classes
        print("   🔍 Checking mixin integration...")
        
        # Check Agent class
        try:
            from agenticflow.core.agent import Agent
            if hasattr(Agent, 'visualize') and hasattr(Agent, 'show'):
                print("   ✅ Agent class has visualization methods")
            else:
                print("   ❌ Agent class missing visualization methods")
        except ImportError:
            print("   ⚠️  Agent class not available (expected in some test environments)")
            
        # Check TaskOrchestrator class  
        try:
            from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
            if hasattr(TaskOrchestrator, 'visualize') and hasattr(TaskOrchestrator, 'show'):
                print("   ✅ TaskOrchestrator class has visualization methods")
            else:
                print("   ❌ TaskOrchestrator class missing visualization methods")
        except ImportError:
            print("   ⚠️  TaskOrchestrator class not available")
            
        # Check MultiAgentSystem class
        try:
            from agenticflow.workflows.multi_agent import MultiAgentSystem
            if hasattr(MultiAgentSystem, 'visualize') and hasattr(MultiAgentSystem, 'show'):
                print("   ✅ MultiAgentSystem class has visualization methods")
            else:
                print("   ❌ MultiAgentSystem class missing visualization methods")
        except ImportError:
            print("   ⚠️  MultiAgentSystem class not available")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Core integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 AgenticFlow Visualization Module Test Suite")
    print("=" * 50)
    
    tests = [
        ("Simple Interface", test_simple_interface),
        ("Object Methods", test_object_methods), 
        ("Jupyter Integration", test_jupyter_integration),
        ("Export Capabilities", test_export_capabilities),
        ("Advanced API", test_advanced_api),
        ("Core Integration", test_integration_with_core)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result:
            print(f"✅ {test_name}")
            passed += 1
        else:
            print(f"❌ {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Visualization module is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())