# Verified CLI conversations

These five conversations were run offline against the supplied CSV and policy PDF. The order fixture is fictional.

## Products under a budget

**Customer:** Quais violões vocês têm até R$ 1.000?

**Empório da Música:** Oi! Encontrei estas opções no catálogo:
Yamaha C40 Nylon Natural — R$ 599,90 — disponível (linha 2)
Yamaha C70 Nylon Natural — R$ 849,00 — disponível (linha 3)
Tagima Memphis AC-39 Nylon Natural — R$ 429,90 — disponível (linha 4)
Giannini GN-15 Nylon Cedr Natural — R$ 689,00 — disponível (linha 5)
Rozini RC-104 Nylon Estudante — R$ 459,90 — disponível (linha 6)
Tagima Dallas Tuner Aço Natural — R$ 749,00 — disponível (linha 7)
Yamaha F310 Aço Natural — R$ 699,90 — disponível (linha 8)
Giannini GF-1R Aço Folk Sunburst — R$ 579,90 — disponível (linha 9)
Shelby SN-100 Folk Aço Preto — R$ 549,00 — disponível (linha 10)
Tagima Woodstock Dreadnought Natural — R$ 899,00 — disponível (linha 12)
Giannini GF-3D Dreadnought Sunburst — R$ 799,90 — indisponível (linha 17)
Shelby SGD-195E Elétrico Aço Sunburst — R$ 799,00 — disponível (linha 28)
Tagima TW-7 7 Cordas Aço Natural — R$ 999,00 — disponível (linha 33)
Shelby SN-7C 7 Cordas Nylon Natural — R$ 749,00 — indisponível (linha 34)
Kala KA-B Barítono Mogno — R$ 599,00 — disponível (linha 49)
Fonte: Desafio Técnico AI Engineer 2026/data/desafio_tecnico_ai_eng - products.csv

## Product price and availability

**Customer:** Quanto custa o Takamine GD20?

**Empório da Música:** Oi! Takamine GD20 Dreadnought Natural está cadastrado por R$ 2.199,00 e aparece como disponível no arquivo, com 5 unidade(s). A informação vem do catálogo fornecido, não de estoque ao vivo.
Fonte: Desafio Técnico AI Engineer 2026/data/desafio_tecnico_ai_eng - products.csv

## Exchange for a manufacturing defect

**Customer:** Como funciona a troca por defeito?

**Empório da Música:** Oi! Para defeito de fabricação, a troca pode ser solicitada em até 30 dias corridos após a compra. Trocas por preferência podem ser feitas em até 7 dias, conforme disponibilidade, com o produto em perfeito estado e na embalagem original. Há itens não elegíveis; consulte a equipe para confirmar seu caso.
Fonte: Desafio Técnico AI Engineer 2026/data/políticas_da_loja.pdf

## Order status with verification

**Customer:** Qual é o status do meu pedido?

**CLI:** Número do pedido: TESTE-100
**CLI:** E-mail cadastrado: cliente@example.test
**CLI:** Telefone cadastrado: 67999990000
**Empório da Música:** Status do pedido: shipped. Previsão de entrega: 2026-11-05. Fonte: orders.csv.

## Out of scope

**Customer:** Qual é a capital da França?

**Empório da Música:** Oi! Posso ajudar com instrumentos musicais, preços e disponibilidade do catálogo, além das políticas da loja.
