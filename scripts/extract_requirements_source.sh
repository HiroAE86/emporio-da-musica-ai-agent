#!/bin/sh
# Reprint the source challenge PDF as text for review against docs/README.md.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
pdf=$(python3 "$root/tools/project_paths.py" challenge-pdf)
pdftotext -layout "$pdf" -
