# Empório da Música customer service agent

A Python CLI prototype for customer questions about products, store policies, and order status. Customer-facing replies are in Brazilian Portuguese. With no model endpoint configured, the existing keyword router and local templates answer offline.

## Quick start

Python 3.10+ and `make` are required. `make setup` creates `.venv` and installs the project, including `pypdf`. From the repository root:

```sh
make setup
make policies   # regenerate the policy wiki from the source PDF
make test
make demo
make chat
make help
```

To run the direct `python` commands below after setup, activate the environment with `. .venv/bin/activate`.

`make policies` uses the supplied policy PDF to regenerate `knowledge/policies/store.md`; it does not require `pdftotext`. `make test` runs the unittest suite. `make lint` installs Ruff in the project environment and runs the Python quality checker. `make preflight` checks the data files and configured model endpoint. `make qa` runs the scenario suite against the configured endpoint, or offline when `OPENAI_BASE_URL` is unset.

`make ask Q="Quanto custa o Yamaha C40?"` asks one question. `make order` runs the local order flow with fictional fixture data. Install dependencies manually with `python3 -m venv .venv && . .venv/bin/activate && python -m pip install -e .`.

## Run

```sh
python tools/agent_cli.py "Quanto custa o Takamine GD20?"
python tools/agent_cli.py "Quais violões vocês têm até R$ 1.000?"
python tools/agent_cli.py "Qual é o endereço da loja?"
python tools/agent_cli.py "Comprei online há cinco dias e me arrependi. Posso devolver?"
python tools/agent_cli.py "Qual é a capital da França?"
ORDER_DATA_DIR=examples/fixtures python tools/agent_cli.py "Qual é o status do meu pedido?"
python tools/agent_cli.py --preflight
```

Order verification asks locally for the order number, registered email, and registered phone. The fictional fixture order uses `TESTE-100`, `cliente@example.test`, and `67999990000`.

## Model setup

Without `OPENAI_BASE_URL`, the CLI uses local answers and never contacts a model. To enable an OpenAI-compatible Chat Completions endpoint, configure `OPENAI_BASE_URL`, `OPENAI_MODEL`, and (when required) `OPENAI_API_KEY`. The CLI does not load `.env` itself; Make loads the optional `.env` file.

```sh
cp .env.example .env
# Set OPENAI_BASE_URL, OPENAI_MODEL, and optionally OPENAI_API_KEY.
make ask Q="Como funciona a garantia?"
```

Tool calling is enabled by default for configured endpoints. Set `AGENT_TOOLS=0` to force the legacy evidence-in-prompt model call. If the server rejects `tools`, the CLI retries through that legacy path; if the model call fails, it uses the local answer.

The model tested for this project was **`lfm3-omni-2b` served by LM Studio** through its OpenAI-compatible endpoint. Inference runs locally, has no per-token API charge, and does not send data to a hosted model provider. In the QA setup, the CLI reached the LM Studio host over the network. The QA run on **2026-11-03** passed **15/15 scenarios and 45/45 checks** in tools mode. This result shows that deterministic retrieval and code-side filtering can keep the flow useful with a 2B model; it does not mean every small model will call tools consistently. For a hosted alternative, `gpt-4o-mini` is a reasonable option; for local use, try Qwen 2.5 7B or larger with a tool-capable LM Studio template. Hosted models add usage cost and send request content to the provider; local models avoid that transfer but need local compute and may add latency. Tool-call reliability varies by model, quantization, serving template, and endpoint.

## Design choices

- **Agent shape:** a short OpenAI Chat Completions tool loop, limited to four tool rounds. It uses the standard library `urllib`, with no agent framework, embeddings, or vector database. The model chooses a local function; Python reads the source and returns its result for the model to explain.
- **Knowledge wiki:** `make policies` uses `pypdf` to reproducibly extract the supplied policy PDF into numbered Markdown sections at `knowledge/policies/store.md`. `knowledge/INDEX.md` lists the available policy topics, catalog categories, and order source; it is included in the system prompt. The PDF remains the source of truth.
- **Tools:** `search_products(query)` and `list_category(category, max_price?, beginner?)` read the operational products CSV; `read_policy(section)` reads one Markdown section; `check_order_status()` starts the existing local verification flow. Tool JSON is validated before source access. Unknown tools and malformed arguments produce safe tool results.
- **Catalog replies:** category and budget questions are filtered and sorted in Python, then rendered locally from the matching rows. This keeps weak models from changing category names, including over-budget products as matches, or inventing prices. Each lookup states its category, match count, and price-limit rule. A new category starts a fresh lookup; price limits are not inherited from the previous turn. For product answers that do use a model, any currency amount that differs from the CSV price falls back to the local answer.
- **Privacy:** order number, email, and phone are collected and checked locally. The model sees only verified status and estimated delivery. Email addresses and phone-like values are redacted from user messages and chat history before model requests. Customer and order CSV rows are never sent to the model.
- **Fallback and UI:** no endpoint means unchanged offline keyword routing. Unsupported tool endpoints fall back to the existing evidence-in-prompt model path, then local templates on failure. The interface is a one-shot or interactive CLI. History stays in memory and is bounded to six recent messages.
- **Source handling:** product facts come from the products CSV; policy facts come from the PDF-derived Markdown. Order and stock data are static snapshots. The supplied case brief leaves the framework, provider, model, UI, and persistence choices open; this prototype keeps the implementation small and documents those choices here.

## Tests and examples

```sh
python -m unittest discover -s tests -v
PATH=/tmp/emporio-venv/bin:$PATH sh scripts/check_python.sh
```

## QA

Run the conversational QA scenarios against the configured local model, or offline when `OPENAI_BASE_URL` is unset:

```sh
make qa
QA_SCENARIO=order make qa
QA_OUT=/tmp/emporio-qa make qa
```

Each run starts fresh conversations, preserves history between turns, and writes a Markdown transcript plus JSONL records under `qa/results/`. The command exits nonzero when a check fails. Reports are local and ignored by Git.

The offline tests use synthetic data and a local fake OpenAI-compatible server. They cover tool dispatch, multiple rounds, bad and unknown calls, unsupported-tool fallback, PII redaction, legacy behavior, and policy facts checked against the PDF. Five offline conversations are in [examples/conversations.md](examples/conversations.md).

## Limitations

Product matching and category inference are lexical; categories are inferred from names and descriptions because the current product lookup does not depend on category labels. There is no live inventory, promotion feed, or order integration. The price check covers currency amounts in product answers; provider-specific tool support can vary. Email and phone checks are a demo safeguard, not production identity verification. Policy text is faithfully extracted but may need manual cleanup if the PDF layout changes; the PDF comparison test guards selected facts, not every sentence.

## AI tools and development workflow

Codex CLI on a VPS implemented the project with the P-Stack skills: poteto-mode, interrogate/adversarial review, blast-radius, applicable `principle-*` skills, and unslop. Work proceeded in scoped rounds. A human set direction and reviewed each round; each round had a focused prompt, and tests, Ruff, and the 300-line file limit had to pass before its commit. Adversarial edge-case probing exposed phrasing bugs. Testing the real `lfm3-omni-2b` model through LM Studio exposed invented prices, category mix-ups, and budget carry-over; those failures led to deterministic pre-retrieval, code-side budget filtering, and a price grounding check. The QA harness gave the final 15/15 scenario and 45/45 check result.

AI proposed and implemented changes; a human chose scope and reviewed them. Source-derived behavior was checked against the supplied CSVs and policy PDF, and the test suite and QA checks were run locally. The model did not determine the project requirements or the acceptance result.
