#!/bin/sh
# Reprint the source challenge PDF as text for review against docs/README.md.
set -eu
pdf='Desafio Técnico AI Engineer 2026/desafio_tecnico_ai_eng_artefact.pdf'
if [ ! -f "$pdf" ]; then
  echo "Challenge PDF not found: $pdf" >&2
  exit 1
fi
pdftotext -layout "$pdf" -
