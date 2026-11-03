"""Resolve repository data paths without relying on Unicode filename spelling."""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = "Desafio Técnico AI Engineer 2026"


def _normalized_name(name: str) -> str:
    return unicodedata.normalize("NFC", name)


def resolve_child(parent: Path, expected_name: str) -> Path:
    expected = _normalized_name(expected_name)
    matches = [path for path in parent.iterdir() if _normalized_name(path.name) == expected]
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one entry named {expected_name!r} under {parent}, found {len(matches)}"
        )
    return matches[0]


def resolve_data_dir() -> Path:
    return resolve_child(ROOT, DATA_DIRECTORY) / "data"


def resolve_policy_pdf() -> Path:
    data_dir = resolve_data_dir()
    matches = [
        path
        for path in data_dir.iterdir()
        if path.is_file() and "pol" in _normalized_name(path.name).casefold()
    ]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one policy PDF under {data_dir}, found {len(matches)}")
    return matches[0]


def resolve_challenge_pdf() -> Path:
    challenge_dir = resolve_child(ROOT, DATA_DIRECTORY)
    return resolve_child(challenge_dir, "desafio_tecnico_ai_eng_artefact.pdf")


if __name__ == "__main__":
    resolvers = {
        "data-dir": resolve_data_dir,
        "policy-pdf": resolve_policy_pdf,
        "challenge-pdf": resolve_challenge_pdf,
    }
    try:
        print(resolvers[sys.argv[1]]())
    except (IndexError, KeyError, FileNotFoundError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
