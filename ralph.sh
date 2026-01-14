#!/bin/bash
# Research-Ralph - Autonomous research scouting agent loop
# Usage: ./ralph.sh [max_iterations] [--agent amp|claude|codex]

set -e

# Version
RALPH_VERSION="2.0.0"

# Help function
show_help() {
  echo "Research-Ralph v$RALPH_VERSION - Autonomous research scouting agent"
  echo ""
  echo "Usage: ./ralph.sh [max_iterations] [--agent amp|claude|codex]"
  echo ""
  echo "Options:"
  echo "  [max_iterations]    Maximum number of iterations (default: 10)"
  echo "  --agent <name>      AI agent to use: 'claude', 'amp', or 'codex' (default: claude)"
  echo "  -h, --help          Show this help message and exit"
  echo ""
  echo "Examples:"
  echo "  ./ralph.sh              # Run with defaults (claude, 10 iterations)"
  echo "  ./ralph.sh 5            # Run for max 5 iterations"
  echo "  ./ralph.sh --agent amp  # Use Amp instead of Claude"
  echo "  ./ralph.sh 20 --agent amp"
  echo ""
  echo "Workflow:"
  echo "  1. Create RRD: ./skill.sh rrd \"Research topic description\""
  echo "  2. Run research: ./ralph.sh [iterations]"
  echo "  3. Check results: cat progress.txt"
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
      if [[ -z "${2:-}" || "$2" == -* ]]; then
        echo "Error: --agent requires a value (claude, amp, or codex)"
        exit 1
      fi
      AGENT="$2"
      shift 2
      ;;
    *)
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
if [[ "$AGENT" != "claude" && "$AGENT" != "amp" && "$AGENT" != "codex" ]]; then
  echo "Error: Invalid agent '$AGENT'. Must be 'claude', 'amp', or 'codex'."
  exit 1
fi

# Verify CLI is installed before starting
if ! command -v "$AGENT" &> /dev/null; then
  echo "Error: '$AGENT' CLI not found in PATH."
  [[ "$AGENT" == "amp" ]] && echo "Install it from: https://ampcode.com"
  [[ "$AGENT" == "claude" ]] && echo "Install it from: https://claude.ai/code"
  [[ "$AGENT" == "codex" ]] && echo "Install it from: https://openai.com/codex"
  exit 1
fi

# Verify jq is installed (needed for parsing rrd.json)
if ! command -v jq &> /dev/null; then
  echo "Error: 'jq' not found in PATH."
  echo "Install it with: brew install jq (macOS) or apt install jq (Linux)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RRD_FILE="$SCRIPT_DIR/rrd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"

# Initialize or reset progress file
init_progress_file() {
  echo "# Research-Ralph Progress Log" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "" >> "$PROGRESS_FILE"
  echo "## Research Patterns" >> "$PROGRESS_FILE"
  echo "- (Patterns discovered during research will be added here)" >> "$PROGRESS_FILE"
  echo "" >> "$PROGRESS_FILE"
  echo "## Cross-Reference Insights" >> "$PROGRESS_FILE"
  echo "- (Connections between papers will be added here)" >> "$PROGRESS_FILE"
  echo "" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
}

# Agent invocation function
run_agent() {
  local prompt_file="$1"
  local prompt_content
  prompt_content=$(cat "$prompt_file") || return 1

  if [[ "$AGENT" == "amp" ]]; then
    echo "$prompt_content" | amp --dangerously-allow-all 2>&1 | tee /dev/stderr
  elif [[ "$AGENT" == "codex" ]]; then
    local last_message_file
    last_message_file="$(mktemp)"
    echo "$prompt_content" | codex exec --dangerously-bypass-approvals-and-sandbox --output-last-message "$last_message_file" - 2>&1 | tee /dev/stderr >/dev/null
    local codex_exit=${PIPESTATUS[1]}
    cat "$last_message_file"
    rm -f "$last_message_file"
    return $codex_exit
  else
    claude -p "$prompt_content" \
      --dangerously-skip-permissions \
      --allowedTools "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch" \
      2>&1 | tee /dev/stderr
  fi
}

# Archive previous run if branch changed
if [ -f "$RRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$RRD_FILE" 2>/dev/null || echo "")
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")

  if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
    # Archive the previous run
    DATE=$(date +%Y-%m-%d)
    # Strip "research/" prefix from branch name for folder
    FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^research/||')
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"

    echo "Archiving previous research: $LAST_BRANCH"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$RRD_FILE" ] && cp "$RRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    echo "   Archived to: $ARCHIVE_FOLDER"

    init_progress_file
  fi
fi

# Track current branch
if [ -f "$RRD_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$RRD_FILE" 2>/dev/null || echo "")
  if [ -n "$CURRENT_BRANCH" ]; then
    echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi
fi

# Initialize progress file if it doesn't exist
[[ ! -f "$PROGRESS_FILE" ]] && init_progress_file

# Verify RRD file exists before starting
if [[ ! -f "$RRD_FILE" ]]; then
  echo "Error: rrd.json not found at $RRD_FILE"
  echo "Create an RRD first using: ./skill.sh rrd \"Your research topic description\""
  exit 1
fi

# Validate RRD file is valid JSON
if ! jq empty "$RRD_FILE" 2>/dev/null; then
  echo "Error: rrd.json is not valid JSON"
  echo "Please check the file for syntax errors: $RRD_FILE"
  exit 1
fi

# Validate required fields exist
if ! jq -e '.project' "$RRD_FILE" >/dev/null 2>&1; then
  echo "Error: rrd.json missing required field 'project'"
  exit 1
fi

if ! jq -e '.requirements.target_papers' "$RRD_FILE" >/dev/null 2>&1; then
  echo "Error: rrd.json missing required field 'requirements.target_papers'"
  exit 1
fi

# Verify prompt.md exists
PROMPT_FILE="$SCRIPT_DIR/prompt.md"
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Error: prompt.md not found at $PROMPT_FILE"
  echo "This file contains the agent instructions and is required."
  exit 1
fi

# Display research info
PROJECT=$(jq -r '.project // "Unknown"' "$RRD_FILE")
PHASE=$(jq -r '.phase // "DISCOVERY"' "$RRD_FILE")
TARGET=$(jq -r '.requirements.target_papers // 0' "$RRD_FILE")
ANALYZED=$(jq -r '.statistics.total_analyzed // 0' "$RRD_FILE")

echo "Starting Research-Ralph v$RALPH_VERSION"
echo "  Agent: $AGENT"
echo "  Project: $PROJECT"
echo "  Phase: $PHASE"
echo "  Papers: $ANALYZED analyzed / $TARGET target"
echo "  Max iterations: $MAX_ITERATIONS"
echo ""

# Track consecutive failures
CONSECUTIVE_FAILURES=0
MAX_CONSECUTIVE_FAILURES=3

for i in $(seq 1 $MAX_ITERATIONS); do
  echo ""
  echo "======================================================="
  echo "  Research-Ralph Iteration $i of $MAX_ITERATIONS ($AGENT)"
  echo "======================================================="

  # Show current phase
  PHASE=$(jq -r '.phase // "DISCOVERY"' "$RRD_FILE" 2>/dev/null || echo "DISCOVERY")
  echo "  Phase: $PHASE"

  set +e
  OUTPUT=$(run_agent "$PROMPT_FILE")
  EXIT_CODE=$?
  set -e

  if [[ $EXIT_CODE -ne 0 ]]; then
    CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
    echo ""
    echo "Error: Agent '$AGENT' failed (exit code $EXIT_CODE)."
    echo "  Consecutive failures: $CONSECUTIVE_FAILURES/$MAX_CONSECUTIVE_FAILURES"
    [[ -n "$OUTPUT" ]] && echo "  Last 20 lines:" && echo "$OUTPUT" | tail -20

    # Classify error type for debugging
    if echo "$OUTPUT" | grep -qi "403\|Forbidden"; then
      echo "  Error type: HTTP 403 Forbidden (source block - try fallback sources)"
    elif echo "$OUTPUT" | grep -qi "429\|Too Many Requests\|rate.limit"; then
      echo "  Error type: Rate limit (429) - will retry with backoff"
    elif echo "$OUTPUT" | grep -qi "bot\|challenge\|captcha\|blocked"; then
      echo "  Error type: Bot challenge detected - use GitHub API instead"
    elif echo "$OUTPUT" | grep -qi "timeout\|timed.out"; then
      echo "  Error type: Request timeout - retry may help"
    elif echo "$OUTPUT" | grep -qi "network\|connection\|DNS"; then
      echo "  Error type: Network error - check connectivity"
    fi

    if [[ $CONSECUTIVE_FAILURES -ge $MAX_CONSECUTIVE_FAILURES ]]; then
      echo ""
      echo "Error: $MAX_CONSECUTIVE_FAILURES consecutive failures. Aborting."
      echo "Possible causes:"
      echo "  - Agent CLI not properly configured"
      echo "  - Network connectivity issues"
      echo "  - Authentication/API key problems"
      exit 1
    fi

    echo "  Retrying..."
    sleep 5
    continue
  fi

  # Reset on success
  CONSECUTIVE_FAILURES=0

  # Check for completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "Research-Ralph completed all research tasks!"
    echo ""
    # Show summary
    PRESENTED=$(jq -r '.statistics.total_presented // 0' "$RRD_FILE" 2>/dev/null || echo "0")
    REJECTED=$(jq -r '.statistics.total_rejected // 0' "$RRD_FILE" 2>/dev/null || echo "0")
    INSIGHTS=$(jq -r '.statistics.total_insights_extracted // 0' "$RRD_FILE" 2>/dev/null || echo "0")
    echo "Summary:"
    echo "  Papers presented: $PRESENTED"
    echo "  Papers rejected: $REJECTED"
    echo "  Insights extracted: $INSIGHTS"
    echo ""
    echo "See progress.txt for detailed findings."
    exit 0
  fi

  echo "Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "Research-Ralph reached max iterations ($MAX_ITERATIONS) without completing."
echo "Check progress.txt for current status."
echo "Run again with more iterations if needed."
exit 1
