"""Category, budget, and catalog-overview lookups over the products CSV."""

from __future__ import annotations

import re

from offline_answers import Evidence, normalize

CATEGORY_TERMS = ("violao", "guitarra", "baixo", "bateria", "teclado", "piano", "ukulele")
OVERVIEW_PHRASES = (
    "o que voce tem",
    "o que vc tem",
    "o que voces tem",
    "o que vcs tem",
    "catalogo",
    "quais produtos",
    "quais instrumentos",
    "que instrumentos",
    "que produtos",
)
BEGINNER_TERMS = ("inician", "estudante", "comecando", "aprender", "recomend")
LIST_LIMIT = 10


def brl(value: float) -> str:
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


LABELS = {
    "violao": "violões",
    "guitarra": "guitarras",
    "baixo": "baixos",
    "bateria": "baterias",
    "teclado": "teclados",
    "piano": "pianos",
    "ukulele": "ukuleles",
}
ALIASES = {"baixo": ("baixo", "bass")}


def _in_category(row: dict[str, str], term: str) -> bool:
    name = normalize(row["name"])
    if any(alias in name for alias in ALIASES.get(term, (term,))):
        return True
    return normalize(row["description"]).startswith(term)


def _available(row: dict[str, str]) -> bool:
    return row["status"] == "active" and int(row["stock_quantity"]) > 0


def _price(row: dict[str, str]) -> float:
    return float(row["price_brl"].replace(",", "."))


def _line(row: dict[str, str], row_number: int, with_description: bool) -> str:
    status = "disponível" if _available(row) else "indisponível"
    line = f"{row['name']} — {brl(_price(row))} — {status} (linha {row_number})"
    if with_description:
        line += f" — {row['description'].split('.')[0].strip()}"
    return line


def category_evidence(query: str, rows: list[dict[str, str]], source: str) -> Evidence | None:
    """Return a category list, a catalog overview, or None when neither applies."""
    if any(phrase in query for phrase in OVERVIEW_PHRASES):
        counts = []
        for term in CATEGORY_TERMS:
            found = [row for row in rows if _in_category(row, term)]
            if found:
                low = min(_price(row) for row in found)
                high = max(_price(row) for row in found)
                counts.append(
                    f"{LABELS[term]}: {len(found)} produto(s), de {brl(low)} a {brl(high)}"
                )
        return Evidence("category", source, "\n".join(counts))

    category = next((term for term in CATEGORY_TERMS if re.search(rf"\b{term}s?\b", query)), None)
    if category is None:
        return None
    budget = re.search(r"\b(?:ate|abaixo de|no maximo)\s+r?\$?\s*([\d.,]+)", query)
    maximum = float(budget.group(1).replace(".", "").replace(",", ".")) if budget else None
    beginner = any(term in query for term in BEGINNER_TERMS)
    selected = [
        (number, row)
        for number, row in enumerate(rows, start=2)
        if _in_category(row, category) and (maximum is None or _price(row) <= maximum)
    ]
    if beginner:
        selected.sort(
            key=lambda item: (
                not _available(item[1]),
                not any(term in normalize(item[1]["description"]) for term in BEGINNER_TERMS),
                _price(item[1]),
            )
        )
    if not selected:
        limit = f" até {brl(maximum)}" if maximum is not None else ""
        return Evidence("category", source, f"Nenhum produto em {LABELS[category]}{limit}.")
    lines = [_line(row, number, beginner) for number, row in selected[:LIST_LIMIT]]
    if len(selected) > LIST_LIMIT:
        lines.append(f"(mais {len(selected) - LIST_LIMIT} produto(s) nesta categoria)")
    return Evidence("category", source, "\n".join(lines))
