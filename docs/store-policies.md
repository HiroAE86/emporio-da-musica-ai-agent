# Domínio: políticas da loja

## Fonte e extração

`Desafio Técnico AI Engineer 2026/data/políticas_da_loja.pdf` é a fonte de regras. O CLI usa `pdftotext -layout` para extrair o texto e envia até 18.000 caracteres ao modelo quando a pergunta contém termos de política.

## Regras demonstradas

A conversa salva em [`examples/conversations.md`](../examples/conversations.md) demonstra a seção 4.1 sobre arrependimento de compra online. A resposta inclui o prazo, as condições do produto, o frete de devolução e o reembolso.

## Limites

A seleção do manual usa palavras-chave, não busca semântica por seção. O prompt instrui o modelo a usar o manual e não inventar regras, mas o CLI não valida a resposta gerada. Se o modelo estiver indisponível, a resposta local conhece apenas o caso de devolução por arrependimento; para outras regras, ela encaminha o cliente à equipe.
