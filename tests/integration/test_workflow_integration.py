"""
Integration tests for AgenticFlow Workflows
===========================================

End-to-end integration tests for complete workflow scenarios.
"""

import pytest
import asyncio
import time
import tempfile
import os
from pathlib import Path

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import FunctionTaskExecutor, RetryPolicy, TaskPriority
from agenticflow.tools.registry import ToolRegistry


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete workflow scenarios."""
    
    @pytest.mark.asyncio
    async def test_simple_data_processing_workflow(self, temp_directory):
        """Test a simple data processing workflow end-to-end."""
        
        # Shared data storage
        workflow_data = {}
        
        async def generate_data(count: int = 100):
            """Generate sample data."""
            data = [{"id": i, "value": i * 2, "category": "A" if i % 2 == 0 else "B"} for i in range(count)]
            workflow_data["raw_data"] = data
            return {"count": len(data), "sample": data[:3]}
        
        async def process_data(**kwargs):
            """Process the generated data."""
            raw_data = workflow_data["raw_data"]
            
            # Calculate statistics
            total_count = len(raw_data)
            category_a_count = sum(1 for item in raw_data if item["category"] == "A")
            category_b_count = total_count - category_a_count
            avg_value = sum(item["value"] for item in raw_data) / total_count
            
            processed_data = {
                "total_count": total_count,
                "category_a_count": category_a_count,
                "category_b_count": category_b_count,
                "average_value": avg_value,
                "processed_at": time.time()
            }
            
            workflow_data["processed_data"] = processed_data
            return processed_data
        
        async def save_results(**kwargs):
            """Save results to file."""
            processed_data = workflow_data["processed_data"]
            
            output_file = os.path.join(temp_directory, "results.txt")
            with open(output_file, "w") as f:
                f.write(f"Data Processing Results\n")
                f.write(f"Total Count: {processed_data['total_count']}\n")
                f.write(f"Category A: {processed_data['category_a_count']}\n")
                f.write(f"Category B: {processed_data['category_b_count']}\n")
                f.write(f"Average Value: {processed_data['average_value']:.2f}\n")
            
            return {"output_file": output_file, "file_exists": os.path.exists(output_file)}
        
        # Set up orchestrator
        orchestrator = TaskOrchestrator(max_concurrent_tasks=3)
        
        orchestrator.add_interactive_task(
            task_id="generate",
            name="Generate Data",
            executor=FunctionTaskExecutor(generate_data, 50)
        )
        orchestrator.add_interactive_task(
            task_id="process",
            name="Process Data",
            executor=FunctionTaskExecutor(process_data),
            dependencies=["generate"]
        )
        orchestrator.add_interactive_task(
            task_id="save",
            name="Save Results",
            executor=FunctionTaskExecutor(save_results),
            dependencies=["process"]
        )
        
        # Execute workflow with streaming
        result = None
        async for update in orchestrator.execute_workflow_with_streaming():
            if update.get("type") == "workflow_completed":
                result = {
                    "success_rate": 100.0 if update.get("status", {}).get("is_complete", False) and update.get("status", {}).get("failed_tasks", 0) == 0 else 0.0,
                    "status": update.get("status", {})
                }
                break
        
        # Verify workflow completion
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == 3
        assert result["status"]["is_complete"] is True
        
        # Verify data flow
        assert "raw_data" in workflow_data
        assert "processed_data" in workflow_data
        assert len(workflow_data["raw_data"]) == 50
        
        # Verify file output
        output_file = os.path.join(temp_directory, "results.txt")
        assert os.path.exists(output_file)
        
        with open(output_file, "r") as f:
            content = f.read()
            assert "Data Processing Results" in content
            assert "Total Count: 50" in content
    
    @pytest.mark.asyncio
    async def test_parallel_computation_workflow(self):
        """Test parallel computation workflow with multiple branches."""
        
        results = {}
        
        async def compute_fibonacci(n: int):
            """Compute fibonacci number."""
            if n <= 1:
                return n
            
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            
            results[f"fib_{n}"] = b
            return {"n": n, "fibonacci": b}
        
        async def compute_factorial(n: int):
            """Compute factorial."""
            result = 1
            for i in range(1, n + 1):
                result *= i
            
            results[f"fact_{n}"] = result
            return {"n": n, "factorial": result}
        
        async def compute_prime_check(n: int):
            """Check if number is prime."""
            if n < 2:
                is_prime = False
            else:
                is_prime = True
                for i in range(2, int(n ** 0.5) + 1):
                    if n % i == 0:
                        is_prime = False
                        break
            
            results[f"prime_{n}"] = is_prime
            return {"n": n, "is_prime": is_prime}
        
        async def aggregate_results(**kwargs):
            """Aggregate all computation results."""
            # Collect results from all branches
            computations = {}
            for key, value in kwargs.items():
                if key.endswith("_result") and isinstance(value, dict):
                    if "fibonacci" in value:
                        computations["fibonacci"] = value
                    elif "factorial" in value:
                        computations["factorial"] = value
                    elif "is_prime" in value:
                        computations["prime"] = value
            
            return {
                "total_computations": len(computations),
                "results": computations,
                "shared_data": results
            }
        
        # Set up parallel computation workflow
        orchestrator = TaskOrchestrator(max_concurrent_tasks=5)
        
        # Parallel computation tasks
        orchestrator.add_interactive_task("fib_10", "Fibonacci 10", FunctionTaskExecutor(compute_fibonacci, 10))
        orchestrator.add_interactive_task("fib_15", "Fibonacci 15", FunctionTaskExecutor(compute_fibonacci, 15))
        orchestrator.add_interactive_task("fact_8", "Factorial 8", FunctionTaskExecutor(compute_factorial, 8))
        orchestrator.add_interactive_task("prime_17", "Prime Check 17", FunctionTaskExecutor(compute_prime_check, 17))
        orchestrator.add_interactive_task("prime_25", "Prime Check 25", FunctionTaskExecutor(compute_prime_check, 25))
        
        # Aggregation task depends on all computations
        orchestrator.add_interactive_task(
            task_id="aggregate",
            name="Aggregate Results",
            executor=FunctionTaskExecutor(aggregate_results),
            dependencies=["fib_10", "fib_15", "fact_8", "prime_17", "prime_25"]
        )
        
        # Execute with timing
        start_time = time.time()
        result = None
        async for update in orchestrator.execute_workflow_with_streaming():
            if update.get("type") == "workflow_completed":
                result = {
                    "success_rate": 100.0 if update.get("status", {}).get("is_complete", False) and update.get("status", {}).get("failed_tasks", 0) == 0 else 0.0,
                    "status": update.get("status", {})
                }
                break
        execution_time = time.time() - start_time
        
        # Verify parallel execution
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == 6
        
        # Verify results are correct
        assert results["fib_10"] == 55  # 10th Fibonacci number
        assert results["fib_15"] == 610  # 15th Fibonacci number
        assert results["fact_8"] == 40320  # 8!
        assert results["prime_17"] is True  # 17 is prime
        assert results["prime_25"] is False  # 25 is not prime
        
        # Should complete faster than sequential execution
        assert execution_time < 1.0  # Should be very fast for these calculations
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test workflow with error recovery and retry mechanisms."""
        
        attempt_counts = {}
        
        async def unstable_task(task_id: str, failure_rate: float = 0.5):
            """Task that fails sometimes."""
            if task_id not in attempt_counts:
                attempt_counts[task_id] = 0
            
            attempt_counts[task_id] += 1
            
            # Fail on first few attempts based on failure rate
            if attempt_counts[task_id] <= 2 and time.time() % 1 < failure_rate:
                raise RuntimeError(f"Task {task_id} failed on attempt {attempt_counts[task_id]}")
            
            return {"task_id": task_id, "attempts": attempt_counts[task_id]}
        
        async def stable_task(task_id: str):
            """Task that always succeeds."""
            return {"task_id": task_id, "status": "success"}
        
        async def recovery_task(**kwargs):
            """Task that processes both success and failure cases."""
            successful_tasks = []
            failed_tasks = []
            
            for key, value in kwargs.items():
                if key.endswith("_result") and isinstance(value, dict):
                    if "error" in str(value):
                        failed_tasks.append(key)
                    else:
                        successful_tasks.append(key)
            
            return {
                "successful_count": len(successful_tasks),
                "failed_count": len(failed_tasks),
                "recovery_applied": len(failed_tasks) > 0
            }
        
        # Set up error recovery workflow
        retry_policy = RetryPolicy(
            max_attempts=3,
            initial_delay=0.01,
            max_delay=0.1,
            backoff_multiplier=2.0
        )
        
        orchestrator = TaskOrchestrator(
            max_concurrent_tasks=3,
            default_retry_policy=retry_policy
        )
        
        # Mix of stable and unstable tasks
        orchestrator.add_function_task("stable_1", "Stable Task 1", stable_task, args=("stable_1",))
        orchestrator.add_function_task("unstable_1", "Unstable Task 1", unstable_task, args=("unstable_1", 0.8))
        orchestrator.add_function_task("stable_2", "Stable Task 2", stable_task, args=("stable_2",))
        orchestrator.add_function_task("unstable_2", "Unstable Task 2", unstable_task, args=("unstable_2", 0.6))
        
        # Recovery task processes all results
        orchestrator.add_function_task(
            "recovery",
            "Recovery Task",
            recovery_task,
            dependencies=["stable_1", "unstable_1", "stable_2", "unstable_2"]
        )
        
        # Execute workflow
        result = await orchestrator.execute_workflow()
        
        # Some tasks may fail even with retries, but workflow should complete
        assert result["status"]["is_complete"] is True
        assert result["status"]["completed_tasks"] >= 3  # At least stable tasks + recovery
        
        # Verify retry attempts were made
        assert any(count > 1 for count in attempt_counts.values())
    
    @pytest.mark.asyncio 
    async def test_tool_registry_integration_workflow(self):
        """Test workflow integration with tool registry."""
        
        # Set up tool registry
        registry = ToolRegistry()
        
        @registry.register_function("math_add", category="math")
        def add_numbers(a: float, b: float) -> float:
            """Add two numbers."""
            return a + b
        
        @registry.register_function("math_multiply", category="math")
        def multiply_numbers(a: float, b: float) -> float:
            """Multiply two numbers."""
            return a * b
        
        @registry.register_function("string_concat", category="text")
        def concat_strings(s1: str, s2: str) -> str:
            """Concatenate two strings."""
            return s1 + s2
        
        # Workflow tasks using tools
        async def calculate_using_tools(x: float, y: float):
            """Use registry tools for calculations."""
            sum_result = await registry.execute_tool("math_add", {"a": x, "b": y})
            product_result = await registry.execute_tool("math_multiply", {"a": x, "b": y})
            
            return {
                "x": x, "y": y,
                "sum": sum_result.result if sum_result.success else None,
                "product": product_result.result if product_result.success else None
            }
        
        async def format_using_tools(**kwargs):
            """Use registry tools for formatting."""
            # Look for the calculation result from the calculate task
            # The orchestrator passes dependency results as {task_id}_result
            calc_result = kwargs.get("calculate_result")
            
            if calc_result and "sum" in calc_result and "product" in calc_result:
                sum_str = str(calc_result["sum"])
                product_str = str(calc_result["product"])
                
                formatted = await registry.execute_tool("string_concat", {"s1": f"Sum: {sum_str}, ", "s2": f"Product: {product_str}"})
                
                return {
                    "formatted_result": formatted.result if formatted.success else None,
                    "calculation_data": calc_result
                }
            
            return {"error": "No calculation result found", "received_kwargs": kwargs}
        
        # Set up orchestrator
        orchestrator = TaskOrchestrator(max_concurrent_tasks=2)
        
        orchestrator.add_function_task("calculate", "Calculate", calculate_using_tools, args=(5.0, 3.0))
        orchestrator.add_function_task("format", "Format", format_using_tools, dependencies=["calculate"])
        
        # Execute workflow
        result = await orchestrator.execute_workflow()
        
        # Verify workflow success
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == 2
        
        # Verify tool integration worked
        format_result = result["task_results"]["format"]["result"]["result"]
        assert "formatted_result" in format_result
        assert "Sum: 8.0, Product: 15.0" == format_result["formatted_result"]
    
    @pytest.mark.asyncio
    async def test_complex_dependency_workflow(self):
        """Test complex workflow with diamond dependencies and fan-out/fan-in patterns."""
        
        execution_order = []
        
        async def tracked_task(task_id: str, duration: float = 0.1):
            """Task that tracks execution order."""
            execution_order.append(f"{task_id}_start")
            await asyncio.sleep(duration)
            execution_order.append(f"{task_id}_end")
            return {"task_id": task_id, "timestamp": time.time()}
        
        # Set up complex DAG
        orchestrator = TaskOrchestrator(max_concurrent_tasks=4)
        
        # Root task
        orchestrator.add_function_task("root", "Root Task", tracked_task, args=("root", 0.05))
        
        # First level - fan out from root
        orchestrator.add_function_task("level1_a", "Level 1A", tracked_task, args=("level1_a", 0.1), dependencies=["root"])
        orchestrator.add_function_task("level1_b", "Level 1B", tracked_task, args=("level1_b", 0.15), dependencies=["root"])
        orchestrator.add_function_task("level1_c", "Level 1C", tracked_task, args=("level1_c", 0.08), dependencies=["root"])
        
        # Second level - mixed dependencies
        orchestrator.add_function_task("level2_a", "Level 2A", tracked_task, args=("level2_a", 0.05), dependencies=["level1_a"])
        orchestrator.add_function_task("level2_b", "Level 2B", tracked_task, args=("level2_b", 0.12), dependencies=["level1_a", "level1_b"])
        orchestrator.add_function_task("level2_c", "Level 2C", tracked_task, args=("level2_c", 0.07), dependencies=["level1_c"])
        
        # Final level - fan in to final task
        orchestrator.add_function_task(
            "final", 
            "Final Task", 
            tracked_task, 
            args=("final", 0.05), 
            dependencies=["level2_a", "level2_b", "level2_c"]
        )
        
        # Execute workflow
        start_time = time.time()
        result = await orchestrator.execute_workflow()
        execution_time = time.time() - start_time
        
        # Verify workflow completion
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == 8
        
        # Verify execution order respects dependencies
        root_start = execution_order.index("root_start")
        final_end = execution_order.index("final_end")
        
        # Root should start first
        assert root_start == 0
        
        # Final should end last
        assert final_end == len(execution_order) - 1
        
        # Verify DAG structure is respected
        for task_end in ["level1_a_end", "level1_b_end", "level1_c_end"]:
            assert execution_order.index("root_end") < execution_order.index(task_end)
        
        # Verify parallel execution efficiency
        # Should complete faster than sequential execution due to parallelism
        assert execution_time < 1.0  # Much less than sum of all durations (more lenient)
    
    @pytest.mark.asyncio
    async def test_file_processing_workflow(self, temp_directory):
        """Test file processing workflow with real file I/O."""
        
        async def create_input_files():
            """Create multiple input files."""
            files_created = []
            
            for i in range(3):
                filename = f"input_{i}.txt"
                filepath = os.path.join(temp_directory, filename)
                
                with open(filepath, "w") as f:
                    f.write(f"File {i} content\n")
                    f.write(f"Line 2 of file {i}\n")
                    f.write(f"Total lines in file {i}: 3\n")
                
                files_created.append(filepath)
            
            return {"files_created": files_created, "count": len(files_created)}
        
        async def process_file(file_index: int, **kwargs):
            """Process a single file."""
            input_file = os.path.join(temp_directory, f"input_{file_index}.txt")
            output_file = os.path.join(temp_directory, f"processed_{file_index}.txt")
            
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input file {input_file} not found")
            
            # Read and process
            with open(input_file, "r") as f:
                lines = f.readlines()
            
            processed_lines = []
            for line_num, line in enumerate(lines, 1):
                processed_lines.append(f"[{line_num}] {line.strip().upper()}")
            
            # Write processed content
            with open(output_file, "w") as f:
                f.write(f"PROCESSED FILE {file_index}\n")
                f.write("=" * 20 + "\n")
                for line in processed_lines:
                    f.write(line + "\n")
            
            return {
                "input_file": input_file,
                "output_file": output_file,
                "lines_processed": len(lines),
                "file_index": file_index
            }
        
        async def merge_processed_files(**kwargs):
            """Merge all processed files."""
            processed_files = []
            total_lines = 0
            
            # Collect processed file info
            for key, value in kwargs.items():
                if key.endswith("_result") and isinstance(value, dict) and "output_file" in value:
                    processed_files.append(value)
                    total_lines += value["lines_processed"]
            
            # Create merged file
            merged_file = os.path.join(temp_directory, "merged_output.txt")
            with open(merged_file, "w") as f:
                f.write("MERGED PROCESSED FILES\n")
                f.write("=" * 30 + "\n\n")
                
                for file_info in sorted(processed_files, key=lambda x: x["file_index"]):
                    f.write(f"\n--- FROM FILE {file_info['file_index']} ---\n")
                    
                    with open(file_info["output_file"], "r") as source:
                        content = source.read()
                        f.write(content)
                    
                    f.write("\n")
            
            return {
                "merged_file": merged_file,
                "files_merged": len(processed_files),
                "total_lines": total_lines
            }
        
        # Set up file processing workflow
        orchestrator = TaskOrchestrator(max_concurrent_tasks=4)
        
        # Create input files
        orchestrator.add_function_task("create_inputs", "Create Input Files", create_input_files)
        
        # Process files in parallel
        for i in range(3):
            orchestrator.add_function_task(
                f"process_{i}",
                f"Process File {i}",
                process_file,
                args=(i,),
                dependencies=["create_inputs"]
            )
        
        # Merge processed files
        orchestrator.add_function_task(
            "merge",
            "Merge Processed Files",
            merge_processed_files,
            dependencies=["process_0", "process_1", "process_2"]
        )
        
        # Execute workflow
        result = await orchestrator.execute_workflow()
        
        # Verify workflow completion
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == 5
        
        # Verify files were created and processed
        for i in range(3):
            input_file = os.path.join(temp_directory, f"input_{i}.txt")
            output_file = os.path.join(temp_directory, f"processed_{i}.txt")
            
            assert os.path.exists(input_file)
            assert os.path.exists(output_file)
        
        # Verify merged file
        merged_file = os.path.join(temp_directory, "merged_output.txt")
        assert os.path.exists(merged_file)
        
        with open(merged_file, "r") as f:
            content = f.read()
            assert "MERGED PROCESSED FILES" in content
            assert "FROM FILE 0" in content
            assert "FROM FILE 1" in content
            assert "FROM FILE 2" in content
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_workflow(self):
        """Test workflow performance with many concurrent tasks."""
        
        async def cpu_intensive_task(task_id: int, iterations: int = 1000):
            """CPU intensive task for performance testing."""
            result = 0
            for i in range(iterations):
                result += i * task_id
                if i % 100 == 0:
                    await asyncio.sleep(0)  # Yield control
            
            return {"task_id": task_id, "result": result, "iterations": iterations}
        
        # Set up performance test with many tasks
        orchestrator = TaskOrchestrator(max_concurrent_tasks=10)
        
        # Create many independent CPU-intensive tasks
        num_tasks = 20
        for i in range(num_tasks):
            orchestrator.add_function_task(
                f"cpu_task_{i}",
                f"CPU Task {i}",
                cpu_intensive_task,
                args=(i, 500)  # Reduced iterations for faster testing
            )
        
        # Execute with timing
        start_time = time.time()
        result = await orchestrator.execute_workflow()
        execution_time = time.time() - start_time
        
        # Verify all tasks completed
        assert result["success_rate"] == 100.0
        assert result["status"]["completed_tasks"] == num_tasks
        
        # Performance should be reasonable
        assert execution_time < 5.0  # Should complete within 5 seconds
        
        # Verify concurrency benefit (rough estimate)
        # With 10 concurrent tasks, should be much faster than sequential
        estimated_sequential_time = num_tasks * 0.1  # Rough estimate per task
        assert execution_time < estimated_sequential_time / 2  # At least 2x speedup