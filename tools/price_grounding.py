"""Check displayed prices against names and amounts in the current evidence only."""

from __future__ import annotations

import re

from offline_answers import normalize

MONEY = re.compile(r"R\$\s*([\d.]+(?:,\d{1,2})?)", re.IGNORECASE)


def clean(text: str) -> str:
    return re.sub(r"[*`_]", "", normalize(text)).translate(
        str.maketrans({"\u00a0": " ", "\u2007": " ", "\u202f": " "})
    )


def cents(value: str) -> int:
    return round(float(value.replace(".", "").replace(",", ".")) * 100)


def _pairs(evidence: str) -> list[tuple[str, int]]:
    return [
        (clean(name), cents(price))
        for name, price in re.findall(r"^(.+?) — R\$\s*([\d.,]+)", evidence, re.MULTILINE)
    ]


def _named_price(prefix: str, price: int, pairs: list[tuple[str, int]]) -> bool:
    matches = []
    for name, expected in pairs:
        words = name.split()
        aliases = [" ".join(words[:end]) for end in range(min(2, len(words)), len(words) + 1)]
        for alias in aliases:
            if re.search(
                rf"\b{re.escape(alias)}\b[\s:|—–(),-]*(?:(?:custa|por|a partir de|esta por|preco)\s*[:—–-]?\s*)?$",
                prefix,
            ):
                matches.append(expected)
                break
    return bool(matches) and all(expected == price for expected in matches)


def prices_grounded(answer: str, evidence: str) -> bool:
    """Fail closed on unrecognized price-bearing category prose or product pairs."""
    answer, source = clean(answer), clean(evidence)
    pairs = _pairs(evidence)
    product = re.search(r"^price \(brl\): ([\d.,]+)$", source, re.MULTILINE)
    maximum = re.search(r"limite de preco desta consulta: r\$\s*([\d.,]+)", source)
    limit = cents(maximum.group(1)) if maximum else None
    for line in answer.splitlines():
        previous = 0
        for match in MONEY.finditer(line):
            price = cents(match.group(1))
            prefix = line[previous : match.start()].strip()
            previous = match.end()
            if product and not pairs:
                if price != round(float(product.group(1).replace(",", ".")) * 100):
                    return False
            elif _named_price(prefix, price, pairs):
                if limit is not None and price > limit:
                    return False
            elif line.strip() not in source.splitlines() or " — r$" in line:
                return False
    return True
