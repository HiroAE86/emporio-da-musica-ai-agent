"""Small source-grounded CLI for the Empório da Música case."""

from __future__ import annotations

import argparse
import csv
import difflib
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from catalog import category_evidence
from intent_router import clearly_out_of_scope
from model_routing import model_answer
from offline_answers import Evidence, carry_over
from order_status import answer_order_status, is_order_request
from project_paths import ROOT, resolve_data_dir, resolve_policy_pdf
from pypdf import PdfReader

try:
    DATA = resolve_data_dir()
except FileNotFoundError:
    DATA = ROOT / "Desafio Técnico AI Engineer 2026" / "data"
PRODUCTS = Path(
    os.getenv("PRODUCTS_CSV") or next(DATA.glob("*products.csv"), DATA / "products.csv")
)
try:
    POLICY_PDF = resolve_policy_pdf()
except FileNotFoundError:
    POLICY_PDF = DATA / "politicas_da_loja.pdf"
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
    "baixo",
    "barato",
    "caro",
    "mais",
    "mil",
    "reais",
    "entre",
    "abaixo",
    "maximo",
}


def source_name(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in text if not unicodedata.combining(char))


def _correct_category_typos(query: str) -> str:
    categories = ("violao", "guitarra", "ukulele", "teclado", "bateria")
    for word in re.findall(r"[a-z]+", query):
        suggestion = difflib.get_close_matches(word, categories, n=1, cutoff=0.82)
        if suggestion:
            query = re.sub(rf"\b{word}\b", suggestion[0], query)
    return query


def load_evidence(question: str) -> Evidence | None:
    query = normalize(question)
    query = _correct_category_typos(query.replace("violoes", "violao"))
    if re.search(r"\b(celular|notebook|computador|pc)\b", query):
        return None
    if any(term in query for term in POLICY_TERMS) or any(
        term in query for term in ("onde fica", "abre", "fecha", "funciona")
    ):
        extracted = " ".join(
            " ".join((page.extract_text() or "").split()) for page in PdfReader(POLICY_PDF).pages
        )
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
    listed = category_evidence(query, rows, source_name(PRODUCTS))
    if listed is not None and not (matches and max(match[0] for match in matches) > 1):
        return listed
    if matches:
        best_score = max(match[0] for match in matches)
        best = [match for match in matches if match[0] == best_score]
        if len(best) != 1:
            names = ", ".join(match[2]["name"] for match in best[:5])
            return Evidence(
                "product",
                source_name(PRODUCTS),
                f"Encontrei mais de um produto possível. Qual deles você procura? {names}",
            )
        _, row_number, row = best[0]
        text = (
            f"Name: {row['name']}\nPrice (BRL): {row['price_brl']}\n"
            f"Stock in supplied CSV snapshot: {row['stock_quantity']}\nStatus: {row['status']}\n"
            f"Description: {row['description']}\nCSV row: {row_number}"
        )
        return Evidence("product", source_name(PRODUCTS), text)
    return None


def print_response(
    question: str,
    prefix: str = "",
    history: list[dict[str, str]] | None = None,
    previous: Evidence | None = None,
    metadata: dict | None = None,
) -> tuple[str, Evidence | None]:
    metadata = metadata if metadata is not None else {}
    if is_order_request(question):
        metadata.update(path="local", tool_calls=[])
        answer = answer_order_status()
        print(f"{prefix}{answer}")
        return answer, None
    if clearly_out_of_scope(question):
        metadata.update(path="local", tool_calls=[])
        answer = "Não consigo ajudar com perguntas de conhecimento geral. Posso ajudar com instrumentos musicais, preços, disponibilidade, políticas da loja ou status de pedidos."
        print(f"{prefix}{answer}")
        return answer, None
    evidence = carry_over(load_evidence(question), previous, question)
    answer = model_answer(question, evidence, history, metadata)
    print(f"{prefix}{answer}")
    if evidence:
        print(f"Fonte: {evidence.source}")
    return answer, evidence


def preflight() -> None:
    missing = [str(path) for path in (PRODUCTS, POLICY_PDF) if not path.is_file()]
    if missing:
        print("Missing required data files: " + ", ".join(missing), file=sys.stderr)
        raise SystemExit(2)
    print(f"Data files: OK ({PRODUCTS.name}, {POLICY_PDF.name})")
    endpoint = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
    if not endpoint:
        print("Model endpoint: not configured; local answers are enabled")
        return
    try:
        with urlopen(f"{endpoint}/models", timeout=5) as response:
            response.read(1)
        print(f"Model endpoint: reachable ({endpoint})")
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        print(f"Model endpoint: unavailable ({error}); local answers are enabled")
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preflight", action="store_true", help="check source files and model endpoint"
    )
    parser.add_argument(
        "message", nargs="*", help="customer message; omit to start interactive mode"
    )
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.message:
        try:
            print_response(" ".join(args.message))
        except (OSError, StopIteration) as error:
            parser.error(f"não consegui consultar as fontes: {error}")
    else:
        from chat_cli import interactive

        interactive()


if __name__ == "__main__":
    main()
