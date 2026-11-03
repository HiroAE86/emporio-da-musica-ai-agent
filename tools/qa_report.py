"""Write QA transcripts and JSONL records."""

import json
import os
from pathlib import Path

from project_paths import ROOT

QA = ROOT / "qa"


def report(records: list[dict], summary: dict, stamp: str) -> tuple[Path, Path]:
    out = Path(os.getenv("QA_OUT", str(QA / "results")))
    out.mkdir(parents=True, exist_ok=True)
    md, jsonl = out / f"qa-{stamp}.md", out / f"qa-{stamp}.jsonl"
    lines = [
        "# Conversational QA",
        "",
        f"**{summary['passed_scenarios']}/{summary['scenarios']} scenarios pass; {summary['passed_checks']}/{summary['checks']} checks pass ({summary['pass_rate']}%).**",
        "",
        "| Scenario | Result |",
        "|---|---|",
    ]
    lines += [f"| {item['id']} | {'PASS' if item['passed'] else 'FAIL'} |" for item in records]
    lines += [
        "",
        f"Totals: {summary['passed_scenarios']}/{summary['scenarios']} scenarios, {summary['passed_checks']}/{summary['checks']} checks ({summary['pass_rate']}%).",
        f"Tool calls made: {summary['tool_call_turns']} turns ({round(100 * summary['tool_call_turns'] / max(1, summary['store_turns']), 1)}% of store turns).",
        f"Answered via model-led tool calls: {summary['model_led_tool_turns']} turns ({round(100 * summary['model_led_tool_turns'] / max(1, summary['store_turns']), 1)}% of store turns).",
        "",
        "## Transcripts",
        "",
    ]
    for item in records:
        lines += [f"### {item['id']} — {'PASS' if item['passed'] else 'FAIL'}", ""]
        for turn in item["turns"]:
            lines += [
                f"**User:** {turn['question']}",
                "",
                f"**Assistant:** {turn['answer']}",
                "",
                f"Mode: {turn['mode']} · Path: {turn['path']} · Source: {turn['source'] or 'none'}{':' + str(turn['source_line']) if turn['source_line'] else ''} · Tools: {json.dumps(turn['tool_calls'], ensure_ascii=False)} · Latency: {turn['latency_seconds']}s",
                "",
            ]
            lines += [
                f"- {'✅' if check['passed'] else '❌'} `{check['check']}` — {check['reason']}"
                for check in turn["checks"]
            ] + [""]
    md.write_text("\n".join(lines), encoding="utf-8")
    with jsonl.open("w", encoding="utf-8") as stream:
        for item in records:
            for turn in item["turns"]:
                stream.write(
                    json.dumps({"scenario": item["id"], **turn}, ensure_ascii=False) + "\n"
                )
    return md, jsonl
