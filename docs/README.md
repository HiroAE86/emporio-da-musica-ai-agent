# Empório da Música — documentação

Protótipo de agente de atendimento por mensagens para apoiar a equipe da loja fictícia Empório da Música, em Campo Grande/MS.

> **Estado:** há um protótipo de agente em `tools/agent_cli.py`. Esta documentação registra o domínio, os requisitos, as decisões e os limites conhecidos.

## Guias por domínio

- [Atendimento ao cliente](customer-service.md) — persona, tipos de solicitação, limites e roteamento entre fontes.
- [Catálogo e promoções](catalog.md) — produtos, categorias, preços e disponibilidade.
- [Pedidos e clientes](orders.md) — consultas de pedidos e dados relacionados.
- [Políticas da loja](store-policies.md) — regras de atendimento contidas no manual.
- [Wiki de políticas](../knowledge/policies/store.md) — Markdown gerado do manual PDF com `make policies`.
- [Arquitetura e operação](architecture.md) — escolhas técnicas, execução e limitações.
- [Exemplos de conversa](conversations.md) — cenários para o conjunto de demonstração.
- [Requisitos completos](requirements.md) — requisitos e entregáveis extraídos do desafio.

## Fontes fornecidas

Os CSVs e o PDF em `Desafio Técnico AI Engineer 2026/data/` são as fontes disponíveis para o agente. Fatos operacionais devem ser respondidos a partir dos CSVs; regras de atendimento devem vir do manual de políticas. Cada guia de domínio registra quais fontes são pertinentes.

## Processo de implementação

- [Processo de implementação](implementation-process.md) — requisitos analisados, escopo mínimo proposto, sequência de execução e critérios de aceite.
