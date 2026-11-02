# Technical decisions

## Scope

The project is a Python 3.10 command-line agent. It uses the standard library and `pdftotext`; it does not run a web server or require a Python package install. The challenge requires Python and permits a CLI, so this shape avoids framework and deployment work that the demonstration does not need. See [`requirements.md`](requirements.md) and the [run instructions in the README](../README.md#run).

## Decisions and rationale

| Area | Decision and reason | Evidence |
|---|---|---|
| Agent approach | Use keyword routing, direct source lookup, and one model call. Do not use an agent framework, embeddings, or a vector database. This is a scope choice for the fixed demo sources; no comparative retrieval benchmark was run. | [`agent_cli.py`](../tools/agent_cli.py), [`requirements.md`](requirements.md) |
| Routing order | Detect order-status requests first. For other messages, policy keywords take precedence over product matching. Product keywords with no row return a no-match result; messages matching neither policy nor product routes get a local scope reply. | [`agent_cli.py`](../tools/agent_cli.py), [`order_status.py`](../tools/order_status.py) |
| Product retrieval | Normalize accents and case, score product names by overlapping query words, and return the unique highest-scoring row. A tie gives the model a clarification instruction; the local fallback returns that instruction in English. This is lexical matching, not semantic search. | [`agent_cli.py`](../tools/agent_cli.py), [`catalog.md`](catalog.md) |
| Policy retrieval | Route policy keywords to `pdftotext`, then pass up to 18,000 extracted characters with the customer question and source path. This avoids maintaining a separate policy index for the supplied manual. | [`agent_cli.py`](../tools/agent_cli.py), [`store-policies.md`](store-policies.md) |
| Model and provider | Use `lfm3-omni-2b` at the supplied OpenAI-compatible local endpoint through Chat Completions. Use Python's `urllib` instead of an SDK so the prototype has no Python API dependency. `OPENAI_BASE_URL`, `OPENAI_MODEL`, and `OPENAI_API_KEY` can override the defaults. | [`.env.example`](../.env.example), [`agent_cli.py`](../tools/agent_cli.py) |
| Environment configuration | Read configuration from exported environment variables; load `.env` in the shell instead of adding a dotenv package. | [README environment setup](../README.md#run), [`agent_cli.py`](../tools/agent_cli.py) |
| Interface | Support one-shot messages and an interactive CLI. The brief permits a CLI, and it lets a reviewer reproduce the examples without a frontend or server. | [`agent_cli.py`](../tools/agent_cli.py), [README run commands](../README.md#run) |
| Conversation history | Do not persist messages. The examples are one-turn demonstrations, and the brief does not require multi-turn memory. This also avoids storing conversation history. | [`agent_cli.py`](../tools/agent_cli.py), [`requirements.md`](requirements.md) |
| Prompt | Instruct the model to use Brazilian Portuguese and a cordial, informal, professional tone; use supplied evidence; state when facts are missing; include all listed return conditions; treat stock as a snapshot; and avoid personal-data disclosure. These are prompt instructions, not enforced output checks. | [`agent_cli.py`](../tools/agent_cli.py), [`conversations.md`](../examples/conversations.md) |
| Data selection | Use the products CSV for name, price, stock, status, and description; use the policy PDF for store rules. Categories and promotions are not queried in this version because the demonstration focuses on product lookup, policy answers, and order status. | [`agent_cli.py`](../tools/agent_cli.py), [`catalog.md`](catalog.md) |
| Order status | Keep the order lookup in `order_status.py`. Match the order ID to `customer_id`, then check the registered email locally. Return only status and estimated delivery. Use the same response for an unknown order and an email mismatch so the CLI does not confirm either value. | [`order_status.py`](../tools/order_status.py), [`orders.md`](orders.md) |
| Order data | Use real order and customer CSVs only when they are available locally. The public demo falls back to fictional rows in `examples/fixtures/`. The email is read with hidden terminal input; neither it nor the CSV rows reach the model. The email check is a demonstration safeguard, not production authentication. | [`.gitignore`](../.gitignore), [`order_status.py`](../tools/order_status.py), [`orders.md`](orders.md) |
| Local knowledge index | Keep `project_knowledge.py` and its generated index out of the public repository. The agent CLI does not use them, and the indexer reads every CSV, including customer and order records. | [`.gitignore`](../.gitignore), [`agent_cli.py`](../tools/agent_cli.py) |
| API failure | Use local templates for product answers, online-return answers, and out-of-scope requests when the model call fails. Other policy questions need the model to summarize the retrieved text; without it, the CLI asks the customer to contact the store. | [`agent_cli.py`](../tools/agent_cli.py) |
| Quality checks | Enforce a 300-line file limit and Ruff lint, formatting, import-order, and complexity checks. These limits are review triggers, not measures of responsibility. The order lookup lives separately because it handles local customer data and took the CLI over the limit. | [`pyproject.toml`](../pyproject.toml), [`check_python.sh`](../scripts/check_python.sh), [`order_status.py`](../tools/order_status.py) |

## Data and trust boundaries

For matched product and policy questions, the model request contains the full customer question plus selected fields from one product row and its CSV row reference, or the extracted policy text. Out-of-scope messages use a local reply. The separate order-status path asks for an order ID and hidden email before it reads the files. It returns no email, phone, address, order items, or tracking code. The order/customer CSV rows and entered verification email do not reach the model. The CLI does not redact personal data from matched product or policy questions, so those messages can reach the configured model endpoint as typed. Real customer and order CSVs are ignored by Git. The public fixture uses the reserved `.test` email domain.

The prompt asks the model not to invent facts or disclose personal data, but the CLI does not validate every model response. The email check only demonstrates a basic requester check. It is not suitable for production access control.

## Verification

The order path was run with `ORDER_DATA_DIR=examples/fixtures` using `TESTE-100` and `cliente@example.test`. It returned `Status do pedido: shipped. Previsão de entrega: 2026-11-05. Fonte: orders.csv.` An incorrect email returned `Não encontrei um pedido com esses dados. Confira e tente novamente.`, the same message used for an unknown order. The saved conversation is in [`examples/conversations.md`](../examples/conversations.md).

`sh scripts/check_python.sh` returned `All checks passed! 2 files already formatted`. `git diff --check` returned no output. These checks do not replace an automated behavior test suite; none is configured.

## Known limits

- Product lookup is lexical. It does not support reliable budget filters, category browsing, or promotion lookup.
- A product-name tie asks the model to clarify; if the model is unavailable, the fallback message is English.
- Policy routing depends on keywords and sends the first 18,000 extracted characters, not a semantically ranked section.
- Matched product and policy questions reach the model as typed, and prompt restrictions are not technically enforced.
- Stock and order status come from static CSV snapshots, not live systems.
- The registered-email check is not production authentication.
- The default model endpoint is specific to the development machine. Set the environment variables for another server.
