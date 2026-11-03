# Domínio: atendimento ao cliente

## Objetivo

Ajudar a equipe da Empório da Música a responder perguntas recorrentes por mensagens, mantendo uma experiência coerente com a identidade da loja.

## Tipos de solicitação

| Intenção | Exemplos | Fonte principal |
|---|---|---|
| Produto | preço, características, disponibilidade, alternativas | Catálogo e categorias CSV |
| Promoção | campanha e condições cadastradas | Promoções CSV |
| Pedido | status e itens de uma compra | Pedidos e itens CSV; identificar cliente com segurança |
| Regra da loja | horário, pagamento, troca, devolução | Manual de políticas PDF |
| Fora de escopo | assunto sem relação com a loja | Sem consulta às fontes; orientar cordialmente |

## Regras de resposta

- Usar uma persona cordial, informal e profissional, alinhada à loja.
- Não apresentar suposições como fatos nem inventar informações ausentes.
- Consultar a fonte correspondente antes de responder fatos operacionais ou regras.
- Quando não houver informação suficiente ou segura, pedir apenas os dados necessários ou encaminhar para atendimento humano.

## Implementação atual

O protótipo está em `tools/agent_cli.py`. Sem endpoint, mantém roteamento local por palavras-chave. Com endpoint, o modelo chama ferramentas que consultam o CSV de produtos ou seções do wiki Markdown. Para status de pedido, número, e-mail e telefone são verificados localmente; ao modelo só chegam status e previsão de entrega. Consulte promoções não é suportada via CSV.
