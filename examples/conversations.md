# Verified CLI conversations

These transcripts were run on 2026-11-03 with `OPENAI_BASE_URL` unset, so answers use the local fallback and require no model endpoint. Product and policy responses cite the supplied source. Order data is fictional.

## Product price and availability

**Customer:** Quanto custa o Takamine GD20?

**Empório da Música:** Oi! Takamine GD20 Dreadnought Natural está cadastrado por R$ 2.199,00 e aparece como disponível no arquivo, com 5 unidade(s). A informação vem do catálogo fornecido, não de estoque ao vivo.

**Source:** `Desafio Técnico AI Engineer 2026/data/desafio_tecnico_ai_eng - products.csv`

## Applying the online regret-return policy

**Customer:** Comprei online há cinco dias e me arrependi. Posso devolver?

**Empório da Música:** Oi! Para compras online, você pode pedir a devolução em até 7 dias corridos após receber o produto, sem justificar. Ele precisa estar sem uso, na embalagem original e com acessórios e manuais. A loja paga o frete de devolução, e o reembolso ocorre pela forma de pagamento original em até 10 dias úteis.

**Source:** `Desafio Técnico AI Engineer 2026/data/políticas_da_loja.pdf`

## Order verification

**Customer:** Qual é o status do meu pedido?

**CLI:** Número do pedido:

**Customer:** TESTE-100

**CLI:** E-mail cadastrado:

**Customer:** cliente@example.test

**CLI:** Telefone cadastrado:

**Customer:** 67999990000

**Empório da Música:** Status do pedido: shipped. Previsão de entrega: 2026-11-05. Fonte: orders.csv.

**Source:** `examples/fixtures/orders.csv` and `examples/fixtures/customers.csv` (fictional data)

## Out of scope

**Customer:** Qual é a capital da França?

**Empório da Música:** Oi! Posso ajudar com instrumentos musicais, preços e disponibilidade do catálogo, além das políticas da loja.
