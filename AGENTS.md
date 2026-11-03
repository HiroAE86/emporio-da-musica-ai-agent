# Repository Guidelines

## Structure and sources

`tools/agent_cli.py` runs the one-shot CLI; `tools/chat_cli.py` manages interactive history. Catalog retrieval lives in `tools/catalog.py`; model routing, tool calls, grounding, and offline answers have separate modules under `tools/`. `tools/order_status.py` verifies orders locally. `tools/qa_runner.py` executes `qa/scenarios.json` and writes Markdown/JSONL reports.

`Desafio Técnico AI Engineer 2026/data/` contains the supplied product CSV and policy PDF. `knowledge/policies/store.md` is generated from the PDF by `tools/policy_markdown.py`; `knowledge/INDEX.md` describes the available sources. Preserve the distinction between operational CSV facts and policy rules. Regenerate derived policy text rather than editing it by hand. `examples/fixtures/` contains fictional customer/order data; `examples/conversations.md` holds exactly five canonical CLI transcripts. `docs/` records requirements and design decisions.

## Development and verification

Run from the repository root. Python 3.10+ and `make` are required.

- `make setup` creates `.venv` and installs the project with `pypdf`.
- `make policies` rebuilds the policy Markdown using `pypdf`; it needs no `pdftotext`.
- `make test` runs `python -m unittest discover -s tests -v`.
- `make lint` runs Ruff lint, format, complexity, and file-length checks through `scripts/check_python.sh`.
- `make qa` runs conversational scenarios against the configured endpoint. Use `make qa OPENAI_BASE_URL=` to force offline mode even when `.env` is present; set `QA_OUT=/tmp/emporio-qa` to keep reports outside the repository.
- `make preflight`, `make demo`, `make chat`, `make ask Q="Quanto custa o Yamaha C40?"`, and `make order` exercise the CLI.
- `make help` lists targets. Override `VENV` to use an existing environment.
- `scripts/extract_requirements_source.sh` prints the challenge PDF and requires `pdftotext`.

Make loads optional `.env` settings; direct Python commands do not. Tests under `tests/` use unittest, synthetic data, fake HTTP model servers, and policy/PDF comparisons. For Python changes, run the unittests and `make lint`; for answer behavior changes, also run offline QA and configured-model QA when available. Keep model and offline results labeled accurately.

## Code and delivery

Use Python standard-library features where practical, four-space indentation, `snake_case`, and UTF-8. Keep scripts runnable with `python3`. Python files under `tools/` and `scripts/` must stay under 300 lines, with function cyclomatic complexity at most 10. Split distinct responsibilities rather than raising limits without cause.

Use concise imperative commit subjects when commits are requested. PRs should state the user-visible change, validation commands/results, and any source-data or generated-policy changes. Do not change source data to make checks pass.

## Privacy and credentials

Real customer/order CSVs contain personal information and stay local. Before exposing order details, verify the requester; use only fictional fixtures in examples and tests. Do not include real customer contact details in logs or replies. Never print `.env` contents or commit credentials.
