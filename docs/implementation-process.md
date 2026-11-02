# Implementation process

## Status

Requirements discovery, scope selection, and the first CLI implementation are complete. The CLI supports product, policy, and out-of-scope messages. Conversation examples and runtime verification remain. This document records the work done and the remaining route to a submission.

## 1. Read the challenge brief

The original brief is `Desafio Técnico AI Engineer 2026/desafio_tecnico_ai_eng_artefact.pdf`. Its required outcome is a Python messaging agent for the fictional Empório da Música that:

- Uses a persona and tone appropriate to the store.
- Answers from the supplied context.
- Chooses operational data for facts such as price and availability, and store policies for rules such as returns and payment.
- Handles questions outside the store's scope appropriately.

The challenge allows any interface and model/provider. It asks for a public GitHub repository with meaningful commits, a README with setup and technical decisions, three to five example conversations, and submission of the repository link by the recruiting email deadline. If information is ambiguous or missing, document a reasonable assumption.

The source summary is in `docs/requirements.md`.

## 2. Inspect existing project materials

The repository contains the challenge brief and source data, domain notes under `docs/`, and `tools/project_knowledge.py`. That tool builds a local index over Markdown, CSV rows, and extracted store-policy PDF text, then performs lexical search and prints source references.

The index is a useful starting point, but it does not generate responses, enforce access control, or guarantee that the most relevant result is returned. The repository documentation also states that customer/order data is sensitive and requester verification is needed before exposing order details.

The policy PDF and source CSVs remain the source of truth. Do not invent store facts or policy rules where those sources are silent.

## 3. Choose the smallest useful scope

The first version is a Python CLI with one model provider and direct retrieval from the approved source files. It does not use the existing all-source index, so customer and order rows stay out of model context. Keep the customer-facing demonstration to three cases:

1. A product price or availability question answered from operational data.
2. A store rule question answered from the policy manual.
3. An out-of-scope question answered with a polite redirection.

Do not include order-status responses in the first version. Order lookups require requester verification and careful handling of personal information. Omitting that optional data path keeps the prototype smaller and avoids exposing customer data without authentication.

The CLI is sufficient because the brief permits it and the focus is on the agent working correctly. Conversation-history persistence is not needed for these one-turn examples. Use a hosted model API to avoid packaging and running a local model; document provider setup and any required API key as an environment variable, never commit credentials.

## 4. Implementation sequence

1. Reviewed the brief, CSV schemas, and policy PDF.
2. Implemented `tools/agent_cli.py` with direct product and policy retrieval, an OpenAI-compatible Chat Completions call, and local replies for selected demo paths.
3. Updated the README and architecture notes with setup and implementation decisions.
4. Add three to five example conversations and verify their facts against source rows and policy sections.
5. Commit coherent increments, publish a public GitHub repository, and submit its link by replying to the recruiting email before the stated deadline.

## 5. Acceptance checks

- Python is the primary language.
- The demo shows persona, context-grounded answers, correct source choice, and out-of-scope handling.
- Product facts come from operational CSV data; policy rules come from the store manual.
- Unknown or unsupported facts are identified as unknown rather than guessed.
- Customer/order details are not exposed in the initial demo.
- The README and three varied conversation examples are present and reproducible.
- The public repository is submitted by the deadline.

## 6. Current gaps

The CLI and setup documentation exist, but no conversation examples have been added. The local model path was exercised using `lfm3-omni-2b` through the OpenAI-compatible endpoint. The CLI has local replies for product lookup, online-return policy, and out-of-scope messages. The current project knowledge index is lexical and remains separate from the CLI.
