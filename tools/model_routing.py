"""Choose model-led tools, evidence retry, or deterministic local answers."""

from __future__ import annotations

import os
import re
import sys
from urllib.error import HTTPError, URLError

from offline_answers import Evidence, local_answer, normalize
from price_grounding import prices_grounded


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
        results: list[str] = []
        answer = run_tool_agent(question, history, calls, results=results)
        metadata["tool_calls"] = calls
        from intent_router import deterministic_tool

        called_tool = bool(calls)
        required_tool = deterministic_tool(question) is not None or evidence is not None
        if (
            answer
            and (called_tool or not required_tool)
            and _answer_is_valid(question, answer, evidence)
            and (
                not any(call["name"] in {"list_category", "list_catalog"} for call in calls)
                or prices_grounded(answer, "\n".join(results))
            )
        ):
            metadata["path"] = "tools"
            metadata["grounding_evidence"] = "\n".join(results)
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
    return (
        answer_text if prices_grounded(answer_text, evidence.text) else local_answer("", evidence)
    )
