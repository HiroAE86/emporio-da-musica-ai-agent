#!/usr/bin/env sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_root"

max_file_lines=${PYTHON_MAX_FILE_LINES:-300}
find tools scripts -type f -name '*.py' -exec sh -c '
limit=$1
shift
for file do
    lines=$(wc -l < "$file")
    if [ "$lines" -gt "$limit" ]; then
        printf "File exceeds %s lines: %s (%s lines)\n" "$limit" "$file" "$lines" >&2
        exit 1
    fi
done
' sh "$max_file_lines" {} +

if command -v ruff >/dev/null 2>&1; then
    ruff check tools scripts
    ruff format --check tools scripts
elif command -v uvx >/dev/null 2>&1; then
    uvx ruff check tools scripts
    uvx ruff format --check tools scripts
else
    printf '%s\n' 'Install Ruff or uv to run the Python checker.' >&2
    exit 127
fi
