# Repository Guidelines

## Project Structure & Module Organization

`Desafio Técnico AI Engineer 2026/data/` holds the operational CSV files and store policy PDF. `docs/` contains project/domain documentation and the generated `knowledge-index.json`. `tools/project_knowledge.py` builds and queries the local project knowledge index; `tools/agent_cli.py` runs the customer-service CLI. `scripts/` contains source-document utilities and the Python quality checker. The project has no configured test suite.

## Build, Test, and Development Commands

Run commands from the repository root:

- `python3 tools/project_knowledge.py build` rebuilds the index from docs, CSVs, and policy PDF. It requires `pdftotext` on `PATH`.
- `python3 tools/project_knowledge.py query "Takamine GD20 price"` searches the index and prints evidence with source paths and row/chunk references. It builds the index if absent.
- `scripts/extract_requirements_source.sh` prints the technical challenge PDF as text; it also requires `pdftotext`.
- `python3 tools/agent_cli.py "Quanto custa o Takamine GD20?"` answers a customer message. Run it without a message for interactive mode.
- `sh scripts/check_python.sh` checks Python lint, formatting, function complexity, and file length under `tools/` and `scripts/`. It needs Ruff on `PATH` or `uvx` installed.

## Coding Style & Naming Conventions

Use Python 3 standard-library features where practical. Indent Python with four spaces, use `snake_case` for functions and variables, and keep scripts directly runnable with `python3`. Use UTF-8 for Markdown and source data. Preserve the distinction between operational CSV facts and policy PDF rules; document sources for derived knowledge. Keep generated indexes reproducible from their source files rather than editing them by hand. Run `sh scripts/check_python.sh` before handing off Python changes. Keep Python files under 300 lines and functions at or below cyclomatic complexity 10; adjust the file limit with `PYTHON_MAX_FILE_LINES` only when needed. These limits flag review risks but do not prove that a file has one clear responsibility. Split a file when unrelated changes repeatedly touch it or it owns distinct data sources and workflows.

## Testing Guidelines

There is no test framework or coverage requirement configured. For changes to the knowledge tool, rebuild the index and run representative queries for both CSV-backed facts and policy text. Add automated tests under `tests/` when the application or more complex logic is introduced; use descriptive names such as `test_policy_lookup.py`.

## Commit & Pull Request Guidelines

No project commit history is available to establish a commit convention. Use concise imperative commit subjects (for example, `Add source-cited knowledge lookup`). Pull requests should describe the user-visible change, list validation commands and results, and note any changes to source data or generated indexes. Include screenshots only for UI changes.

## Security & Data Handling

Customer CSVs contain personal information. Do not include customer contact details in examples, logs, or answers unless required and authorized by the application. Before exposing order details, implement requester verification. Never commit API keys or other credentials.
