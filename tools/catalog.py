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
    "o que voces vendem",
    "o que vcs vendem",
    "o que tem ai",
    "o que a loja vende",
    "o que voces tem ai",
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


def _amount(value: str) -> float:
    value = normalize(value).strip()
    if value.endswith("k"):
        return float(value[:-1].replace(",", ".")) * 1000
    if "mil" in value:
        number = re.search(r"\d+(?:[.,]\d+)?", value)
        return (float(number.group().replace(",", ".")) if number else 1) * 1000
    if "." in value:
        value = value.replace(".", "")
    return float(value.replace(",", "."))


def _line(row: dict[str, str], row_number: int, with_description: bool) -> str:
    status = "disponível" if _available(row) else "indisponível"
    line = f"{row['name']} — {brl(_price(row))} — {status}"
    if with_description:
        line += f" — {row['description'].split('.')[0].strip()}"
    return line


def _sort_selected(selected: list[tuple[int, dict[str, str]]], query: str, beginner: bool) -> bool:
    only_best = any(
        term in query
        for term in (
            "mais barato",
            "mais barata",
            "menor preco",
            "mais caro",
            "mais cara",
            "maior preco",
        )
    )
    if any(term in query for term in ("mais barato", "mais barata", "menor preco")):
        selected.sort(key=lambda item: _price(item[1]))
    elif any(term in query for term in ("mais caro", "mais cara", "maior preco")):
        selected.sort(key=lambda item: _price(item[1]), reverse=True)
    if beginner:
        selected.sort(
            key=lambda item: (
                not _available(item[1]),
                not any(term in normalize(item[1]["description"]) for term in BEGINNER_TERMS),
                _price(item[1]),
            )
        )
    return only_best


def _empty_category(
    category: str,
    maximum: float | None,
    rows: list[dict[str, str]],
    source: str,
    label: str,
    limit_note: str,
) -> Evidence:
    limit = f" até {brl(maximum)}" if maximum is not None else ""
    details = f"Nenhum produto em {LABELS[category]}{limit}."
    if maximum is not None:
        above = sorted(
            (row for row in rows if _in_category(row, category) and _price(row) > maximum),
            key=_price,
        )
        if above:
            details += f" Mais barato acima do limite: {_line(above[0], 0, False)}."
    return Evidence(
        "category",
        source,
        f"{label}\n{limit_note}\nCorrespondências dentro do limite: 0\n{details}",
    )


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

    mentions = [
        (term, match) for term in CATEGORY_TERMS for match in re.finditer(rf"\b{term}s?\b", query)
    ]
    category = next(
        (term for term, match in mentions if not re.search(r"\bnao\s+$", query[: match.start()])),
        None,
    )
    if category == "baixo" and re.search(r"\b(preco|valor|custa)\s+baixo\b", query):
        category = None
    if category is None:
        return None
    between = re.search(r"\bentre\s+(.+?)\s+e\s+(.+?)(?:\s+reais)?(?:\b|$)", query)
    budget = re.search(
        r"\b(?:ate|abaixo de|no maximo)\s+r?\$?\s*(mil(?:\s+reais)?|[\d.,]+k?|\d+(?:[.,]\d+)?\s*mil(?:\s+reais)?)",
        query,
    )
    maximum = _amount(budget.group(1)) if budget else None
    beginner = any(term in query for term in BEGINNER_TERMS)
    selected = [
        (number, row)
        for number, row in enumerate(rows, start=2)
        if _in_category(row, category) and (maximum is None or _price(row) <= maximum)
    ]
    if between:
        low, high = _amount(between.group(1)), _amount(between.group(2))
        selected = [(number, row) for number, row in selected if low <= _price(row) <= high]
    only_best = _sort_selected(selected, query, beginner)
    label = f"Categoria: {LABELS[category]}"
    limit_note = (
        f"Limite de preço desta consulta: {brl(maximum)}."
        if maximum is not None
        else "Limite de preço desta consulta: nenhum; limites anteriores não são herdados."
    )
    if not selected:
        return _empty_category(category, maximum, rows, source, label, limit_note)
    limit = 1 if only_best else LIST_LIMIT
    lines = [_line(row, number, beginner) for number, row in selected[:limit]]
    if maximum is not None:
        lines.insert(0, f"Correspondências até {brl(maximum)}: {len(selected)}")
    if len(selected) > limit and not only_best:
        lines.append(f"(mais {len(selected) - LIST_LIMIT} produto(s) nesta categoria)")
    return Evidence("category", source, label + "\n" + limit_note + "\n" + "\n".join(lines))
