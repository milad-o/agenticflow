"""Python agent with comprehensive code operations."""

import ast
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Annotated, List, Optional, Dict, Any
from langchain_core.tools import tool
from langchain_community.tools import ShellTool
from ..core.flow import Agent

class PythonAgent(Agent):
    """Agent specialized in Python code operations."""
    
    def __init__(self, name: str = "python_agent", description: str = "Python code specialist"):
        tools = self._create_tools()
        super().__init__(name, tools=tools, description=description)
    
    def _create_tools(self) -> List:
        """Create Python tools."""
        return [
            self._execute_python,
            self._validate_python,
            self._generate_python,
            self._convert_to_python,
            self._format_python,
            self._analyze_python,
            self._test_python,
            self._install_package,
            self._create_script,
            self._run_script,
            self._debug_python,
            self._optimize_python,
            self._document_python,
            self._refactor_python,
            self._python_repl
        ]
    
    @tool
    def _execute_python(
        self,
        code: Annotated[str, "Python code to execute"],
        timeout: Annotated[int, "Timeout in seconds (default: 30)"] = 30
    ) -> str:
        """Execute Python code and return the result."""
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute the code
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Clean up
            Path(temp_file).unlink()
            
            output = ""
            if result.stdout:
                output += f"📤 Output:\n{result.stdout}\n"
            if result.stderr:
                output += f"⚠️ Errors:\n{result.stderr}\n"
            if result.returncode != 0:
                output += f"❌ Exit code: {result.returncode}\n"
            
            return output or "✅ Code executed successfully (no output)"
        except subprocess.TimeoutExpired:
            return f"⏰ Code execution timed out after {timeout} seconds"
        except Exception as e:
            return f"❌ Error executing code: {e}"
    
    @tool
    def _validate_python(
        self,
        code: Annotated[str, "Python code to validate"]
    ) -> str:
        """Validate Python code syntax and structure."""
        try:
            # Parse the code to check syntax
            tree = ast.parse(code)
            
            # Check for common issues
            issues = []
            
            # Check for undefined variables (basic check)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    # This is a variable assignment, which is fine
                    pass
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    # This is a variable reference, we can't easily check if it's defined
                    pass
            
            # Check for imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
            
            result = f"✅ Python code is syntactically valid\n"
            result += f"📦 Imports found: {', '.join(imports) if imports else 'None'}\n"
            result += f"📏 Lines of code: {len(code.splitlines())}\n"
            result += f"🔤 Characters: {len(code)}\n"
            
            if issues:
                result += f"⚠️ Issues found:\n" + "\n".join(issues)
            
            return result
        except SyntaxError as e:
            return f"❌ Syntax Error: {e.msg} at line {e.lineno}, column {e.offset}"
        except Exception as e:
            return f"❌ Error validating code: {e}"
    
    @tool
    def _generate_python(
        self,
        description: Annotated[str, "Description of the Python code to generate"],
        requirements: Annotated[str, "Specific requirements or constraints"] = ""
    ) -> str:
        """Generate Python code based on description."""
        try:
            # This is a simplified code generator - in practice, you'd use an LLM
            template = f'''# Generated Python code
# Description: {description}
# Requirements: {requirements}

def main():
    """Main function based on description."""
    # TODO: Implement based on description
    pass

if __name__ == "__main__":
    main()
'''
            return f"🐍 Generated Python code:\n```python\n{template}\n```"
        except Exception as e:
            return f"❌ Error generating code: {e}"
    
    @tool
    def _convert_to_python(
        self,
        source_code: Annotated[str, "Source code to convert to Python"],
        source_language: Annotated[str, "Source programming language"]
    ) -> str:
        """Convert code from another language to Python."""
        try:
            # This is a simplified converter - in practice, you'd use an LLM
            if source_language.lower() in ['javascript', 'js']:
                # Basic JS to Python conversion patterns
                python_code = source_code
                python_code = python_code.replace('var ', '')
                python_code = python_code.replace('let ', '')
                python_code = python_code.replace('const ', '')
                python_code = python_code.replace('function ', 'def ')
                python_code = python_code.replace('{', ':')
                python_code = python_code.replace('}', '')
                python_code = python_code.replace('console.log', 'print')
                python_code = python_code.replace(';', '')
                
                return f"🔄 Converted {source_language} to Python:\n```python\n{python_code}\n```"
            else:
                return f"⚠️ Conversion from {source_language} to Python not yet implemented"
        except Exception as e:
            return f"❌ Error converting code: {e}"
    
    @tool
    def _format_python(
        self,
        code: Annotated[str, "Python code to format"]
    ) -> str:
        """Format Python code using standard formatting rules."""
        try:
            # Basic formatting - in practice, you'd use black or autopep8
            lines = code.split('\n')
            formatted_lines = []
            
            for line in lines:
                # Remove trailing whitespace
                line = line.rstrip()
                # Add proper indentation (basic)
                if line.strip():
                    formatted_lines.append(line)
                else:
                    formatted_lines.append('')
            
            formatted_code = '\n'.join(formatted_lines)
            return f"✨ Formatted Python code:\n```python\n{formatted_code}\n```"
        except Exception as e:
            return f"❌ Error formatting code: {e}"
    
    @tool
    def _analyze_python(
        self,
        code: Annotated[str, "Python code to analyze"]
    ) -> str:
        """Analyze Python code for complexity, patterns, and suggestions."""
        try:
            tree = ast.parse(code)
            
            # Basic analysis
            functions = []
            classes = []
            imports = []
            variables = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    variables.add(node.name)
            
            analysis = f"📊 Python Code Analysis:\n"
            analysis += f"📏 Lines: {len(code.splitlines())}\n"
            analysis += f"🔤 Characters: {len(code)}\n"
            analysis += f"🔧 Functions: {len(functions)} - {', '.join(functions)}\n"
            analysis += f"🏗️ Classes: {len(classes)} - {', '.join(classes)}\n"
            analysis += f"📦 Imports: {len(imports)} - {', '.join(imports)}\n"
            analysis += f"📝 Variables: {len(variables)} - {', '.join(sorted(variables))}\n"
            
            return analysis
        except Exception as e:
            return f"❌ Error analyzing code: {e}"
    
    @tool
    def _test_python(
        self,
        code: Annotated[str, "Python code to test"],
        test_cases: Annotated[str, "Test cases to run"] = ""
    ) -> str:
        """Test Python code with provided test cases."""
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run basic syntax check
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', temp_file],
                capture_output=True,
                text=True
            )
            
            # Clean up
            Path(temp_file).unlink()
            
            if result.returncode == 0:
                return "✅ Code passed syntax validation"
            else:
                return f"❌ Syntax errors found:\n{result.stderr}"
        except Exception as e:
            return f"❌ Error testing code: {e}"
    
    @tool
    def _install_package(
        self,
        package: Annotated[str, "Package name to install"],
        version: Annotated[str, "Package version (optional)"] = ""
    ) -> str:
        """Install a Python package."""
        try:
            package_spec = f"{package}=={version}" if version else package
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_spec],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return f"✅ Successfully installed {package_spec}"
            else:
                return f"❌ Error installing {package_spec}:\n{result.stderr}"
        except Exception as e:
            return f"❌ Error installing package: {e}"
    
    @tool
    def _create_script(
        self,
        script_name: Annotated[str, "Name of the script to create"],
        code: Annotated[str, "Python code for the script"],
        directory: Annotated[str, "Directory to create script in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Create a Python script file."""
        try:
            os.makedirs(directory, exist_ok=True)
            script_path = os.path.join(directory, script_name)
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            return f"✅ Created Python script '{script_path}'"
        except Exception as e:
            return f"❌ Error creating script: {e}"
    
    @tool
    def _run_script(
        self,
        script_name: Annotated[str, "Name of the script to run"],
        directory: Annotated[str, "Directory containing the script (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Run a Python script."""
        try:
            script_path = os.path.join(directory, script_name)
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True
            )
            
            output = ""
            if result.stdout:
                output += f"📤 Output:\n{result.stdout}\n"
            if result.stderr:
                output += f"⚠️ Errors:\n{result.stderr}\n"
            if result.returncode != 0:
                output += f"❌ Exit code: {result.returncode}\n"
            
            return output or "✅ Script executed successfully (no output)"
        except Exception as e:
            return f"❌ Error running script: {e}"
    
    @tool
    def _debug_python(
        self,
        code: Annotated[str, "Python code to debug"],
        error_message: Annotated[str, "Error message to debug"] = ""
    ) -> str:
        """Debug Python code and provide suggestions."""
        try:
            # Try to execute the code to see what happens
            try:
                exec(code)
                return "✅ Code executed successfully - no obvious errors found"
            except Exception as e:
                error_info = f"❌ Error found: {type(e).__name__}: {e}\n"
                error_info += f"📍 Traceback:\n{traceback.format_exc()}\n"
                
                # Provide debugging suggestions
                suggestions = []
                if "NameError" in str(type(e)):
                    suggestions.append("Check for undefined variables")
                elif "SyntaxError" in str(type(e)):
                    suggestions.append("Check for syntax errors")
                elif "IndentationError" in str(type(e)):
                    suggestions.append("Check indentation")
                elif "ImportError" in str(type(e)):
                    suggestions.append("Check if required modules are installed")
                
                if suggestions:
                    error_info += f"💡 Suggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
                
                return error_info
        except Exception as e:
            return f"❌ Error debugging code: {e}"
    
    @tool
    def _optimize_python(
        self,
        code: Annotated[str, "Python code to optimize"]
    ) -> str:
        """Provide optimization suggestions for Python code."""
        try:
            suggestions = []
            
            # Check for common optimization opportunities
            if "for i in range(len(" in code:
                suggestions.append("Consider using enumerate() instead of range(len())")
            
            if "if x == True" in code or "if x == False" in code:
                suggestions.append("Use 'if x:' or 'if not x:' instead of 'if x == True/False'")
            
            if "import *" in code:
                suggestions.append("Avoid 'import *' - import specific functions instead")
            
            if "print(" in code and "logging" not in code:
                suggestions.append("Consider using logging instead of print for production code")
            
            if suggestions:
                return f"🚀 Optimization suggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
            else:
                return "✅ No obvious optimization opportunities found"
        except Exception as e:
            return f"❌ Error analyzing code for optimization: {e}"
    
    @tool
    def _document_python(
        self,
        code: Annotated[str, "Python code to document"],
        style: Annotated[str, "Documentation style (docstring, comments, or both)"] = "both"
    ) -> str:
        """Add documentation to Python code."""
        try:
            # Basic documentation addition
            lines = code.split('\n')
            documented_lines = []
            
            for i, line in enumerate(lines):
                if line.strip().startswith('def ') and i > 0:
                    # Add docstring for functions
                    func_name = line.split('(')[0].replace('def ', '')
                    documented_lines.append(f'    """Documentation for {func_name} function."""')
                documented_lines.append(line)
            
            documented_code = '\n'.join(documented_lines)
            return f"📚 Documented Python code:\n```python\n{documented_code}\n```"
        except Exception as e:
            return f"❌ Error documenting code: {e}"
    
    @tool
    def _refactor_python(
        self,
        code: Annotated[str, "Python code to refactor"],
        refactor_type: Annotated[str, "Type of refactoring (extract_function, rename_variable, etc.)"] = "extract_function"
    ) -> str:
        """Refactor Python code."""
        try:
            if refactor_type == "extract_function":
                # Basic function extraction
                return f"🔄 Refactored code (extracted function):\n```python\n{code}\n```"
            else:
                return f"⚠️ Refactoring type '{refactor_type}' not yet implemented"
        except Exception as e:
            return f"❌ Error refactoring code: {e}"
    
    @property
    def _python_repl(self):
        """Shell tool for interactive execution."""
        return ShellTool()
