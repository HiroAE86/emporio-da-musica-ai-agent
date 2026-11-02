# Domain: architecture and operation

## Constraints

Python is the primary language. The prototype is a one-file CLI in `tools/agent_cli.py` and uses only the Python standard library plus the system `pdftotext` command.

## Decisions

| Topic | Decision | Reason |
|---|---|---|
| Agent approach | Keyword routing, direct retrieval, and a single model call | Smallest path that demonstrates selecting the right source and grounding an answer |
| Model and provider | OpenAI-compatible Chat Completions; default `lfm3-omni-2b` at the local server URL, configurable with `OPENAI_BASE_URL` and `OPENAI_MODEL` | Tests against a local model without adding a Python SDK dependency |
| Interface | CLI, one message or interactive session | The brief permits CLI and it is easy to reproduce |
| History | No persistence | The initial demo is one-turn and has no history requirement |
| Data handling | Read product and policy sources; verify order ID and email locally; never send customer/order rows to the model | Limits order disclosure and keeps contact data out of model context |
| Order lookup boundary | Keep local CSV matching in `tools/order_status.py`; keep message routing and model calls in `tools/agent_cli.py` | Isolates customer-data handling and keeps the CLI below its 300-line limit |

## Execution

Run `python3 tools/agent_cli.py "customer message"`. The default model server is `http://100.111.77.36:1234/v1`; set `OPENAI_BASE_URL` and `OPENAI_MODEL` to use another OpenAI-compatible server or model. Set `OPENAI_API_KEY` only if the server requires a key. Local templates handle product lookups, online returns, and out-of-scope messages when the API is unavailable. Policy extraction requires `pdftotext` on `PATH`.

## Limits

Product matching uses keyword overlap and is intended for the supplied case. Inventory comes from the static CSV snapshot. Order lookup checks the order ID and registered email locally, then returns status and estimated delivery. This is a basic demo safeguard, not production identity verification. The local response templates cover only the demo paths.
