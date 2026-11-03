# Empório da Música CLI

A small Python command-line agent for the Empório da Música case. It answers product questions from the supplied products CSV, store-policy questions from the policy PDF, and redirects unrelated questions. Order and customer records are never sent to the model.

## Run

Python 3.10 or newer is required. Policy extraction uses the declared pure-Python `pypdf` dependency; no system PDF utility is needed. Install the project once in a virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Then run the commands below in that activated environment.

```sh
python3 tools/agent_cli.py "Quanto custa o Takamine GD20?"
python3 tools/agent_cli.py "Comprei online há cinco dias e me arrependi. Posso devolver?"
ORDER_DATA_DIR=examples/fixtures python3 tools/agent_cli.py "Qual é o status do meu pedido?"
python3 tools/agent_cli.py
```

The model defaults to `lfm3-omni-2b` at `http://100.111.77.36:1234/v1`, using the OpenAI-compatible Chat Completions endpoint. Change `OPENAI_BASE_URL` and `OPENAI_MODEL` to use another server or model. A local server does not need an API key; set `OPENAI_API_KEY` only if your server requires one. The CLI uses local templates when the server is unavailable.

To use the example settings, copy `.env.example` to `.env` and load it in your shell before running the CLI:

```sh
cp .env.example .env
set -a
source .env
set +a
python3 tools/agent_cli.py "Quanto custa o Takamine GD20?"
```

The CLI reads environment variables directly; it does not parse `.env` files itself. Loading `.env` in the shell avoids a dotenv dependency. Keep real credentials in `.env`, which is ignored by Git.

## Technical choices

**Approach and retrieval.** A keyword router sends product questions to the products CSV, store-rule questions to the policy PDF, and order-status requests to a local verifier. Product lookup uses word overlap against product names and returns the unique best match. Policy lookup extracts up to 18,000 characters with `pypdf`, installed from the declared project dependency. This direct approach fits the fixed demo sources. I did not evaluate a vector database or agent framework because the brief does not require semantic retrieval.

**Model and prompt.** The default is the locally served `lfm3-omni-2b` model supplied for this project. The CLI calls its OpenAI-compatible Chat Completions endpoint with Python's `urllib`, so no API SDK is needed. The system prompt sets a cordial Brazilian Portuguese tone, restricts answers to retrieved evidence, asks the model to state when facts are missing, and requires the full return conditions when answering about regret returns. It also labels stock as a snapshot and tells the model not to disclose personal data. The CLI does not enforce these prompt instructions with an output validator.

**Interface and state.** The CLI supports one-shot and interactive use because the brief permits a CLI and the examples need no web interface. It does not save conversation history because this demonstration handles one request at a time and does not require memory.

**Data handling.** Product and policy evidence can go to the model. Order status is checked before model routing by matching the order ID and registered email locally. The CLI hides the email input and returns only status and estimated delivery. Real customer and order CSVs stay local and are ignored by Git; the public example uses fictional rows in `examples/fixtures/`. The hidden email is used only in the order lookup. Matched product and policy questions are sent to the model as typed, so do not include contact details in those messages. Out-of-scope questions use a local reply. Email matching is a basic demonstration safeguard, not production authentication.

If the model request fails, local replies cover product lookup, the documented online-return case, and out-of-scope questions. Other policy questions need the model to summarize the retrieved manual text.

For the full decision record, evidence links, and limits, see [Technical decisions](docs/architecture.md).

## Limits

- Product matching is lexical and designed for the supplied case, not a production catalog.
- Stock is shown from the supplied CSV snapshot. It is not live inventory.
- Order lookup asks for the order ID and registered email, then returns only status and estimated delivery. This email check is a basic demo safeguard, not production identity verification. Real customer and order CSVs are not included in the public repository.
- Install the project dependencies with `python -m pip install -e .` to enable policy extraction.
- Prompt rules are instructions, not enforced guarantees; matched product and policy questions are sent to the configured model as typed.

## Future improvements

- Replace email matching with a stronger identity check before using real customer data.
- Improve product matching to handle more paraphrases and spelling variations.
- Add automated checks for source-backed answers and out-of-scope handling.

## Development assistance

OpenAI Codex was used to inspect the challenge materials, implement and review the prototype, and maintain the project documentation. Decisions and limitations were checked against the supplied brief and source files.

Four CLI conversations are saved in [examples/conversations.md](examples/conversations.md). They cover product lookup, a return-policy question, an order-status lookup using fictional data, and an out-of-scope question.

The CLI uses the OpenAI-compatible `/chat/completions` endpoint so it can connect to local inference servers.

## Python code checks

Run the project checker:

```sh
sh scripts/check_python.sh
```

The script uses Ruff from `PATH`, or downloads it into the `uvx` cache when `uvx` is installed. Otherwise, install Ruff in a virtual environment first. It checks Python files under `tools/` and `scripts/` for common errors, import order, formatting, function complexity, and a 300-line file limit. Set `PYTHON_MAX_FILE_LINES` to change the size limit. Ruff settings live in `pyproject.toml`.

The checker enforces a 300-line file limit and Ruff complexity checks. Treat those limits as review triggers, not measures of responsibility. Split a file when unrelated changes repeatedly touch it or it owns distinct data sources and workflows.
