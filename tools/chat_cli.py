"""Interactive chat loop that keeps recent turns as model context."""

from __future__ import annotations

import os
import sys

from agent_cli import print_response


def mode_description() -> str:
    endpoint = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
    if not endpoint:
        return "modo local (sem modelo configurado)"
    return f"modelo {os.getenv('OPENAI_MODEL') or 'lfm3-omni-2b'} em {endpoint}"


def interactive() -> None:
    print(f"Empório da Música, {mode_description()}. Digite 'sair' para encerrar.")
    history: list[dict[str, str]] = []
    previous = None
    while True:
        try:
            question = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.casefold() in {"sair", "exit", "quit", "tchau", "até mais", "ate mais"}:
            break
        if not question:
            continue
        try:
            answer, previous = print_response(question, "Loja: ", history, previous)
            history += [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ]
            history = history[-6:]
        except (OSError, StopIteration) as error:
            print(f"Não consegui consultar as fontes: {error}", file=sys.stderr)
