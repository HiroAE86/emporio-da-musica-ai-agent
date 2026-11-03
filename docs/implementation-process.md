# Implementation process

## Status

Requirements discovery, scope selection, CLI implementation, and five canonical conversation examples are complete. The CLI supports product, policy, order-status, and out-of-scope messages. The repository is public at https://github.com/HiroAE86/emporio-da-musica-ai-agent. Email submission remains unverified.

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

The CLI is sufficient because the brief permits it and the focus is on the agent working correctly. Conversation history remains in memory and bounded to six recent messages. The optional model endpoint uses OpenAI-compatible Chat Completions tool calling; offline keyword routing remains the default when no endpoint is configured.

## 4. Implementation sequence

1. Reviewed the brief, operational CSV schemas, and policy PDF.
2. Added a reproducible PDF-to-Markdown policy wiki and an OpenAI-compatible tool loop for product, category, policy, and locally verified order lookup.
3. Added a local order-status check using an order ID, registered email, and registered phone, with fictional public fixtures.
4. Captured five canonical conversations by running the CLI offline, including a category switch, policy application, and complete fictional order verification. Additional model dialogues remain in the linked QA report.
5. Recorded the design reasons in `docs/architecture.md` and summarized them in the README.
6. Kept offline behavior as the default and added fake-server tests for tool fallback and privacy boundaries.

## 5. Acceptance checks

- Python is the primary language.
- The demo shows persona, context-grounded answers, correct source choice, and out-of-scope handling.
- Product facts come from operational CSV data; policy rules come from the store manual.
- Unknown or unsupported facts are identified as unknown rather than guessed.
- Customer contact data is not included in answers; order status is returned only after local verification.
- The README and five varied offline conversation examples are present and reproducible.
- The public repository link must be submitted by the deadline; no sent-email receipt is recorded here.

## 6. Current gaps

The CLI supports product and policy answers, local order-status verification, and out-of-scope redirection. The public order-status example uses fictional data. Real customer and order CSVs remain local and are excluded from Git.

The requirements fix validates category product-price pairs against current filtered evidence, including actual tool results, and corrects the offline installment tiers. Fake-server regressions cover swapped prices, budget violations, and narrower tool results. Current verification passes 41 unittests, lint, and offline QA (15/15 scenarios, 46/46 checks). Historical model QA reports describe their original revisions; the requirements-fix report records the new configured-model runs, including an intermittent return-policy wording failure. Offline freight and warranty answers still defer to the source or store team.
