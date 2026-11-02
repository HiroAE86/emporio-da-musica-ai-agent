# Empório da Música CLI

A small Python command-line agent for the Empório da Música case. It answers product questions from the supplied products CSV, store-policy questions from the policy PDF, and redirects unrelated questions. Order and customer records are never sent to the model.

## Run

Python 3.10 or newer and `pdftotext` are required. No Python packages need installation.

```sh
python3 tools/agent_cli.py "Quanto custa o Takamine GD20?"
python3 tools/agent_cli.py "Comprei online há cinco dias e me arrependi. Posso devolver?"
python3 tools/agent_cli.py
```

The model defaults to `lfm3-omni-2b` at `http://100.111.77.36:1234/v1`, using the OpenAI-compatible Chat Completions endpoint. Change `OPENAI_BASE_URL` and `OPENAI_MODEL` to use another server or model. A local server does not need an API key; set `OPENAI_API_KEY` only if your server requires one. The CLI uses local templates when the server is unavailable.

## Design

The CLI uses a small keyword router and direct retrieval from two approved sources. Product lookup reads the products CSV and returns the matching row. Policy lookup extracts text from the store-policy PDF with `pdftotext`. The model receives the matching product row or policy text through the OpenAI-compatible Chat Completions API. Customer and order CSVs are excluded.

The CLI does not retain conversation history. It uses local templates when the API request fails. These templates cover product lookup, online-return policy, and out-of-scope requests. Other policy questions need the model API to summarize the retrieved policy text.

## Limits

- Product matching is lexical and designed for the supplied case, not a production catalog.
- Stock is shown from the supplied CSV snapshot. It is not live inventory.
- Order status is not supported because the project has no requester verification flow.
- Install `pdftotext` to answer policy questions.

## Development assistance

OpenAI Codex was used to inspect the challenge materials, implement and review the prototype, and maintain the project documentation. Decisions and limitations were checked against the supplied brief and source files.

The required set of three to five saved example conversations has not been added yet.

The CLI uses the OpenAI-compatible `/chat/completions` endpoint so it can connect to local inference servers.

## Python code checks

Run the project checker:

```sh
sh scripts/check_python.sh
```

The script uses Ruff from `PATH`, or downloads it into the `uvx` cache when `uvx` is installed. Otherwise, install Ruff in a virtual environment first. It checks Python files under `tools/` and `scripts/` for common errors, import order, formatting, function complexity, and a 300-line file limit. Set `PYTHON_MAX_FILE_LINES` to change the size limit. Ruff settings live in `pyproject.toml`.

The size and complexity limits are warning signals, not a measure of whether a file has one clear responsibility. During review, split a file when unrelated changes repeatedly touch it or when it owns distinct data sources and workflows.
