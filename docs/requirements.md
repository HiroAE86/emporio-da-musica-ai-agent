# Requisitos do desafio técnico — AI Engineer

Fonte: `Desafio Técnico AI Engineer 2026/desafio_tecnico_ai_eng_artefact.pdf`.

## Objetivo

Construir em Python um agente de atendimento por mensagens para a loja fictícia Empório da Música, em Campo Grande/MS, para apoiar a equipe com perguntas recorrentes.

## Comportamento obrigatório

- Usar persona e tom alinhados à identidade da loja.
- Receber mensagens e responder com base no contexto fornecido.
- Consultar dados operacionais para fatos como preço, disponibilidade de produtos e status de pedidos.
- Consultar as políticas para regras como trocas, devoluções, horários de funcionamento e formas de pagamento.
- Lidar adequadamente com perguntas fora do escopo.

## Fontes fornecidas

- `Desafio Técnico AI Engineer 2026/data/*.csv`: tabelas operacionais, incluindo produtos, pedidos, clientes e promoções.
- `Desafio Técnico AI Engineer 2026/data/políticas_da_loja.pdf`: manual interno de políticas e procedimentos de atendimento.
- O uso de todos os dados é opcional; selecionar o que contribuir para a experiência.

## Decisões técnicas a documentar

O README deve justificar:

- abordagem/framework do agente (por exemplo, RAG, chamadas de ferramentas, ReAct, agente SQL ou híbrido);
- modelo e provedor;
- interface (CLI, notebook, API ou UI simples);
- persistência do histórico, se fizer sentido;
- tratamento dos dados.

Python é a única restrição técnica obrigatória. Quando houver ambiguidade ou informação indisponível, assumir uma interpretação razoável e registrá-la no README.

## Entregáveis

1. Repositório Git público no GitHub, com histórico de commits que mostre progresso real. Não consolidar todo o trabalho em um único force-push nem alterar o repositório após o prazo de entrega.
2. README com configuração do ambiente e provedor, comandos para executar, justificativas técnicas (incluindo retrieval e estratégia de prompt), limitações conhecidas e melhorias futuras, e declaração de assistentes de código usados e como.
3. De 3 a 5 conversas de exemplo em `.md`, `.txt` ou imagem, cobrindo cenários variados. Pelo menos uma deve demonstrar consulta não trivial a dados ou aplicação de política.
4. Enviar o link do repositório público em resposta ao e-mail do processo seletivo, dentro do prazo comunicado.

## Cenários sugeridos

- Listar violões disponíveis que custem até R$ 1.000.
- Informar o endereço da loja.
- Consultar o preço do Takamine GD20.
- Explicar se uma compra por arrependimento pode ser devolvida, aplicando a política.

## Checklist de aceite

- [ ] Python é a linguagem principal.
- [ ] Persona, respostas baseadas no contexto, escolha entre dados e políticas, e tratamento de perguntas fora de escopo estão demonstrados.
- [ ] Fatos operacionais vêm dos CSVs relevantes; respostas de política vêm do manual.
- [ ] README contém instruções de execução, decisões e justificativas, limitações e declaração de uso de assistentes.
- [ ] Há de 3 a 5 conversas variadas, incluindo uma consulta ou aplicação de política não trivial.
- [ ] O link do repositório público é enviado até o prazo.
