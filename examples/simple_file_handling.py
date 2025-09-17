#!/usr/bin/env python3
"""
Simple Example: File Handling Workflow
======================================

This example demonstrates a basic file handling workflow using AgenticFlow:
- Create multiple text files with different content
- Process and validate the files
- Clean up by deleting the files

This showcases basic file operations in a structured workflow.
"""

import asyncio
import time
import os
import random
from typing import Dict, List, Any

import sys
sys.path.append('/Users/miladolad/OneDrive/Work Projects/ma_system/agenticflow/src')

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import RetryPolicy, TaskPriority


class FileProcessor:
    """Simple file handling processor."""
    
    def __init__(self):
        self.start_time = time.time()
        self.base_dir = "/Users/miladolad/OneDrive/Work Projects/ma_system/agenticflow/temp_files"
        self.created_files = []
        
    def log_event(self, stage: str, details: Dict[str, Any]):
        elapsed = time.time() - self.start_time
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        print(f"[{timestamp}] {stage}: {details}")
    
    async def create_directory(self, **kwargs) -> Dict[str, Any]:
        """Create the working directory for files."""
        self.log_event("CREATE_DIRECTORY", {"path": self.base_dir})
        
        await asyncio.sleep(0.1)  # Simulate work
        
        # Create directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        result = {
            "directory": self.base_dir,
            "exists": os.path.exists(self.base_dir),
            "is_directory": os.path.isdir(self.base_dir),
            "processing_time": time.time()
        }
        
        self.log_event("DIRECTORY_CREATED", {
            "path": self.base_dir,
            "exists": result["exists"]
        })
        
        return result
    
    async def create_files(self, file_count: int = 5, **kwargs) -> Dict[str, Any]:
        """Create multiple test files."""
        self.log_event("CREATE_FILES", {"count": file_count, "directory": self.base_dir})
        
        await asyncio.sleep(0.2)
        
        files_created = []
        
        file_contents = [
            "This is a test file for basic text content.\nLine 2\nLine 3",
            "File 2: Configuration Data\nSetting1=Value1\nSetting2=Value2\nSetting3=Value3",
            "File 3: Sample Data\n1,2,3,4,5\n6,7,8,9,10\n11,12,13,14,15",
            "File 4: Log Entry\n[INFO] Application started\n[DEBUG] Processing request\n[INFO] Request completed",
            "File 5: Documentation\n# Title\n## Subtitle\n- Item 1\n- Item 2\n- Item 3"
        ]
        
        for i in range(file_count):
            filename = f"test_file_{i+1}.txt"
            filepath = os.path.join(self.base_dir, filename)
            
            content = file_contents[i] if i < len(file_contents) else f"Test file {i+1} content\nGenerated automatically"
            
            # Write file
            with open(filepath, 'w') as f:
                f.write(content)
            
            file_info = {
                "filename": filename,
                "filepath": filepath,
                "size": len(content),
                "lines": len(content.split('\n'))
            }
            
            files_created.append(file_info)
            self.created_files.append(filepath)
        
        result = {
            "files_created": files_created,
            "total_files": len(files_created),
            "base_directory": self.base_dir,
            "processing_time": time.time()
        }
        
        self.log_event("FILES_CREATED", {
            "count": len(files_created),
            "total_size": sum(f["size"] for f in files_created)
        })
        
        return result
    
    async def validate_files(self, **kwargs) -> Dict[str, Any]:
        """Validate that files were created correctly."""
        self.log_event("VALIDATE_FILES", {"checking": len(self.created_files)})
        
        await asyncio.sleep(0.3)
        
        validation_results = []
        
        for filepath in self.created_files:
            filename = os.path.basename(filepath)
            
            exists = os.path.exists(filepath)
            is_file = os.path.isfile(filepath) if exists else False
            size = os.path.getsize(filepath) if exists else 0
            
            # Read content for validation
            content = ""
            line_count = 0
            if exists and is_file:
                with open(filepath, 'r') as f:
                    content = f.read()
                    line_count = len(content.split('\n'))
            
            validation_results.append({
                "filename": filename,
                "filepath": filepath,
                "exists": exists,
                "is_file": is_file,
                "size": size,
                "line_count": line_count,
                "valid": exists and is_file and size > 0
            })
        
        total_valid = sum(1 for r in validation_results if r["valid"])
        validation_success = total_valid == len(validation_results)
        
        result = {
            "validation_results": validation_results,
            "total_files": len(validation_results),
            "valid_files": total_valid,
            "validation_success": validation_success,
            "success_rate": total_valid / len(validation_results) if validation_results else 0,
            "processing_time": time.time()
        }
        
        self.log_event("VALIDATION_COMPLETE", {
            "valid": total_valid,
            "total": len(validation_results),
            "success_rate": f"{result['success_rate']:.1%}"
        })
        
        return result
    
    async def process_files(self, **kwargs) -> Dict[str, Any]:
        """Process the files (count lines, words, characters)."""
        self.log_event("PROCESS_FILES", {"processing": len(self.created_files)})
        
        await asyncio.sleep(0.4)
        
        processing_results = []
        total_stats = {"lines": 0, "words": 0, "chars": 0}
        
        for filepath in self.created_files:
            filename = os.path.basename(filepath)
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                
                lines = len(content.split('\n'))
                words = len(content.split())
                chars = len(content)
                
                processing_results.append({
                    "filename": filename,
                    "lines": lines,
                    "words": words,
                    "characters": chars,
                    "size_bytes": os.path.getsize(filepath)
                })
                
                total_stats["lines"] += lines
                total_stats["words"] += words
                total_stats["chars"] += chars
        
        result = {
            "processing_results": processing_results,
            "total_stats": total_stats,
            "files_processed": len(processing_results),
            "processing_time": time.time()
        }
        
        self.log_event("PROCESSING_COMPLETE", {
            "files": len(processing_results),
            "total_lines": total_stats["lines"],
            "total_words": total_stats["words"]
        })
        
        return result
    
    async def cleanup_files(self, **kwargs) -> Dict[str, Any]:
        """Delete the created files and directory."""
        self.log_event("CLEANUP", {"deleting": len(self.created_files)})
        
        await asyncio.sleep(0.2)
        
        deleted_files = []
        
        # Delete individual files
        for filepath in self.created_files:
            filename = os.path.basename(filepath)
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted_files.append(filename)
        
        # Delete directory if empty
        directory_deleted = False
        if os.path.exists(self.base_dir) and not os.listdir(self.base_dir):
            os.rmdir(self.base_dir)
            directory_deleted = True
        
        result = {
            "deleted_files": deleted_files,
            "files_deleted": len(deleted_files),
            "directory_deleted": directory_deleted,
            "cleanup_successful": len(deleted_files) == len(self.created_files),
            "processing_time": time.time()
        }
        
        self.log_event("CLEANUP_COMPLETE", {
            "files_deleted": len(deleted_files),
            "directory_deleted": directory_deleted
        })
        
        return result


async def run_file_handling():
    """Execute the file handling workflow."""
    print("📁 AgenticFlow Simple Example: File Handling Workflow")
    print("=" * 58)
    print()
    
    processor = FileProcessor()
    
    # Configure orchestrator
    retry_policy = RetryPolicy(
        max_attempts=2,
        initial_delay=0.1,
        max_delay=2.0,
        backoff_multiplier=2.0
    )
    
    orchestrator = TaskOrchestrator(
        max_concurrent_tasks=2,  # Some tasks can run in parallel
        default_retry_policy=retry_policy
    )
    
    print("🔨 Building File Handling Workflow...")
    print("-" * 38)
    
    # Task 1: Create directory
    orchestrator.add_function_task(
        "create_dir", "Create Directory",
        processor.create_directory,
        priority=TaskPriority.HIGH
    )
    
    # Task 2: Create files (depends on directory)
    orchestrator.add_function_task(
        "create_files", "Create Files",
        processor.create_files,
        args=(5,),  # Create 5 files
        dependencies=["create_dir"],
        priority=TaskPriority.HIGH
    )
    
    # Task 3: Validate files (depends on file creation)
    orchestrator.add_function_task(
        "validate_files", "Validate Files",
        processor.validate_files,
        dependencies=["create_files"],
        priority=TaskPriority.NORMAL
    )
    
    # Task 4: Process files (depends on validation, can run in parallel with other processing)
    orchestrator.add_function_task(
        "process_files", "Process Files",
        processor.process_files,
        dependencies=["validate_files"],
        priority=TaskPriority.NORMAL
    )
    
    # Task 5: Cleanup (depends on processing)
    orchestrator.add_function_task(
        "cleanup", "Cleanup Files",
        processor.cleanup_files,
        dependencies=["process_files"],
        priority=TaskPriority.LOW
    )
    
    # Execute the workflow
    print("🚀 Executing File Handling Workflow...")
    print("-" * 38)
    
    start_time = time.time()
    result = await orchestrator.execute_workflow()
    total_time = time.time() - start_time
    
    # Generate report
    print()
    print("=" * 58)
    print("📊 FILE HANDLING REPORT")
    print("=" * 58)
    
    success_rate = result["success_rate"]
    total_tasks = result["status"]["total_tasks"]
    completed_tasks = result["status"]["completed_tasks"]
    
    print(f"⏱️  Total Processing Time: {total_time:.2f} seconds")
    print(f"✅ Success Rate: {success_rate:.1f}%")
    print(f"📊 Tasks Completed: {completed_tasks}/{total_tasks}")
    print(f"🔄 Workflow Status: {'COMPLETED' if result['status']['is_complete'] else 'INCOMPLETE'}")
    
    if "dag_stats" in result:
        dag_stats = result["dag_stats"]
        print(f"📈 Processing Stages: {dag_stats.get('execution_levels', 'N/A')}")
        print(f"🎯 Critical Path: {' → '.join(dag_stats.get('critical_path', []))}")
    
    # Detailed breakdown
    print("\n" + "-" * 58)
    print("📋 TASK BREAKDOWN")
    print("-" * 58)
    
    if "task_results" in result:
        for task_id, task_info in result["task_results"].items():
            status = "✅" if task_info.get("state") == "completed" else "❌"
            task_name = task_info.get("name", task_id)
            execution_time = task_info.get("execution_time", 0)
            
            print(f"{status} {task_name}")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   🔄 Attempts: {task_info.get('attempts', 1)}")
            
            # Show task-specific results
            if task_info.get("result") and task_info["result"].get("success"):
                task_result = task_info["result"]["result"]
                if isinstance(task_result, dict):
                    if "directory" in task_result:
                        print(f"   📁 Directory: {os.path.basename(task_result['directory'])}")
                    elif "files_created" in task_result:
                        print(f"   📄 Files Created: {task_result['total_files']}")
                        print(f"   📏 Total Size: {sum(f['size'] for f in task_result['files_created'])} bytes")
                    elif "validation_success" in task_result:
                        print(f"   ✅ Valid Files: {task_result['valid_files']}/{task_result['total_files']}")
                        print(f"   📊 Success Rate: {task_result['success_rate']:.1%}")
                    elif "total_stats" in task_result:
                        stats = task_result['total_stats']
                        print(f"   📝 Total Lines: {stats['lines']}")
                        print(f"   🔤 Total Words: {stats['words']}")
                    elif "cleanup_successful" in task_result:
                        print(f"   🗑️  Files Deleted: {task_result['files_deleted']}")
                        print(f"   ✅ Cleanup: {'Success' if task_result['cleanup_successful'] else 'Failed'}")
            print()
    
    # Final assessment
    print("-" * 58)
    print("🎯 WORKFLOW ASSESSMENT")
    print("-" * 58)
    
    grade = "A+" if success_rate >= 95 else "A" if success_rate >= 85 else "B+" if success_rate >= 75 else "B"
    
    print(f"📊 Overall Grade: {grade}")
    print()
    
    if success_rate >= 95:
        print("✅ EXCELLENT: All file operations completed successfully")
        print("   • Directory created and managed properly")
        print("   • Files created, validated, and processed")
        print("   • Clean cleanup with no leftover files")
    elif success_rate >= 85:
        print("✅ GOOD: Most file operations completed successfully")
        print("   • Minor issues in some processing stages")
    else:
        print("⚠️  NEEDS IMPROVEMENT: Some file operations failed")
    
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Sequential workflow with dependencies")
    print("   • File system operations (create, read, delete)")
    print("   • Data validation and processing")
    print("   • Resource cleanup and management")
    print("   • Error handling and retry logic")
    
    return {
        "example_name": "File Handling Workflow",
        "grade": grade,
        "success_rate": success_rate,
        "execution_time": total_time,
        "tasks_completed": f"{completed_tasks}/{total_tasks}",
        "key_features": [
            "Directory management",
            "File creation and validation", 
            "Content processing",
            "Cleanup operations"
        ]
    }


if __name__ == "__main__":
    result = asyncio.run(run_file_handling())
    
    print()
    print("=" * 58)
    print(f"🏆 FINAL RESULT: {result['grade']} ({result['success_rate']:.1f}% success)")
    print("🚀 File Handling workflow validation complete!")
    print("=" * 58)