# Challenge requirements

Source: [`Desafio Técnico AI Engineer 2026/desafio_tecnico_ai_eng_artefact.pdf`](../Desafio%20T%C3%A9cnico%20AI%20Engineer%202026/desafio_tecnico_ai_eng_artefact.pdf), extracted with `pypdf` on 2026-11-03. The original brief asks for a Python text-message customer-service agent for the fictional Empório da Música in Campo Grande/MS. All technical choices below are open unless the brief says otherwise.

## Required behavior

- Use a persona and tone aligned with the store.
- Receive messages and answer using the supplied context.
- Choose when to consult operational data (examples: product availability, price, order status) and when to consult policy (examples: exchanges, hours, payment methods).
- Handle questions outside the store's scope appropriately.

## Technical decisions to document in README

- Agent framework or approach (examples: RAG, function calling, ReAct, SQL agent, hybrid).
- Model and provider; paid, free, local, and API models are allowed.
- User interface (examples: CLI, notebook, API, simple UI).
- Whether conversation history persists.
- Data handling.
- Python is the only mandatory technical constraint. For ambiguity or unavailable information, make a reasonable assumption and document it.

## Deliverables from the brief

1. A public GitHub repository containing the project, with meaningful progress in commit history. Do not collapse all work into one force-pushed commit or change the repository after the stated deadline.
2. A README with setup and model-provider instructions, run commands, technical rationale (including retrieval and prompt strategy), known limitations and improvements possible with more time, and an account of coding assistants used and how.
3. Three to five varied agent conversations in Markdown, text, or image format. At least one must show a non-trivial data lookup or policy application. Suggested questions include available guitars under R$1,000, store address, Takamine GD20 price, and the online regret-return policy.
4. Reply to the recruiting email with the public repository link before the deadline stated in that email.

The recruiter additionally asks for an English README covering setup, technical decisions, limitations, and AI-tool use; three to five conversations, including one non-trivial example; and real commit history. These requirements overlap with the brief and are tracked in the Portuguese handoff summary.
