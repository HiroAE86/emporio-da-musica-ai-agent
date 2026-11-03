"""OpenAI-compatible tool-calling transport and local tool dispatch."""

from __future__ import annotations

import csv
import json
import os
import re
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from catalog import category_evidence
from offline_answers import normalize
from project_paths import ROOT

MAX_TOOL_ROUNDS = 4
POLICY_FILE = ROOT / "knowledge" / "policies" / "store.md"
CATEGORIES = {"violao", "guitarra", "baixo", "bateria", "teclado", "piano", "ukulele"}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search products by name or product terms.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_category",
            "description": "List catalog products in a category, optionally filtered by price or beginner suitability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": sorted(CATEGORIES)},
                    "max_price": {"type": ["number", "null"]},
                    "beginner": {"type": "boolean"},
                },
                "required": ["category"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_policy",
            "description": "Read one numbered policy section from the markdown wiki.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "enum": [
                            "about",
                            "hours",
                            "payment",
                            "exchange",
                            "freight",
                            "promotions",
                            "service",
                            "warranty",
                            "privacy",
                            "final",
                        ],
                    }
                },
                "required": ["section"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Run the local order verification prompts. Never provide customer data to this tool in arguments.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]
POLICY_SECTIONS = {
    "about": "1.",
    "hours": "2.",
    "payment": "3.",
    "exchange": "4.",
    "freight": "5.",
    "promotions": "6.",
    "service": "7.",
    "warranty": "8.",
    "privacy": "9.",
    "final": "10.",
}


def _arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, dict):
        raise TypeError("arguments must be a JSON object")
    return raw


def _search_products(args: dict[str, Any]) -> str:
    query = args.get("query")
    if (
        set(args) != {"query"}
        or not isinstance(query, str)
        or not query.strip()
        or len(query) > 160
    ):
        raise ValueError("query must be a non-empty string up to 160 characters")
    from agent_cli import load_evidence

    evidence = load_evidence(query)
    return (
        evidence.text
        if evidence and evidence.kind == "product"
        else "No exact product match found."
    )


def _list_category(args: dict[str, Any]) -> str:
    if set(args) - {"category", "max_price", "beginner"}:
        raise ValueError("unexpected category arguments")
    category, maximum = args.get("category"), args.get("max_price")
    beginner = args.get("beginner", False)
    invalid_price = maximum is not None and (
        isinstance(maximum, bool)
        or not isinstance(maximum, (int, float))
        or maximum < 0
        or maximum > 1000000
    )
    if category not in CATEGORIES or invalid_price or not isinstance(beginner, bool):
        raise ValueError("invalid category, max_price, or beginner")
    from agent_cli import PRODUCTS, source_name

    with PRODUCTS.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    query = category + (f" ate {maximum}" if maximum is not None else "")
    query += " iniciante" if beginner else ""
    evidence = category_evidence(normalize(query), rows, source_name(PRODUCTS))
    return evidence.text if evidence else "No products found in that category."


def _read_policy(args: dict[str, Any]) -> str:
    if set(args) != {"section"} or args.get("section") not in POLICY_SECTIONS:
        raise ValueError("unknown policy section")
    text = POLICY_FILE.read_text(encoding="utf-8")
    marker = POLICY_SECTIONS[args["section"]]
    for section in re.split(r"(?=^## )", text, flags=re.MULTILINE):
        if section.startswith("## " + marker):
            return section.strip()
    raise ValueError("policy section is missing; run make policies")


def _check_order(args: dict[str, Any]) -> str:
    if args:
        raise ValueError("order data is collected locally, not through tool arguments")
    from order_status import answer_order_status

    result = answer_order_status()
    match = re.search(r"Status do pedido: (.+?)\. Previsão de entrega: (.+?)\.", result)
    return (
        f"Status do pedido: {match.group(1)}. Previsão de entrega: {match.group(2)}."
        if match
        else result
    )


def _dispatch(name: str, raw_args: Any) -> str:
    handlers = {
        "search_products": _search_products,
        "list_category": _list_category,
        "read_policy": _read_policy,
        "check_order_status": _check_order,
    }
    handler = handlers.get(name)
    if handler is None:
        raise LookupError(f"Unknown tool: {name}")
    return handler(_arguments(raw_args))


def _tool_result(call: dict[str, Any]) -> str:
    function = call.get("function", {})
    name = function.get("name", "")
    try:
        return _dispatch(name, function.get("arguments", {}))
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        return f"Invalid arguments for {name}: {error}"
    except LookupError as error:
        return str(error)
    except (OSError, KeyError, csv.Error) as error:
        return f"Tool {name} could not read its source: {error}"


def _model_safe(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted email]", text)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)", "[redacted phone]", text)
    return re.sub(
        r"\b((?:pedido|order|ordem)\s*(?:n[ºo.]?\s*)?[:#-]?\s*)[A-Z0-9][A-Z0-9-]{2,}\b",
        r"\1[redacted order id]",
        text,
        flags=re.IGNORECASE,
    )


def run_tool_agent(question: str, history: list[dict[str, str]] | None = None) -> str | None:
    """Return model content, or None when tool support is unavailable/invalid."""
    base_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
    instructions = (
        "Você atende a Empório da Música em português brasileiro, com tom informal e profissional. "
        "Use as ferramentas para consultar fatos; não invente. A lista de fontes e seções disponíveis:\n"
        + (ROOT / "knowledge" / "INDEX.md").read_text(encoding="utf-8")
        + "\nDados de cliente nunca devem ser solicitados por ferramenta nem repetidos."
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": instructions},
        *[
            {**item, "content": _model_safe(item.get("content", ""))}
            for item in (history or [])[-6:]
        ],
        {"role": "user", "content": _model_safe(question)},
    ]
    for round_number in range(MAX_TOOL_ROUNDS + 1):
        payload = json.dumps(
            {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
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
        except HTTPError as error:
            if error.code in {400, 404, 422}:
                return None
            raise
        choice = result["choices"][0]["message"]
        calls = choice.get("tool_calls") or []
        if not calls:
            return choice.get("content", "").strip() or None
        if round_number == MAX_TOOL_ROUNDS:
            return None
        messages.append(
            {"role": "assistant", "content": choice.get("content"), "tool_calls": calls}
        )
        for call in calls:
            messages.append(
                {"role": "tool", "tool_call_id": call.get("id", ""), "content": _tool_result(call)}
            )
    return None
