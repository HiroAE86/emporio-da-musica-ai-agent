# Domínio: políticas da loja

## Fonte e extração

`Desafio Técnico AI Engineer 2026/data/políticas_da_loja.pdf` é a fonte de regras. `make policies` extrai o PDF com `pypdf` para [`knowledge/policies/store.md`](../knowledge/policies/store.md), separado pelas dez seções numeradas. O índice [`knowledge/INDEX.md`](../knowledge/INDEX.md) apresenta as fontes e os tópicos ao modelo; a ferramenta lê apenas a seção solicitada.

## Regras demonstradas

A conversa salva em [`examples/conversations.md`](../examples/conversations.md) demonstra a seção 4 sobre trocas por defeito. A seção 4.1 registra o prazo, as condições do produto, o frete de devolução e o reembolso para arrependimento online.

## Limites

O modelo escolhe a seção; não há busca semântica nem embeddings. O prompt instrui o modelo a usar a seção e não inventar regras, mas o CLI não valida a resposta gerada. A checagem de fonte cobre fatos selecionados, não cada frase do manual.
