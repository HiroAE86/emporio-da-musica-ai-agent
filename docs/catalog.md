# Domínio: catálogo e promoções

## Fonte usada

`Desafio Técnico AI Engineer 2026/data/*products.csv` é a fonte do protótipo. O CLI lê `name`, `price_brl`, `stock_quantity`, `status` e `description`. Considera o item disponível quando `status` é `active` e `stock_quantity` é maior que zero.

## Método de busca

O CLI verifica termos de política antes de procurar produto. Para produto, normaliza caixa e acentos, compara palavras da pergunta com palavras do nome e escolhe o maior resultado único. Em caso de empate, envia ao modelo uma instrução para pedir esclarecimento; se o modelo falhar, a resposta local mostra essa instrução em inglês. O método é lexical; não promete busca semântica.

## Fontes não usadas

`categories.csv` e `promotions.csv` são fornecidos pelo desafio, mas o protótipo não os consulta. A primeira versão cobre busca de produto por nome, preço e disponibilidade. Listas por orçamento, navegação por categoria e consulta de promoções ficam para uma versão futura.
