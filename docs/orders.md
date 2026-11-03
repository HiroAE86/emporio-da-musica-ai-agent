# Domínio: pedidos e clientes

## Fontes

Os arquivos `orders.csv` e `customers.csv` fornecem os campos para verificar pedidos. Os arquivos reais ficam locais e não são incluídos no repositório público. `examples/fixtures/` contém dados fictícios para reproduzir a demonstração.

## Consulta de status

O CLI solicita número do pedido, e-mail e telefone cadastrados. Ele confere localmente a relação entre `order_id`, `customer_id` e os dois contatos. Se os dados não corresponderem, a resposta não revela se o pedido ou os contatos existem.

Quando a verificação passa, o CLI retorna somente o status e a previsão de entrega. Não envia dados de pedido ou contato ao modelo. A correspondência por e-mail é uma proteção básica para a demonstração, não uma autenticação adequada para produção.
