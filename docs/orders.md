# Domínio: pedidos e clientes

## Fontes

Os arquivos `orders.csv` e `customers.csv` fornecem os campos para verificar pedidos. Os arquivos reais ficam locais e não são incluídos no repositório público. `examples/fixtures/` contém dados fictícios para reproduzir a demonstração.

## Consulta de status

O CLI solicita o número do pedido e o e-mail cadastrado. Ele confere a relação entre `order_id`, `customer_id` e `email` localmente. Se os dados não corresponderem, a resposta não revela se o pedido ou o e-mail existe.

Quando a verificação passa, o CLI retorna somente o status e a previsão de entrega. Não envia dados de pedido ou contato ao modelo. A correspondência por e-mail é uma proteção básica para a demonstração, não uma autenticação adequada para produção.
