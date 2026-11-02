# Implementation process

## Status

Requirements discovery, scope selection, CLI implementation, and four conversation examples are complete. The CLI supports product, policy, order-status, and out-of-scope messages. GitHub publication and email submission remain.

## 1. Read the challenge brief

The original brief is `Desafio Técnico AI Engineer 2026/desafio_tecnico_ai_eng_artefact.pdf`. Its required outcome is a Python messaging agent for the fictional Empório da Música that:

- Uses a persona and tone appropriate to the store.
- Answers from the supplied context.
- Chooses operational data for facts such as price and availability, and store policies for rules such as returns and payment.
- Handles questions outside the store's scope appropriately.

The challenge allows any interface and model/provider. It asks for a public GitHub repository with meaningful commits, a README with setup and technical decisions, three to five example conversations, and submission of the repository link by the recruiting email deadline. If information is ambiguous or missing, document a reasonable assumption.

The source summary is in `docs/requirements.md`.

## 2. Inspect existing project materials

The CLI retrieves product and policy evidence directly. Order status uses a local customer/order join and never sends contact or order records to the model. The public demo uses fictional order data.

The policy PDF and source CSVs remain the source of truth. Do not invent store facts or policy rules where those sources are silent.

## 3. Choose the smallest useful scope

The Python CLI uses direct retrieval and one model provider. Product and policy answers receive only the selected evidence. Order status is verified locally against fictional public fixture data or private local CSVs. The response includes status and estimated delivery only.

The CLI is sufficient because the brief permits it and the focus is on the agent working correctly. Conversation-history persistence is not needed for these one-turn examples. The model uses an OpenAI-compatible local endpoint configured through environment variables.

## 4. Implementation sequence

1. Reviewed the brief, operational CSV schemas, and policy PDF.
2. Implemented direct product and policy retrieval with a local model call and local fallback replies.
3. Added a local order-status check using an order ID and registered email, with fictional public fixtures.
4. Saved four conversations and checked their facts against the product CSV, fixture CSVs, and policy section 4.1.
5. Recorded the design reasons in `docs/architecture.md` and summarized them in the README.
6. Committed focused changes. GitHub publication and email submission remain.

## 5. Acceptance checks

- Python is the primary language.
- The demo shows persona, context-grounded answers, correct source choice, and out-of-scope handling.
- Product facts come from operational CSV data; policy rules come from the store manual.
- Unknown or unsupported facts are identified as unknown rather than guessed.
- Customer contact data is not included in answers; order status is returned only after local verification.
- The README and four varied conversation examples are present and reproducible.
- The public repository is submitted by the deadline.

## 6. Current gaps

The CLI supports product and policy answers, local order-status verification, and out-of-scope redirection. The public order-status example uses fictional data. Real customer and order CSVs remain local and are excluded from Git.
