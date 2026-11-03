"""Deterministic tool selection for clear customer intents."""

from __future__ import annotations

import json
import re

from catalog import CATEGORY_TERMS
from offline_answers import normalize


def deterministic_tool(question: str) -> tuple[str, dict[str, object]] | None:
    """Return a tool and arguments when the message states a clear lookup intent."""
    query = normalize(question)
    overviews = (
        "o que voce vende",
        "o que voces vendem",
        "o que vcs vendem",
        "o que tem ai",
        "o que voces tem",
        "quais produtos",
        "quais instrumentos",
        "que instrumentos",
        "que produtos",
        "catalogo",
    )
    if any(phrase in query for phrase in overviews):
        return "list_catalog", {}
    mentions = [
        (term, match) for term in CATEGORY_TERMS for match in re.finditer(rf"\b{term}s?\b", query)
    ]
    category = next(
        (
            term
            for term, match in mentions
            if not re.search(r"\bnao\s+$", query[: match.start()])
            and not (term == "baixo" and re.search(r"\b(preco|valor|custa)\s+baixo\b", query))
        ),
        None,
    )
    if category:
        return "list_category", {"category": category}
    policy_terms = {
        "hours": ("horario", "abre", "fecha", "funciona"),
        "payment": ("pagamento", "pix", "cartao", "boleto"),
        "exchange": ("troca", "devol", "retorn", "arrepend"),
        "freight": ("frete", "entrega"),
        "warranty": ("garantia",),
        "privacy": ("privacidade", "dados pessoais"),
    }
    for section, terms in policy_terms.items():
        if any(term in query for term in terms):
            return "read_policy", {"section": section}
    return None


def evidence_messages(
    name: str, arguments: dict[str, object], result: str
) -> list[dict[str, object]]:
    """Represent a pre-retrieval as a normal assistant tool call and result."""
    call_id = "deterministic-lookup"
    return [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)},
                }
            ],
        },
        {"role": "tool", "tool_call_id": call_id, "content": result},
    ]
