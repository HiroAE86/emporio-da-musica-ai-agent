# Canonical conversations

Exactly five conversations, captured by running the CLI offline on 2026-11-03 with `OPENAI_BASE_URL` unset. No model was used. Customer replies and source lines below are CLI output, with terminal line endings and trailing spaces normalized. Additional historical model dialogues are in the [Nemotron QA report](../qa/reports/nemotron-2026-11-03.md).

## Product recommendation with a budget

**Mode:** offline (local answer).

**Customer:** Quero um violão para iniciante até R$ 500

```text
Oi! Encontrei estas opções no catálogo:
Categoria: violões
Limite de preço desta consulta: R$ 500,00.
Correspondências até R$ 500,00: 2
Tagima Memphis AC-39 Nylon Natural — R$ 429,90 — disponível — Violão clássico com cordas de nylon, perfeito para quem está começando
Rozini RC-104 Nylon Estudante — R$ 459,90 — disponível — Violão clássico de estudo da Rozini, feito com madeiras nacionais
Fonte: Desafio Técnico AI Engineer 2026/data/desafio_tecnico_ai_eng - products.csv
```

## Switching categories without carrying the budget

**Mode:** offline (local answers), one interactive CLI session. Inputs: `Quais violões até R$ 500?`, `e guitarra?`, `sair`. Piped input is not echoed by the terminal.

```text
Empório da Música, modo local (sem modelo configurado). Digite 'sair' para encerrar.
Você: Loja: Oi! Encontrei estas opções no catálogo:
Categoria: violões
Limite de preço desta consulta: R$ 500,00.
Correspondências até R$ 500,00: 2
Tagima Memphis AC-39 Nylon Natural — R$ 429,90 — disponível
Rozini RC-104 Nylon Estudante — R$ 459,90 — disponível
Fonte: Desafio Técnico AI Engineer 2026/data/desafio_tecnico_ai_eng - products.csv
Você: Loja: Oi! Encontrei estas opções no catálogo:
Categoria: guitarras
Limite de preço desta consulta: nenhum; limites anteriores não são herdados.
Fender Stratocaster American Pro II — R$ 12.500,00 — disponível
Gibson Les Paul Standard '50s — R$ 18.900,00 — disponível
Ibanez RG550 Genesis Collection — R$ 7.500,00 — disponível
PRS SE Custom 24 — R$ 6.800,00 — disponível
Fender Telecaster Player Series — R$ 5.400,00 — disponível
Fonte: Desafio Técnico AI Engineer 2026/data/desafio_tecnico_ai_eng - products.csv
Você:
```

## Online purchase regret return

**Mode:** offline (local answer).

**Customer:** Comprei online há cinco dias e me arrependi. Posso devolver?

```text
Oi! Para compras online, você pode pedir a devolução em até 7 dias corridos após receber o produto, sem justificar. Ele precisa estar sem uso, na embalagem original e com acessórios e manuais. A loja paga o frete de devolução, e o reembolso ocorre pela forma de pagamento original em até 10 dias úteis.
Fonte: Desafio Técnico AI Engineer 2026/data/políticas_da_loja.pdf
```

## Verified order status

**Mode:** offline, with `ORDER_DATA_DIR=examples/fixtures`.

**Customer:** Qual o status do pedido?

Verification inputs, in prompt order, were the fictional fixture values:

1. Order number: `TESTE-100`.
2. Registered email: `cliente@example.test`.
3. Registered phone: `67999990000`.

The email and phone inputs are hidden by `getpass`; the terminal transcript preserves that behavior.

```text
Número do pedido: TESTE-100
E-mail cadastrado:
Telefone cadastrado:
Status do pedido: enviado. Previsão de entrega: 2026-11-05. Fonte: orders.csv.
```

## Out of scope

**Mode:** offline (local answer).

**Customer:** Qual é a capital da França?

```text
Não consigo ajudar com perguntas de conhecimento geral. Posso ajudar com instrumentos musicais, preços, disponibilidade, políticas da loja ou status de pedidos.
```
