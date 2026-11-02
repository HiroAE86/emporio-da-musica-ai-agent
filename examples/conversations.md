# Example conversations

These examples were run with `python3 tools/agent_cli.py` against the configured OpenAI-compatible local model. The order-status example uses fictional data from `examples/fixtures/`. The out-of-scope question is handled locally by design.

## Product price and availability

**Customer:** Quanto custa o Takamine GD20?

**Empório da Música:** O Takamine GD20 custa **R$ 2199**.

**Source:** `Desafio Técnico AI Engineer 2026/data/desafio_tecnico_ai_eng - products.csv`

## Return policy

**Customer:** Comprei online há cinco dias e me arrependi. Posso devolver?

**Empório da Música:** Com base na evidência fornecida, aqui estão as informações sobre o arrependimento de compra online:

* **Prazo para devolução:** O cliente pode solicitar a devolução em até 7 (sete) dias corridos após o recebimento do produto, sem necessidade de justificativa.
* **Condições do produto:** O produto deve estar em sua embalagem original, sem sinais de uso, com todos os acessórios e manuais.
* **Quem paga o frete de devolução:** O frete de devolução é por conta da loja em caso de arrependimento.
* **Forma e prazo do reembolso:** O reembolso será realizado na mesma forma de pagamento original em até 10 dias úteis.

**Source:** `Desafio Técnico AI Engineer 2026/data/políticas_da_loja.pdf`

## Order status

**Customer:** Qual é o status do meu pedido?

**CLI prompt:** Número do pedido

**Customer:** TESTE-100

**CLI prompt:** E-mail cadastrado (hidden input)

**Customer:** `cliente@example.test`

**Empório da Música:** Status do pedido: shipped. Previsão de entrega: 2026-11-05. Fonte: `orders.csv`.

**Source:** `examples/fixtures/orders.csv` and `examples/fixtures/customers.csv` (fictional data)

## Out-of-scope question

**Customer:** Qual é a capital da França?

**Empório da Música:** Oi! Posso ajudar com instrumentos musicais, preços e disponibilidade do catálogo, além das políticas da loja.
