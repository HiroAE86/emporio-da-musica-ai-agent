# Domínio: catálogo e promoções

## Fonte usada

`Desafio Técnico AI Engineer 2026/data/*products.csv` é a fonte do protótipo. O CLI lê `name`, `price_brl`, `stock_quantity`, `status` e `description`. Considera o item disponível quando `status` é `active` e `stock_quantity` é maior que zero.

## Método de busca

O caminho offline verifica termos de política antes de procurar produto. Para produto, normaliza caixa e acentos, compara palavras da pergunta com palavras do nome e escolhe o maior resultado único. A ferramenta `search_products` reutiliza essa busca; `list_category` filtra a lista local por categoria, orçamento e indicação para iniciantes. O método é lexical; não promete busca semântica.

## Fontes não usadas

`categories.csv` e `promotions.csv` não são usados por estas ferramentas. Categoria é inferida pelo nome e descrição do produto. Promoções e seus períodos não são consultados.
