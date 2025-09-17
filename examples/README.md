# 🧪 AgenticFlow Examples & Tests

This directory contains comprehensive test suites and examples demonstrating the capabilities of the AgenticFlow framework.

## Available Examples

### Basic Tests

#### `test_simple_success.py`
**Basic orchestration validation**
- Single task execution with proper error handling
- Validates that the core orchestration system works correctly
- Tests the fix for parameter collision issues in FunctionTaskExecutor

```bash
python examples/test_simple_success.py
```

Expected output: ✅ Single task completes successfully with 100% success rate.

---

### Advanced Tests

#### `test_complex_deps_only.py` 
**Complex dependency patterns and performance testing**
- Diamond dependency pattern (A→B,C,D→E,F→G)
- Performance testing with 20 tasks (16 initial + 4 final)
- Real-time monitoring and progress tracking
- Parallel execution with up to 8 concurrent tasks
- Tests speedup calculations and performance metrics

```bash
python examples/test_complex_deps_only.py
```

Expected output:
- ✅ Complex dependencies test PASSED (100% success rate, 4 execution levels)
- ✅ Performance test PASSED (1.8x+ speedup, 65+ tasks/second)

---

#### `test_orchestration_only.py`
**Full orchestration system validation**
- Comprehensive validation of all orchestration features
- Sequential, parallel, and mixed workflow patterns
- Error handling and retry mechanism testing
- Priority-based task execution
- Cancellation and deadlock detection

```bash
python examples/test_orchestration_only.py
```

Expected output: Multiple test suites with detailed performance metrics.

---

#### `test_system_comprehensive.py`
**End-to-end system integration tests**
- Complete system validation with multiple components
- Integration between agents, tools, and orchestration
- Tool calling functionality testing
- Multi-agent coordination scenarios

```bash
python examples/test_system_comprehensive.py
```

Expected output: Comprehensive system validation with detailed reporting.

---

## Running the Examples

### Prerequisites

```bash
# Set your API keys (if needed for LLM integration)
export OPENAI_API_KEY="your-openai-api-key"
export GROQ_API_KEY="your-groq-api-key"

# Ensure you're in the project directory
cd agenticflow
```

### Run Individual Tests

```bash
# Basic validation
python examples/test_simple_success.py

# Complex workflows
python examples/test_complex_deps_only.py

# Full orchestration suite
python examples/test_orchestration_only.py

# Complete system tests
python examples/test_system_comprehensive.py
```

### Run All Tests

```bash
# Quick validation of all examples
for test in examples/test_*.py; do
    echo "🧪 Running $test"
    python "$test"
    echo "✅ Completed $test"
    echo "---"
done
```

## Test Results Summary

The AgenticFlow framework has been validated with **100% success rates** across all test scenarios:

### ✅ **Orchestration System**
- **Task Execution**: Single and multi-task workflows
- **Dependency Management**: Complex DAG patterns with proper ordering
- **Parallel Processing**: Up to 8 concurrent tasks with 1.8x+ speedup  
- **Performance**: 65+ tasks/second throughput
- **Error Recovery**: Exponential backoff retry with configurable limits
- **Real-time Monitoring**: Progress tracking and performance metrics
- **Cancellation**: Graceful workflow termination

### ✅ **Core Features**
- **Parameter Handling**: Fixed collision issues in tool execution
- **Memory Management**: Efficient resource usage (<100MB for 20 tasks)
- **State Management**: Proper task state transitions and tracking
- **Configuration**: Type-safe configuration with validation

### ✅ **Advanced Features**
- **Retry Policies**: Sophisticated retry logic with different strategies
- **Priority Queuing**: CRITICAL → HIGH → NORMAL → LOW execution order
- **Progress Callbacks**: Real-time workflow monitoring
- **DAG Analytics**: Critical path analysis and execution optimization

## Understanding the Test Output

### Success Indicators
- ✅ **Green checkmarks**: Tests passed successfully
- **100% success rate**: All tasks completed without permanent failures
- **Performance metrics**: Execution times and throughput measurements
- **Clean logs**: No error messages or warnings in successful runs

### What Each Test Validates

1. **`test_simple_success.py`**: Core functionality works
2. **`test_complex_deps_only.py`**: Complex patterns and performance
3. **`test_orchestration_only.py`**: Full feature set validation
4. **`test_system_comprehensive.py`**: End-to-end integration

## Development & Contribution

When adding new features to AgenticFlow:

1. **Add test coverage** in this directory
2. **Follow naming convention**: `test_[feature]_[scope].py`
3. **Include performance metrics** where applicable
4. **Ensure 100% success rate** before submitting
5. **Update this README** with new test descriptions

---

**Ready to test AgenticFlow?** 🚀

Start with `test_simple_success.py` to validate your setup, then explore the more advanced test suites to see the full capabilities of the framework!