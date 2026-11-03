# Empório da Música customer service agent

A Python CLI prototype for product questions, store policies, order status, and unrelated requests. Customer-facing replies use Brazilian Portuguese. Product and regret-return answers have local templates, so the CLI works without a model service.

## Setup

Requires Python 3.10 or newer. From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

The project installs `pypdf` to extract the supplied store policy PDF. The original case brief is included at `Desafio Técnico AI Engineer 2026/desafio_tecnico_ai_eng_artefact.pdf`.

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

Order lookup prompts for the order number, registered email, and registered phone. The fixture order uses `TESTE-100`, `cliente@example.test`, and `67999990000`.

By default, `OPENAI_BASE_URL` is unset and local templates answer supported questions. To enable model-assisted policy and product answers, configure an OpenAI-compatible Chat Completions endpoint and model:

```sh
cp .env.example .env
# Edit .env, then load it into the shell:
set -a
. ./.env
set +a
```

Set `OPENAI_BASE_URL` (for example `http://localhost:1234/v1`), `OPENAI_MODEL`, and `OPENAI_API_KEY` only if the endpoint requires a key. The CLI does not load `.env` itself. `--preflight` checks the catalog and policy files; if configured, it also checks the endpoint's `/models` route. An unavailable model falls back to local answers. Address, hours, payment methods, exchanges, and regret-return questions are answered locally from the policy PDF. Unknown policy facts get a message to contact the store.

## Technical decisions

- **Approach:** deterministic keyword routing and direct CSV/PDF retrieval, with an optional single model call. No framework, embeddings, or vector database are needed for these fixed sources. Product matching is lexical; policy retrieval extracts the manual and sends its first 18,000 characters.
- **Model and prompt:** any configured OpenAI-compatible chat model can be used. The prompt requests a cordial Brazilian Portuguese tone, source-grounded answers, complete return conditions, and no personal-data disclosure. These instructions are not enforced by an output validator. Local templates provide predictable product, category/budget, policy, regret-return, and out-of-scope replies when no endpoint is configured or reachable.
- **Interface and history:** one-shot and interactive CLI; no persistent conversation history because the case does not require it.
- **Data:** product facts come from the products CSV; policy text comes from the store PDF. Order/customer rows stay local. The order lookup requires the order number, email, and phone, then returns only status and estimated delivery. It uses one generic reply for mismatches and unknown orders. The included order fixtures are fictional. Product and policy questions are sent as typed to a configured model endpoint with retrieved evidence; do not include personal details in those messages.
- **Scope decisions:** this prototype does not implement category/budget filtering, promotions, address lookup, or general policy clause matching in its local fallback. It does not demonstrate live inventory or real-time order integration.

## Tests and examples

Run the offline behavior suite:

```sh
python -m unittest discover -s tests -v
```

Tests use synthetic catalog, customer, and order data and do not call a model endpoint. Four verified transcripts are in [examples/conversations.md](examples/conversations.md).

## Limitations

Product matching depends on words in product names; category filtering matches category words in names and descriptions because the CSV has no category labels. Policy routing depends on keywords, and local replies use facts present in the supplied PDF. Model output can omit or misstate evidence because it is not validated. Stock and order status are static CSV snapshots. Email and phone checks are a basic demo safeguard, not production identity verification. The CLI does not redact personal details included in product or policy questions sent to a configured endpoint.

With more time, I would add response validation, a stronger identity flow, and explicit category labels in the catalog.

## AI tools

OpenAI Codex assisted with challenge analysis, implementation, code review, and documentation. I checked the resulting behavior against the supplied files and added offline tests; the model is optional at runtime.
