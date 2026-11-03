"""Small source-grounded CLI for the Empório da Música case."""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from catalog import category_evidence
from offline_answers import Evidence, carry_over, local_answer
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


HISTORY_MESSAGES = 6


def model_answer(
    question: str, evidence: Evidence | None, history: list[dict[str, str]] | None = None
) -> str:
    base_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
    if not base_url:
        return local_answer(question, evidence)
    instructions = (
        "Você atende a Empório da Música. Responda em português brasileiro, com tom informal e profissional. "
        "Use somente as evidências fornecidas. Não invente preço, estoque, regra ou condição. "
        "Ao citar um produto, escreva o nome e o preço exatamente como na evidência. O estoque é uma fotografia do CSV, não tempo real. "
        "Em perguntas sobre arrependimento de compra online, inclua o prazo, as condições do produto, "
        "quem paga o frete de devolução, a forma e o prazo do reembolso, se constarem na evidência. "
        "Se a evidência não responder, diga isso e sugira falar com a equipe. Nunca exponha dados pessoais. "
        "Sem evidência, responda cumprimentos de forma breve; para assuntos fora da loja, não responda a pergunta "
        "e ofereça ajuda com instrumentos, preços, disponibilidade, pedidos e políticas da loja."
    )
    if evidence is None:
        context = "Nenhuma evidência das fontes da loja corresponde a esta mensagem."
    else:
        context = f"Evidência ({evidence.kind}, fonte {evidence.source}):\n{evidence.text}"
    payload = json.dumps(
        {
            "model": os.getenv("OPENAI_MODEL", "lfm3-omni-2b"),
            "messages": [
                {"role": "system", "content": instructions},
                *(history or [])[-HISTORY_MESSAGES:],
                {"role": "user", "content": f"Pergunta do cliente: {question}\n\n{context}"},
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
        content = result["choices"][0]["message"]["content"].strip()
        return content or local_answer(question, evidence)
    except (
        HTTPError,
        URLError,
        TimeoutError,
        ValueError,
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        print(
            f"API indisponível ({error}); usando resposta local baseada na fonte.", file=sys.stderr
        )
        return local_answer(question, evidence)


def print_response(
    question: str,
    prefix: str = "",
    history: list[dict[str, str]] | None = None,
    previous: Evidence | None = None,
) -> tuple[str, Evidence | None]:
    if is_order_request(question):
        answer = answer_order_status()
        print(f"{prefix}{answer}")
        return answer, None
    evidence = carry_over(load_evidence(question), previous, question)
    answer = model_answer(question, evidence, history)
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
