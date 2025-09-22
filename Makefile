UV ?= uv
QUERY ?= Analyze sales.csv then generate a report
CAPS ?= examples/capabilities/example_caps.yaml

.PHONY: help sync-dev sync-groq-ollama sync-all test test-unit test-integration health demo-llm demo-supervisor supervisor-cli precommit

help:
	@echo "Common targets:"
	@echo "  make sync-dev            # Install dev deps"
	@echo "  make sync-groq-ollama    # Dev deps + Groq LLM + Ollama embeddings"
	@echo "  make sync-all            # Dev deps + all optional extras"
	@echo "  make test                # Run all tests"
	@echo "  make test-unit           # Run unit tests only"
	@echo "  make test-integration    # Run integration tests"
	@echo "  make health              # Provider health check"
	@echo "  make demo-llm            # LLM + Embedding demo"
	@echo "  make demo-supervisor     # Supervisor + LLM demo"
	@echo "  make supervisor-cli      # Supervisor CLI (use QUERY=... CAPS=...)"
	@echo "  make precommit           # Run pre-commit hooks"

sync-dev:
	$(UV) sync --extra dev

sync-groq-ollama:
	$(UV) sync --extra dev --extra llm-groq --extra embed-ollama

sync-all:
	$(UV) sync --extra dev --extra llm-groq --extra llm-azure --extra embed-ollama --extra embed-hf

test:
	$(UV) run pytest -q

test-unit:
	$(UV) run pytest -q -k "not integration"

test-integration:
	$(UV) run pytest -q -m integration

health:
	$(UV) run python examples/utils/health_check.py

demo-llm:
	$(UV) run python examples/dev_llm_embed_demo.py

demo-supervisor:
	$(UV) run python examples/supervisor_llm_demo.py

supervisor-cli:
	$(UV) run python examples/supervisor_cli.py --query "$(QUERY)" --caps "$(CAPS)"

precommit:
	pre-commit run --all-files || true

demo-config:
	$(UV) run python examples/config_demo.py --config "$(CONFIG)"

demo-realistic:
	$(UV) run python examples/02_sales_workflow/sales_workflow.py

demo-file-qna:
	$(UV) run python examples/01_file_qna/file_qa.py --path examples/01_file_qna/content --outdir examples/01_file_qna/artifacts --question "Compare science vs law vs literature; common themes across nature, science, literature, business, law"
