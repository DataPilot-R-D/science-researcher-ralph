#!/bin/bash
# Restore AGENTS.md and CLAUDE.md from docs-baseline/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASELINE_DIR="$SCRIPT_DIR/docs-baseline"

restore_file() {
  local name="$1"
  local src="$BASELINE_DIR/$name"
  local dst="$SCRIPT_DIR/$name"

  if [[ ! -f "$src" ]]; then
    echo "Error: Missing baseline file: $src" >&2
    exit 1
  fi

  cp "$src" "$dst"
}

restore_file "AGENTS.md"
restore_file "CLAUDE.md"

echo "Restored AGENTS.md and CLAUDE.md from: $BASELINE_DIR"
