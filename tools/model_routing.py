"""Choose model-led tools, evidence retry, or deterministic local answers."""

from __future__ import annotations

import os
import re
import sys
from urllib.error import HTTPError, URLError

from catalog import brl
from offline_answers import Evidence, local_answer, normalize


def model_answer(
    question: str,
    evidence: Evidence | None,
    history: list[dict[str, str]] | None = None,
    metadata: dict | None = None,
) -> str:
    metadata = metadata if metadata is not None else {}
    strategy = os.getenv("AGENT_TOOL_STRATEGY", "auto").casefold()
    if strategy not in {"auto", "tools", "preretrieve"}:
        strategy = "auto"
    base_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
    if not base_url:
        metadata["path"] = "local"
        return local_answer(question, evidence)
    tools_enabled = os.getenv("AGENT_TOOLS", "1") != "0" and strategy != "preretrieve"
    if tools_enabled:
        result = _tools_answer(question, evidence, history, strategy, metadata)
        if result is not None:
            return result
    elif os.getenv("AGENT_TOOLS", "1") != "0" and strategy == "tools":
        metadata["path"] = "local"
        return local_answer(question, evidence)
    if strategy != "preretrieve" and os.getenv("AGENT_TOOLS", "1") != "0":
        metadata["path"] = "local"
        return local_answer(question, evidence)
    from legacy_model import answer

    metadata["path"] = "preretrieve"
    result = answer(question, evidence, history)
    if _answer_is_valid(question, result, evidence):
        return result
    metadata["path"] = "local"
    return local_answer(question, evidence)


def _tools_answer(
    question: str,
    evidence: Evidence | None,
    history: list[dict[str, str]] | None,
    strategy: str,
    metadata: dict,
) -> str | None:
    from tool_calling import run_tool_agent

    try:
        calls: list[dict] = []
        answer = run_tool_agent(question, history, calls)
        metadata["tool_calls"] = calls
        from intent_router import deterministic_tool

        called_tool = bool(calls)
        required_tool = deterministic_tool(question) is not None or evidence is not None
        if (
            answer
            and (called_tool or not required_tool)
            and _answer_is_valid(question, answer, evidence)
        ):
            metadata["path"] = "tools"
            return answer
        if strategy != "tools":
            return _preretrieve_retry(question, evidence, history, metadata)
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
            f"API com ferramentas indisponível ({error}); usando evidência local.", file=sys.stderr
        )
        if strategy != "tools":
            return _preretrieve_retry(question, evidence, history, metadata)
    return None


def _preretrieve_retry(
    question: str, evidence: Evidence | None, history: list[dict[str, str]] | None, metadata: dict
) -> str:
    if evidence is not None:
        from legacy_model import answer

        result = answer(question, evidence, history)
        if _answer_is_valid(question, result, evidence):
            metadata["path"] = "preretrieve"
            return result
    metadata["path"] = "local"
    return local_answer(question, evidence)


def _answer_is_valid(question: str, answer_text: str, evidence: Evidence | None) -> bool:
    if _check_model_prices(answer_text, evidence) != answer_text:
        return False
    from intent_router import deterministic_tool

    if evidence is not None and evidence.kind == "category":
        category = re.search(r"^Categoria: (.+)$", evidence.text, re.MULTILINE)
        if category and normalize(category.group(1)) not in normalize(answer_text):
            return False
    intent = deterministic_tool(question)
    if intent and intent[0] == "list_category":
        category = intent[1].get("category", "").rstrip("s")
        return category in normalize(answer_text)
    return True


def _check_model_prices(answer_text: str, evidence: Evidence | None) -> str:
    if evidence is None or evidence.kind not in {"product", "category"}:
        return answer_text
    normalized_answer = answer_text.translate(
        str.maketrans({"\u00a0": " ", "\u2007": " ", "\u202f": " "})
    )
    amounts = re.findall(r"R\$\s*([\d.]+(?:,\d{1,2})?)", normalized_answer)
    if not amounts:
        return answer_text
    if evidence.kind == "category":
        import csv

        from agent_cli import PRODUCTS

        with PRODUCTS.open(encoding="utf-8-sig", newline="") as stream:
            valid_prices = {
                brl(float(row["price_brl"].replace(",", "."))) for row in csv.DictReader(stream)
            }
        return (
            answer_text
            if all("R$ " + amount in valid_prices for amount in amounts)
            else local_answer("", evidence)
        )
    source_price = re.search(r"^Price \(BRL\): ([\d.,]+)$", evidence.text, re.MULTILINE)
    if source_price is None:
        return local_answer("", evidence)
    expected = brl(float(source_price.group(1).replace(",", ".")))
    if any("R$ " + amount != expected for amount in amounts):
        return local_answer("", evidence)
    return answer_text
