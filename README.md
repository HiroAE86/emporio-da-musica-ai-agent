# Empório da Música customer service agent

A Python CLI prototype for customer questions about products, store policies, and order status. Customer-facing replies are in Brazilian Portuguese. With no model endpoint configured, the existing keyword router and local templates answer offline.

## Quick start

Python 3.10+ and `make` are required. From the repository root:

```sh
make setup
make policies   # regenerate the policy wiki from the source PDF
make test
make demo
make chat
make help
```

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

Tool calling is enabled by default for configured endpoints. Set `AGENT_TOOLS=0` to force the legacy evidence-in-prompt model call. If the server rejects `tools`, the CLI retries through that legacy path; if the model call fails, it uses the local answer. GPT-4o mini is a hosted option with tool calling. For local use, Qwen 2.5 7B or larger models in LM Studio are reasonable candidates when their served template supports tools. Small models such as `lfm3-omni-2b` may not call tools reliably. Model capability depends on the provider and endpoint configuration.

## Design choices

- **Agent shape:** a short OpenAI Chat Completions tool loop, limited to four tool rounds. It uses the standard library `urllib`, with no agent framework, embeddings, or vector database. The model chooses a local function; Python reads the source and returns its result for the model to explain.
- **Knowledge wiki:** `make policies` uses `pypdf` to reproducibly extract the supplied policy PDF into numbered Markdown sections at `knowledge/policies/store.md`. `knowledge/INDEX.md` lists the available policy topics, catalog categories, and order source; it is included in the system prompt. The PDF remains the source of truth.
- **Tools:** `search_products(query)` and `list_category(category, max_price?, beginner?)` read the operational products CSV; `read_policy(section)` reads one Markdown section; `check_order_status()` starts the existing local verification flow. Tool JSON is validated before source access. Unknown tools and malformed arguments produce safe tool results.
- **Privacy:** order number, email, and phone are collected and checked locally. The model sees only verified status and estimated delivery. Email addresses and phone-like values are redacted from user messages and chat history before model requests. Customer and order CSV rows are never sent to the model.
- **Fallback and UI:** no endpoint means unchanged offline keyword routing. Unsupported tool endpoints fall back to the existing evidence-in-prompt model path, then local templates on failure. The interface is a one-shot or interactive CLI. History stays in memory and is bounded to six recent messages.
- **Source handling:** product facts come from the products CSV; policy facts come from the PDF-derived Markdown. Order and stock data are static snapshots. The supplied case brief leaves the framework, provider, model, UI, and persistence choices open; this prototype keeps the implementation small and documents those choices here.

## Tests and examples

```sh
python -m unittest discover -s tests -v
PATH=/tmp/emporio-venv/bin:$PATH sh scripts/check_python.sh
```

The offline tests use synthetic data and a local fake OpenAI-compatible server. They cover tool dispatch, multiple rounds, bad and unknown calls, unsupported-tool fallback, PII redaction, legacy behavior, and policy facts checked against the PDF. Five offline conversations are in [examples/conversations.md](examples/conversations.md).

## Limitations

Product matching and category inference are lexical; categories are inferred from names and descriptions because the current product lookup does not depend on category labels. There is no live inventory, promotion feed, or order integration. Model answers are not checked against retrieved source text, and provider-specific tool support can vary. Email and phone checks are a demo safeguard, not production identity verification. Policy text is faithfully extracted but may need manual cleanup if the PDF layout changes; the PDF comparison test guards selected facts, not every sentence.

## AI tools

OpenAI Codex assisted with challenge analysis, implementation, review, and documentation. Offline tests and source comparisons were used to check behavior. A model endpoint is optional at runtime.
