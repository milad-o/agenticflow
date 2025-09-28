# AgenticFlow Makefile
# Common development tasks

.PHONY: help install test test-unit test-integration test-e2e lint format clean docs examples demos quick-demo full-demo test-runner

# Default target
help:
	@echo "AgenticFlow Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies"
	@echo "  install-dev Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test        Run all tests"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-e2e    Run end-to-end tests only"
	@echo "  test-cov    Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint        Run linters"
	@echo "  format      Format code"
	@echo "  type-check  Run type checking"
	@echo ""
	@echo "Documentation:"
	@echo "  docs        Build documentation"
	@echo "  examples    Run example scripts"
	@echo ""
	@echo "Demos (Working with Tangible Results):"
	@echo "  demos         Run all working demos"
	@echo "  quick-demo    Run quick demo (0.98s execution)"
	@echo "  full-demo     Run comprehensive demo (3 tasks, 1.52s avg)"
	@echo "  research-demo Run research & writing team (saves markdown report)"
	@echo "  test-runner   Run comprehensive test suite"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean       Clean temporary files"
	@echo "  clean-all   Clean everything including caches"

# Setup
install:
	uv sync

install-dev:
	uv sync --dev

# Testing
test:
	uv run pytest

test-unit:
	uv run pytest tests/unit/ -m unit

test-integration:
	uv run pytest tests/integration/ -m integration

test-e2e:
	uv run pytest tests/e2e/ -m e2e

test-cov:
	uv run pytest --cov=agenticflow --cov-report=html --cov-report=term

# Code Quality
lint:
	uv run ruff check agenticflow/ tests/ examples/
	uv run mypy agenticflow/

format:
	uv run ruff format agenticflow/ tests/ examples/

type-check:
	uv run mypy agenticflow/

# Documentation
docs:
	@echo "Building documentation..."
	@echo "Documentation is in docs/ directory"

examples:
	@echo "Running basic examples..."
	uv run python examples/basic/hello_world.py
	uv run python examples/basic/method_chaining.py

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

clean-all: clean
	rm -rf .venv/
	rm -rf uv.lock
	rm -rf workspaces/
	rm -rf logs/

# Development workflow
dev-setup: install-dev
	@echo "Development environment ready!"

ci: lint type-check test
	@echo "CI checks passed!"

# Run specific examples
example-hello:
	uv run python examples/basic/hello_world.py

example-chaining:
	uv run python examples/basic/method_chaining.py

example-advanced:
	uv run python examples/advanced/research_and_writing_workflow.py

# Demos with tangible results
demos: quick-demo full-demo research-demo
	@echo "All demos completed!"

quick-demo:
	@echo "Running quick demo (0.98s execution)..."
	uv run python demos/quick_demo.py

full-demo:
	@echo "Running comprehensive demo (3 tasks, 1.52s avg)..."
	uv run python demos/comprehensive_demo.py

research-demo:
	@echo "Running research & writing team demo (saves markdown report)..."
	uv run python demos/research_and_write_team.py

test-runner:
	@echo "Running comprehensive test suite..."
	uv run python tests/test_runner.py

# Quick test without API keys
test-simple:
	uv run python examples/basic/hello_world.py
	uv run python examples/basic/method_chaining.py
