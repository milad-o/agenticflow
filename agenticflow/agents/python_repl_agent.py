"""
Python REPL Agent - Code Execution and Analysis
==============================================

Safe Python code execution with comprehensive error handling and result formatting.
"""

import io
import sys
import contextlib
import traceback
import ast
import json
from typing import Dict, List, Any, Optional
import subprocess
import tempfile
import os


class PythonREPLAgent:
    """Agent for safe Python code execution and analysis."""

    def __init__(self):
        self.capabilities = [
            "python_code_execution",
            "data_analysis",
            "script_generation",
            "package_management",
            "code_validation",
            "mathematical_computation"
        ]
        self.execution_history = []
        self.installed_packages = set()

    async def arun(self, task: str) -> Dict[str, Any]:
        """Async execution wrapper."""
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute Python code or analyze programming tasks."""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ["execute", "run", "python", "code", "script"]):
            return self._execute_code_task(task)
        elif any(keyword in task_lower for keyword in ["analyze", "data", "pandas", "numpy"]):
            return self._analyze_data_task(task)
        elif any(keyword in task_lower for keyword in ["install", "package", "pip", "requirement"]):
            return self._manage_packages_task(task)
        elif any(keyword in task_lower for keyword in ["validate", "check", "syntax"]):
            return self._validate_code_task(task)
        else:
            return self._generate_code_solution(task)

    def _execute_code_task(self, task: str) -> Dict[str, Any]:
        """Execute Python code safely."""
        # Extract code from task
        code = self._extract_code_from_task(task)
        if not code:
            return {
                "action": "code_execution",
                "success": False,
                "error": "No Python code found in task",
                "suggestion": "Please provide Python code to execute"
            }

        result = self._safe_execute(code)
        self.execution_history.append({
            "code": code,
            "result": result,
            "timestamp": self._get_timestamp()
        })

        return {
            "action": "python_execution",
            "success": result.get("success", False),
            "code": code,
            "output": result.get("output", ""),
            "error": result.get("error"),
            "execution_time": result.get("execution_time", 0),
            "variables_created": result.get("variables", [])
        }

    def _analyze_data_task(self, task: str) -> Dict[str, Any]:
        """Generate data analysis code."""
        analysis_code = self._generate_analysis_code(task)
        result = self._safe_execute(analysis_code)

        return {
            "action": "data_analysis",
            "success": result.get("success", False),
            "analysis_code": analysis_code,
            "output": result.get("output", ""),
            "error": result.get("error"),
            "insights": self._extract_insights_from_output(result.get("output", ""))
        }

    def _manage_packages_task(self, task: str) -> Dict[str, Any]:
        """Handle package installation and management."""
        packages = self._extract_packages_from_task(task)
        results = []

        for package in packages:
            try:
                # Use subprocess to install package
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    self.installed_packages.add(package)
                    results.append({
                        "package": package,
                        "success": True,
                        "message": f"Successfully installed {package}"
                    })
                else:
                    results.append({
                        "package": package,
                        "success": False,
                        "error": result.stderr
                    })
            except Exception as e:
                results.append({
                    "package": package,
                    "success": False,
                    "error": str(e)
                })

        return {
            "action": "package_management",
            "packages_processed": packages,
            "results": results,
            "installed_packages": list(self.installed_packages)
        }

    def _validate_code_task(self, task: str) -> Dict[str, Any]:
        """Validate Python code syntax and structure."""
        code = self._extract_code_from_task(task)
        if not code:
            return {
                "action": "code_validation",
                "success": False,
                "error": "No code provided for validation"
            }

        validation_result = self._validate_syntax(code)
        return {
            "action": "code_validation",
            "code": code,
            **validation_result
        }

    def _generate_code_solution(self, task: str) -> Dict[str, Any]:
        """Generate Python code solution for a given problem."""
        # This would ideally use an LLM to generate code
        # For now, provide template solutions for common tasks

        task_lower = task.lower()

        if "csv" in task_lower and ("read" in task_lower or "load" in task_lower):
            code = """
import pandas as pd

# Read CSV file
df = pd.read_csv('your_file.csv')
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(df.head())
"""
        elif "json" in task_lower and ("read" in task_lower or "parse" in task_lower):
            code = """
import json

# Read JSON file
with open('your_file.json', 'r') as f:
    data = json.load(f)

print(f"Type: {type(data)}")
print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}")
print(json.dumps(data, indent=2)[:500])
"""
        elif "plot" in task_lower or "chart" in task_lower or "graph" in task_lower:
            code = """
import matplotlib.pyplot as plt
import numpy as np

# Create sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title('Sample Plot')
plt.xlabel('X values')
plt.ylabel('Y values')
plt.grid(True)
plt.show()
"""
        else:
            code = f"""
# Solution for: {task}
# TODO: Implement specific solution

print("Task: {task}")
print("This is a template. Please specify your requirements.")
"""

        return {
            "action": "code_generation",
            "task": task,
            "generated_code": code,
            "suggestion": "Review and modify the generated code as needed"
        }

    def _safe_execute(self, code: str) -> Dict[str, Any]:
        """Execute code safely with output capture."""
        import time
        start_time = time.time()

        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        # Track variables before execution
        globals_before = set(globals().keys())

        try:
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer

            # Execute the code
            exec(code, globals())

            # Get output
            output = stdout_buffer.getvalue()
            error_output = stderr_buffer.getvalue()

            # Track new variables
            globals_after = set(globals().keys())
            new_variables = list(globals_after - globals_before)

            execution_time = time.time() - start_time

            return {
                "success": True,
                "output": output,
                "error": error_output if error_output else None,
                "execution_time": execution_time,
                "variables": new_variables
            }

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "output": stdout_buffer.getvalue(),
                "error": f"{type(e).__name__}: {str(e)}",
                "traceback": traceback.format_exc(),
                "execution_time": execution_time,
                "variables": []
            }
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _validate_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python code syntax."""
        try:
            ast.parse(code)
            return {
                "success": True,
                "valid": True,
                "message": "Code syntax is valid"
            }
        except SyntaxError as e:
            return {
                "success": False,
                "valid": False,
                "error": f"Syntax error at line {e.lineno}: {e.msg}",
                "line": e.lineno,
                "column": e.offset
            }
        except Exception as e:
            return {
                "success": False,
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }

    def _extract_code_from_task(self, task: str) -> str:
        """Extract Python code from task description."""
        # Look for code blocks
        if "```python" in task:
            start = task.find("```python") + 9
            end = task.find("```", start)
            if end != -1:
                return task[start:end].strip()

        if "```" in task:
            start = task.find("```") + 3
            end = task.find("```", start)
            if end != -1:
                code = task[start:end].strip()
                # Simple heuristic to check if it's Python
                if any(keyword in code for keyword in ["import", "def", "class", "print", "="]):
                    return code

        # If no code blocks, check if the entire task looks like code
        if any(keyword in task for keyword in ["import ", "def ", "class ", "print(", " = "]):
            return task.strip()

        return ""

    def _extract_packages_from_task(self, task: str) -> List[str]:
        """Extract package names from installation task."""
        packages = []

        # Look for explicit package mentions
        words = task.split()
        for i, word in enumerate(words):
            if word.lower() in ["install", "pip"] and i + 1 < len(words):
                # Next words might be packages
                j = i + 1
                while j < len(words) and not words[j].startswith('-'):
                    package = words[j].strip(',').strip()
                    if package and not package.lower() in ["install", "pip", "package"]:
                        packages.append(package)
                    j += 1

        # Look for requirements.txt style
        lines = task.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '==' in line:
                package = line.split('==')[0].strip()
                packages.append(package)

        return packages

    def _generate_analysis_code(self, task: str) -> str:
        """Generate data analysis code based on task."""
        task_lower = task.lower()

        if "csv" in task_lower:
            return """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load and analyze CSV data
df = pd.read_csv('data.csv')  # Update with actual filename
print("Dataset Info:")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print("\\nData Types:")
print(df.dtypes)
print("\\nSummary Statistics:")
print(df.describe())
print("\\nMissing Values:")
print(df.isnull().sum())

# Basic visualizations
if len(df.columns) > 1:
    df.hist(figsize=(12, 8))
    plt.tight_layout()
    plt.show()
"""
        elif "json" in task_lower:
            return """
import json
import pandas as pd

# Load and analyze JSON data
with open('data.json', 'r') as f:  # Update with actual filename
    data = json.load(f)

print(f"Data type: {type(data)}")
if isinstance(data, dict):
    print(f"Keys: {list(data.keys())}")
elif isinstance(data, list):
    print(f"List length: {len(data)}")
    if data and isinstance(data[0], dict):
        print(f"First item keys: {list(data[0].keys())}")

# Convert to DataFrame if possible
try:
    df = pd.json_normalize(data)
    print(f"\\nDataFrame shape: {df.shape}")
    print(df.head())
except:
    print("Could not convert to DataFrame")
"""
        else:
            return """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# General data analysis template
print("Starting data analysis...")
# Add your data loading and analysis code here
"""

    def _extract_insights_from_output(self, output: str) -> List[str]:
        """Extract insights from analysis output."""
        insights = []
        lines = output.split('\n')

        for line in lines:
            if 'shape:' in line.lower():
                insights.append(f"Dataset dimensions: {line.strip()}")
            elif 'columns:' in line.lower():
                insights.append(f"Available columns: {line.strip()}")
            elif 'missing' in line.lower() and 'values' in line.lower():
                insights.append(f"Data quality: {line.strip()}")

        return insights

    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get code execution history."""
        return self.execution_history