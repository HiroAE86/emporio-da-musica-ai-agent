"""Local response templates backed by supplied catalog and policy evidence."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    kind: str
    source: str
    text: str


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def local_answer(question: str, evidence: Evidence | None) -> str:
    if evidence is None:
        return "Oi! Posso ajudar com instrumentos musicais, preços e disponibilidade do catálogo, além das políticas da loja."
    if evidence.kind == "product":
        if evidence.text.startswith(("No matching", "Several products")):
            return evidence.text
        values = dict(line.split(": ", 1) for line in evidence.text.splitlines() if ": " in line)
        price = float(values["Price (BRL)"])
        formatted = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        status = (
            "disponível"
            if values["Status"] == "active" and int(values["Stock in supplied CSV snapshot"]) > 0
            else "indisponível"
        )
        return f"Oi! {values['Name']} está cadastrado por {formatted} e aparece como {status} no arquivo, com {values['Stock in supplied CSV snapshot']} unidade(s). A informação vem do catálogo fornecido, não de estoque ao vivo."
    if evidence.kind == "category":
        formatted = evidence.text
        if formatted.startswith("Nenhum"):
            return "Oi! " + formatted
        return "Oi! Encontrei estas opções no catálogo:\n" + formatted
    if evidence.kind == "policy" and evidence.text:
        return policy_answer(question, evidence.text)
    query = normalize(question)
    if "defeito" not in query and any(term in query for term in ("arrepend", "devol", "retorn")):
        return regret_answer()
    return "Encontrei informações da política da loja. Não consegui resumir esta política agora; consulte a fonte ou fale com a equipe da loja."


def regret_answer() -> str:
    return (
        "Oi! Para compras online, você pode pedir a devolução em até 7 dias corridos após receber o produto, sem justificar. "
        "Ele precisa estar sem uso, na embalagem original e com acessórios e manuais. A loja paga o frete de devolução, "
        "e o reembolso ocorre pela forma de pagamento original em até 10 dias úteis."
    )


def policy_answer(question: str, source_text: str) -> str:
    topics = {
        "exchange": ("troca", "devol", "arrepend"),
        "address": ("endereco", "onde fica", "localizacao"),
        "hours": ("horario", "abre", "fecha", "funciona"),
        "payment": ("pagamento", "pix", "cartao", "boleto"),
    }
    query = normalize(question)
    is_defect = any(term in query for term in ("defeito", "quebrad", "estragad", "nao funciona"))
    if not is_defect and any(term in query for term in ("devol", "arrepend", "retorn")):
        return regret_answer()
    key = (
        "exchange"
        if is_defect
        else next(
            (name for name, terms in topics.items() if any(term in query for term in terms)), None
        )
    )
    if key is None:
        return "Encontrei informações da política da loja. Não consegui resumir esta política agora; consulte a fonte ou fale com a equipe da loja."
    text = normalize(source_text)
    if not policy_facts_present(key, text):
        return "Oi! Não encontrei essa informação nas fontes fornecidas. Posso encaminhar sua dúvida para a equipe da loja."
    if key == "exchange" and "30 (trinta) dias corridos" not in text:
        return regret_answer()
    return {
        "address": "Oi! A loja fica na Rua 14 de Maio, 3200, Centro, Campo Grande/MS, CEP 79202-333.",
        "hours": "Oi! O atendimento presencial e via WhatsApp funciona de segunda a sexta, das 9h às 18h, e aos sábados, das 9h às 13h. A loja fecha aos domingos e feriados.",
        "payment": "Oi! A loja aceita PIX à vista com 5% de desconto, cartões de débito e crédito (crédito em até 12x sem juros, parcela mínima de R$ 100) e boleto à vista, com compensação em até 3 dias úteis.",
        "exchange": "Oi! Para defeito de fabricação, a troca pode ser solicitada em até 30 dias corridos após a compra. Trocas por preferência podem ser feitas em até 7 dias, conforme disponibilidade, com o produto em perfeito estado e na embalagem original. Há itens não elegíveis; consulte a equipe para confirmar seu caso.",
    }[key]


def policy_facts_present(key: str, text: str) -> bool:
    checks = {
        "address": ("rua 14 de maio", "cep 79202-333"),
        "hours": ("horario de funcionamento", "segunda a sexta-feira", "domingo e feriados"),
        "payment": ("formas de pagamento", "pix", "boleto bancario"),
        "exchange": ("politica de trocas e devolucoes", "trocas", "devolucoes"),
    }
    return all(term in text for term in checks[key])
