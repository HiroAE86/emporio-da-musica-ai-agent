# Shortcuts for the Empório da Música agent. Run `make help` to list them.
# If a .env file exists, its OPENAI_* settings are loaded automatically.

VENV ?= .venv
PY := $(VENV)/bin/python
CLI := $(PY) tools/agent_cli.py

-include .env
export OPENAI_BASE_URL OPENAI_MODEL OPENAI_API_KEY AGENT_TOOLS AGENT_TOOL_STRATEGY

.PHONY: help setup preflight test lint demo chat ask order policies qa clean

help: ## List available commands
	@grep -E "^[a-z]+:.*## " $(MAKEFILE_LIST) | awk -F ":.*## " "{printf \"  make %-10s %s\n\", \$$1, \$$2}"

$(PY):
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -e .

setup: $(PY) ## Create .venv and install the project

preflight: $(PY) ## Check data files and the model endpoint
	@$(CLI) --preflight

test: $(PY) ## Run the offline test suite
	@$(PY) -m unittest discover -s tests -v

lint: $(PY) ## Run Ruff lint and format checks
	@$(PY) -m pip install -q ruff
	@PATH="$(VENV)/bin:$$PATH" sh scripts/check_python.sh

policies: $(PY) ## Regenerate the markdown policy wiki from the source PDF
	@$(PY) tools/policy_markdown.py

demo: $(PY) ## Run the example questions from the case
	@for q in \
		"Quanto custa o Takamine GD20?" \
		"Quais violões vocês têm até R$$ 1.000?" \
		"Comprei online há cinco dias e me arrependi. Posso devolver?" \
		"Vocês aceitam devolução de produto com defeito?" \
		"Qual o endereço da loja?" \
		"Quais formas de pagamento vocês aceitam?" \
		"Qual é a capital da França?"; do \
		echo; echo "Cliente: $$q"; $(CLI) "$$q"; \
	done

order: $(PY) ## Order status demo with fixture data (TESTE-100, cliente@example.test, 67999990000)
	@ORDER_DATA_DIR=examples/fixtures $(CLI) "Qual é o status do meu pedido?"

qa: $(PY) ## Run conversational QA scenarios
	@$(PY) tools/qa_runner.py

ask: $(PY) ## Ask one question: make ask Q="Quanto custa o Yamaha C40?"
	@$(CLI) "$(Q)"

chat: $(PY) ## Start an interactive conversation
	@$(CLI)

clean: ## Remove the virtualenv and caches
	rm -rf $(VENV) .ruff_cache tools/__pycache__ tests/__pycache__ *.egg-info
