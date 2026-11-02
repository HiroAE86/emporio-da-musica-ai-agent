"""Small source-grounded CLI for the Empório da Música case."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Desafio Técnico AI Engineer 2026" / "data"
PRODUCTS = next(DATA.glob("*products.csv"))
POLICY_PDF = next(DATA.glob("*pol*.pdf"))
POLICY_TERMS = (
    "troca",
    "devol",
    "retorn",
    "arrepend",
    "pagamento",
    "pix",
    "cartao",
    "boleto",
    "horario",
    "aberto",
    "endereco",
    "localizacao",
    "frete",
    "entrega",
    "garantia",
)
PRODUCT_TERMS = (
    "preco",
    "custa",
    "valor",
    "estoque",
    "disponivel",
    "produto",
    "violao",
    "guitarra",
    "piano",
    "instrumento",
)
IGNORED_PRODUCT_WORDS = {
    "preco",
    "quanto",
    "custa",
    "valor",
    "estoque",
    "disponivel",
    "produto",
    "violao",
    "guitarra",
    "piano",
    "instrumento",
    "do",
    "da",
    "de",
    "o",
    "a",
    "um",
    "uma",
    "qual",
    "me",
    "diga",
    "por",
    "favor",
    "tem",
    "com",
    "para",
}


@dataclass(frozen=True)
class Evidence:
    kind: str
    source: str
    text: str


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in text if not unicodedata.combining(char))


def load_evidence(question: str) -> Evidence | None:
    query = normalize(question)
    if any(term in query for term in POLICY_TERMS):
        extracted = subprocess.run(
            ["pdftotext", "-layout", str(POLICY_PDF), "-"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return Evidence("policy", str(POLICY_PDF.relative_to(ROOT)), extracted[:18000])

    with PRODUCTS.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    query_words = {
        word
        for word in re.findall(r"[a-z0-9]+", query)
        if word not in IGNORED_PRODUCT_WORDS and len(word) > 1
    }
    matches = []
    for row_number, row in enumerate(rows, start=2):
        name_words = set(re.findall(r"[a-z0-9]+", normalize(row["name"])))
        score = len(query_words & name_words)
        if score:
            matches.append((score, row_number, row))
    if matches or any(term in query for term in PRODUCT_TERMS):
        if not matches:
            return Evidence(
                "product",
                str(PRODUCTS.relative_to(ROOT)),
                "No matching product was found in the catalog.",
            )
        best_score = max(match[0] for match in matches)
        best = [match for match in matches if match[0] == best_score]
        if len(best) != 1:
            names = ", ".join(match[2]["name"] for match in best[:5])
            return Evidence(
                "product",
                str(PRODUCTS.relative_to(ROOT)),
                f"Several products may match. Ask the customer to clarify: {names}",
            )
        _, row_number, row = best[0]
        text = (
            f"Name: {row['name']}\nPrice (BRL): {row['price_brl']}\n"
            f"Stock in supplied CSV snapshot: {row['stock_quantity']}\nStatus: {row['status']}\n"
            f"Description: {row['description']}\nCSV row: {row_number}"
        )
        return Evidence("product", str(PRODUCTS.relative_to(ROOT)), text)
    return None


def local_answer(question: str, evidence: Evidence | None) -> str:
    if evidence is None:
        return "Oi! Posso ajudar com instrumentos musicais, preços e disponibilidade do catálogo, além das políticas da loja."
    if evidence.kind == "product":
        if evidence.text.startswith("No matching") or evidence.text.startswith("Several products"):
            return evidence.text
        values = dict(line.split(": ", 1) for line in evidence.text.splitlines() if ": " in line)
        price = float(values["Price (BRL)"])
        price_brl = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        status = (
            "disponível"
            if values["Status"] == "active" and int(values["Stock in supplied CSV snapshot"]) > 0
            else "indisponível"
        )
        return f"Oi! {values['Name']} está cadastrado por {price_brl} e aparece como {status} no arquivo, com {values['Stock in supplied CSV snapshot']} unidade(s). A informação vem do catálogo fornecido, não de estoque ao vivo."
    if any(term in normalize(question) for term in ("arrepend", "devol", "retorn")):
        return (
            "Oi! Para compras online, você pode pedir a devolução em até 7 dias corridos após receber o produto, sem justificar. "
            "Ele precisa estar sem uso, na embalagem original e com acessórios e manuais. A loja paga o frete de devolução, "
            "e o reembolso ocorre pela forma de pagamento original em até 10 dias úteis."
        )
    return "Encontrei informações da política da loja. Não consegui resumir esta política agora; consulte a fonte ou fale com a equipe da loja."


def model_answer(question: str, evidence: Evidence | None) -> str:
    if evidence is None:
        return local_answer(question, evidence)
    base_url = os.getenv("OPENAI_BASE_URL", "http://100.111.77.36:1234/v1").rstrip("/")
    instructions = (
        "Você atende a Empório da Música. Responda em português brasileiro, com tom informal e profissional. "
        "Use somente as evidências fornecidas. Não invente preço, estoque, regra ou condição. O estoque é uma fotografia do CSV, não tempo real. "
        "Se a evidência não responder, diga isso e sugira falar com a equipe. Nunca exponha dados pessoais."
    )
    payload = json.dumps(
        {
            "model": os.getenv("OPENAI_MODEL", "lfm3-omni-2b"),
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": f"Pergunta do cliente: {question}\n\nEvidência ({evidence.kind}, fonte {evidence.source}):\n{evidence.text}"},
            ],
        }
    ).encode()
    request = Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'local')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read())
        return result["choices"][0]["message"]["content"].strip()
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError) as error:
        print(
            f"API indisponível ({error}); usando resposta local baseada na fonte.", file=sys.stderr
        )
        return local_answer(question, evidence)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "message", nargs="*", help="customer message; omit to start interactive mode"
    )
    args = parser.parse_args()
    if args.message:
        question = " ".join(args.message)
        try:
            evidence = load_evidence(question)
            print(model_answer(question, evidence))
            if evidence:
                print(f"\nFonte: {evidence.source}")
        except (OSError, subprocess.CalledProcessError, StopIteration) as error:
            parser.error(f"não consegui consultar as fontes: {error}")
        return

    print("Empório da Música. Digite 'sair' para encerrar.")
    while True:
        try:
            question = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.casefold() in {"sair", "exit", "quit"}:
            break
        if not question:
            continue
        try:
            evidence = load_evidence(question)
            print(f"Loja: {model_answer(question, evidence)}")
            if evidence:
                print(f"Fonte: {evidence.source}")
        except (OSError, subprocess.CalledProcessError, StopIteration) as error:
            print(f"Não consegui consultar as fontes: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
