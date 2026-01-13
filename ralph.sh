#!/bin/bash
# Ralph - Long-running AI agent loop
# Usage: ./ralph.sh [max_iterations] [--agent amp|claude]

set -e

# Version
RALPH_VERSION="1.0.0"

# Help function
show_help() {
  echo "Ralph v$RALPH_VERSION - Autonomous AI agent loop"
  echo ""
  echo "Usage: ./ralph.sh [max_iterations] [--agent amp|claude]"
  echo ""
  echo "Options:"
  echo "  [max_iterations]    Maximum number of iterations (default: 10)"
  echo "  --agent <name>      AI agent to use: 'claude' or 'amp' (default: claude)"
  echo "  -h, --help          Show this help message and exit"
  echo ""
  echo "Examples:"
  echo "  ./ralph.sh              # Run with defaults (claude, 10 iterations)"
  echo "  ./ralph.sh 5            # Run for max 5 iterations"
  echo "  ./ralph.sh --agent amp  # Use Amp instead of Claude"
  echo "  ./ralph.sh 20 --agent amp"
}

# Default values
MAX_ITERATIONS=10
AGENT="claude"  # Default to Claude Code CLI

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    --agent)
      # Fix 1: Validate --agent value exists
      if [[ -z "${2:-}" || "$2" == -* ]]; then
        echo "Error: --agent requires a value (claude or amp)"
        exit 1
      fi
      AGENT="$2"
      shift 2
      ;;
    *)
      # Fix 2: Error on unknown options, warn on unexpected args
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        MAX_ITERATIONS="$1"
      elif [[ "$1" == -* ]]; then
        echo "Error: Unknown option '$1'. Use --help for usage."
        exit 1
      else
        echo "Warning: Ignoring unexpected argument '$1'"
      fi
      shift
      ;;
  esac
done

# Validate agent
if [[ "$AGENT" != "claude" && "$AGENT" != "amp" ]]; then
  echo "Error: Invalid agent '$AGENT'. Must be 'claude' or 'amp'."
  exit 1
fi

# Fix 5: Verify CLI is installed before starting
CLI_CMD="claude"
[[ "$AGENT" == "amp" ]] && CLI_CMD="amp"

if ! command -v "$CLI_CMD" &> /dev/null; then
  echo "Error: '$CLI_CMD' CLI not found in PATH."
  if [[ "$AGENT" == "amp" ]]; then
    echo "Install it from: https://ampcode.com"
  else
    echo "Install it from: https://claude.ai/code"
  fi
  exit 1
fi

# Verify jq is installed (needed for parsing prd.json)
if ! command -v jq &> /dev/null; then
  echo "Error: 'jq' not found in PATH."
  echo "Install it with: brew install jq (macOS) or apt install jq (Linux)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"

# Agent invocation function
run_agent() {
  local prompt_file="$1"

  # Fix 4: Validate prompt file exists
  if [[ ! -f "$prompt_file" ]]; then
    echo "ERROR: Prompt file not found: $prompt_file" >&2
    return 1
  fi

  if [[ ! -r "$prompt_file" ]]; then
    echo "ERROR: Prompt file not readable: $prompt_file" >&2
    return 1
  fi

  if [[ "$AGENT" == "amp" ]]; then
    cat "$prompt_file" | amp --dangerously-allow-all 2>&1 | tee /dev/stderr
  else
    # Claude Code CLI
    claude -p "$(cat "$prompt_file")" \
      --dangerously-skip-permissions \
      --allowedTools "Bash,Read,Edit,Write,Grep,Glob" \
      2>&1 | tee /dev/stderr
  fi
}

# Archive previous run if branch changed
if [ -f "$PRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")

  if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
    # Archive the previous run
    DATE=$(date +%Y-%m-%d)
    # Strip "ralph/" prefix from branch name for folder
    FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^ralph/||')
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"

    echo "Archiving previous run: $LAST_BRANCH"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$PRD_FILE" ] && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    echo "   Archived to: $ARCHIVE_FOLDER"

    # Reset progress file for new run
    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi
fi

# Track current branch
if [ -f "$PRD_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  if [ -n "$CURRENT_BRANCH" ]; then
    echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi
fi

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# Ralph Progress Log" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
fi

# Verify PRD file exists before starting
if [[ ! -f "$PRD_FILE" ]]; then
  echo "ERROR: prd.json not found at $PRD_FILE"
  echo "Create a PRD first using: ./skill.sh prd \"Your feature description\""
  exit 1
fi

echo "Starting Ralph v$RALPH_VERSION - Agent: $AGENT, Max iterations: $MAX_ITERATIONS"

for i in $(seq 1 $MAX_ITERATIONS); do
  echo ""
  echo "═══════════════════════════════════════════════════════"
  echo "  Ralph Iteration $i of $MAX_ITERATIONS ($AGENT)"
  echo "═══════════════════════════════════════════════════════"

  # Fix 3: Handle agent failures properly instead of || true
  set +e
  OUTPUT=$(run_agent "$SCRIPT_DIR/prompt.md")
  EXIT_CODE=$?
  set -e

  if [[ $EXIT_CODE -ne 0 ]]; then
    echo ""
    echo "ERROR: Agent '$AGENT' failed with exit code $EXIT_CODE"
    echo "Check if '$AGENT' CLI is installed and authenticated."
    if [[ -n "$OUTPUT" ]]; then
      echo "--- Agent output (last 50 lines) ---"
      echo "$OUTPUT" | tail -50
      echo "--- End of agent output ---"
    fi
    echo "Continuing to next iteration..."
    sleep 2
    continue
  fi

  # Check for completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "Ralph completed all tasks!"
    echo "Completed at iteration $i of $MAX_ITERATIONS"
    exit 0
  fi

  echo "Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
echo "Check $PROGRESS_FILE for status."
exit 1
