"""Run source-grounded conversational scenarios and write reviewable reports."""

from __future__ import annotations

import contextlib
import csv
import getpass
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from unittest.mock import patch

import tool_calling
from agent_cli import PRODUCTS, print_response
from project_paths import ROOT
from qa_report import report

QA = ROOT / "qa"


def product_prices() -> set[int]:
    with PRODUCTS.open(encoding="utf-8-sig", newline="") as stream:
        return {
            round(float(row["price_brl"].replace(",", ".")) * 100) for row in csv.DictReader(stream)
        }


def customer_pii() -> set[str]:
    values = set()
    for path in PRODUCTS.parent.glob("*customers.csv"):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                values.update(value.strip() for value in row.values() if value and value.strip())
    return values


def amounts(text: str) -> list[tuple[str, int]]:
    found = []
    text = text.translate(str.maketrans({"\u00a0": " ", "\u2007": " ", "\u202f": " "}))
    for value in re.findall(r"R\$\s*([\d.]+(?:,\d{1,2})?)", text):
        found.append((value, round(float(value.replace(".", "").replace(",", ".")) * 100)))
    return found


def check_one(
    key: str, terms: object, answer: str, evidence: str, prices: set[int], pii: set[str]
) -> list[dict]:
    normalized, output = answer.casefold(), []

    def add(name: str, passed: bool, reason: str) -> None:
        output.append({"check": name, "passed": bool(passed), "reason": reason})

    if key == "must_contain":
        for mode, items in terms.items():
            hits = [item for item in items if item.casefold() in normalized]
            add(
                key + "." + mode,
                bool(hits) if mode == "any" else len(hits) == len(items),
                f"found {hits}; expected {items}",
            )
    elif key == "must_not_contain":
        misses = [item for item in terms if item.casefold() not in normalized]
        add(key, len(misses) == len(terms), f"absent {misses}; forbidden {terms}")
    elif key == "category":
        passed = (
            _overview_counts_match(answer, evidence)
            if terms == "overview"
            else terms.casefold() in normalized
        )
        add(key, passed, f"expected category phrase {terms!r}")
    elif key == "max_price":
        over = [value for value, cents in amounts(answer) if cents > round(float(terms) * 100)]
        add(key, not over, f"amounts above {terms}: {over}")
    elif key == "prices_grounded":
        grounded = prices | {cents for _, cents in amounts(evidence)}
        unknown = [value for value, cents in amounts(answer) if cents not in grounded]
        add(key, not unknown, f"ungrounded amounts: {unknown}")
    elif key == "no_pii":
        leaks = [value for value in pii if len(value) > 4 and value.casefold() in normalized]
        add(key, not leaks, f"customer values found: {leaks}")
    elif key == "refuses":
        phrases = (
            "não é possível",
            "nao e possivel",
            "não posso",
            "nao posso",
            "não consigo",
            "nao consigo",
            "não tenho acesso",
            "nao tenho acesso",
            "posso ajudar com instrumentos",
            "fora do escopo",
        )
        refusal = any(term in normalized for term in phrases)
        add(key, refusal, "recognized refusal" if refusal else "no refusal phrase detected")
    return output


def _overview_counts_match(answer: str, evidence: str) -> bool:
    expected = re.findall(r"^([^:]+): (\d+) produto", evidence, re.MULTILINE)
    clean = re.sub(r"[*`_]", "", answer.casefold())
    variants = {
        "violões": "viol(?:ão|oes|ões)",
        "guitarras": "guitarr(?:a|as)",
        "baixos": "baix(?:o|os)",
        "baterias": "bateri(?:a|as)",
        "teclados": "teclad(?:o|os)",
        "pianos": "pian(?:o|os)",
        "ukuleles": "ukulele(?:s)?",
    }
    for label, count in expected:
        label_pattern = variants.get(label, re.escape(label))
        count_pattern = rf"(?:[|:]\s*{count}\b|\(\s*{count}\s+(?:produtos?|modelos?|opções?)\))"
        if count == "1":
            count_pattern = rf"(?:{count_pattern}|apenas um modelo|um único modelo)"
        lines = [line for line in clean.splitlines() if re.search(label_pattern, line)]
        if not any(re.search(count_pattern, line) for line in lines):
            return False
    return bool(expected)


def checks(
    answer: str, expected: dict, prices: set[int], pii: set[str], evidence: str = ""
) -> list[dict]:
    return [
        check
        for key, terms in expected.items()
        for check in check_one(key, terms, answer, evidence, prices, pii)
    ]


def run(scenarios: list[dict]) -> tuple[list[dict], dict]:
    prices, pii = product_prices(), customer_pii()
    records = []
    for scenario in scenarios:
        history: list[dict[str, str]] = []
        previous = None
        turns = []
        for turn in scenario["turns"]:
            calls: list[dict] = []
            metadata: dict = {}
            original_tool_result = tool_calling._tool_result

            def capture(
                call: dict, calls: list = calls, original: object = original_tool_result
            ) -> str:
                function = call.get("function", {})
                try:
                    arguments = json.loads(function.get("arguments", "{}"))
                except (ValueError, TypeError):
                    arguments = {}
                calls.append({"name": function.get("name", "unknown"), "arguments": arguments})
                return original(call)

            inputs = iter(turn.get("order_inputs", []))
            mode = (
                "offline"
                if not os.getenv("OPENAI_BASE_URL")
                else (
                    "tools"
                    if os.getenv("AGENT_TOOLS", "1") != "0"
                    and os.getenv("AGENT_TOOL_STRATEGY", "auto") != "preretrieve"
                    else "legacy"
                )
            )
            started = time.monotonic()
            with (
                patch.dict(os.environ, {"ORDER_DATA_DIR": str(ROOT / "examples" / "fixtures")}),
                patch.object(tool_calling, "_tool_result", capture),
                patch(
                    "builtins.input", side_effect=lambda *_, input_iter=inputs: next(input_iter, "")
                ),
                patch.object(
                    getpass,
                    "getpass",
                    side_effect=lambda *_, input_iter=inputs: next(input_iter, ""),
                ),
                open(os.devnull, "w") as sink,
                contextlib.redirect_stdout(sink),
            ):
                answer, evidence = print_response(
                    turn["user"], history=history, previous=previous, metadata=metadata
                )
            elapsed = time.monotonic() - started
            history.extend(
                (
                    {"role": "user", "content": turn["user"]},
                    {"role": "assistant", "content": answer},
                )
            )
            history = history[-6:]
            previous = evidence
            result = checks(
                answer, turn.get("expect", {}), prices, pii, evidence.text if evidence else ""
            )
            expected_tools = turn.get("expect", {}).get("tools_called")
            if expected_tools is not None and mode == "tools":
                result.append(
                    {
                        "check": "tools_called",
                        "passed": any(call["name"] in expected_tools for call in calls),
                        "reason": f"expected any of {expected_tools}; got {calls}",
                    }
                )
            source_line = None
            if evidence:
                row = re.search(r"^CSV row: (\d+)$", evidence.text, re.MULTILINE)
                source_line = int(row.group(1)) if row else None
            turns.append(
                {
                    "question": turn["user"],
                    "answer": answer,
                    "source": evidence.source if evidence else None,
                    "source_line": source_line,
                    "mode": mode,
                    "path": metadata.get("path", "local"),
                    "tool_calls": calls,
                    "latency_seconds": round(elapsed, 3),
                    "checks": result,
                }
            )
        records.append(
            {
                "id": scenario["id"],
                "turns": turns,
                "passed": all(check["passed"] for turn in turns for check in turn["checks"]),
            }
        )
    total = sum(len(turn["checks"]) for item in records for turn in item["turns"])
    passed = sum(
        check["passed"] for item in records for turn in item["turns"] for check in turn["checks"]
    )
    return records, {
        "scenarios": len(records),
        "passed_scenarios": sum(item["passed"] for item in records),
        "checks": total,
        "passed_checks": passed,
        "pass_rate": round(100 * passed / total, 1) if total else 100,
        "store_turns": sum(
            1
            for item in records
            for turn in item["turns"]
            if turn["source"] or turn["tool_calls"] or turn["path"] == "preretrieve"
        ),
        "tool_call_turns": sum(
            1 for item in records for turn in item["turns"] if turn["tool_calls"]
        ),
        "model_led_tool_turns": sum(
            1
            for item in records
            for turn in item["turns"]
            if turn["path"] == "tools" and turn["tool_calls"]
        ),
    }


def main() -> int:
    scenarios = json.loads((QA / "scenarios.json").read_text(encoding="utf-8"))
    selected = os.getenv("QA_SCENARIO")
    if selected:
        scenarios = [item for item in scenarios if selected in item["id"]]
        if not scenarios:
            raise SystemExit(f"No QA scenario matches {selected!r}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    records, summary = run(scenarios)
    md, jsonl = report(records, summary, stamp)
    print(
        f"QA: {summary['passed_scenarios']}/{summary['scenarios']} scenarios; {summary['passed_checks']}/{summary['checks']} checks ({summary['pass_rate']}%)"
    )
    print(f"Reports: {md} and {jsonl}")
    return int(summary["passed_checks"] != summary["checks"])


if __name__ == "__main__":
    sys.exit(main())
