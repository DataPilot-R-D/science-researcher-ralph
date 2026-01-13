#!/bin/bash
# skill.sh - Run skills with either Claude Code or Amp
# Usage: ./skill.sh <skill-name> [task] [--agent amp|claude]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
AGENT="claude"

show_help() {
  echo "skill.sh - Run skills with either Claude Code or Amp"
  echo ""
  echo "Usage: ./skill.sh <skill-name> [task] [--agent amp|claude]"
  echo ""
  echo "Options:"
  echo "  --list           List available skills"
  echo "  --agent <name>   Agent to use: 'claude' or 'amp' (default: claude)"
  echo "  -h, --help       Show this help message"
  echo ""
  echo "Examples:"
  echo "  ./skill.sh prd \"Create a PRD for login feature\""
  echo "  ./skill.sh ralph tasks/prd-login.md"
  echo "  ./skill.sh prd \"Create a PRD\" --agent amp"
}

list_skills() {
  echo "Available skills:"
  for dir in "$SKILLS_DIR"/*/; do
    if [[ -f "$dir/SKILL.md" ]]; then
      name=$(basename "$dir")
      # Extract description from frontmatter
      desc=$(sed -n '/^description:/p' "$dir/SKILL.md" | sed -E 's/description: *"?//' | sed -E 's/"?$//' | head -c 60)
      echo "  $name - $desc..."
    fi
  done
}

# Parse arguments
SKILL_NAME=""
TASK=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    --list)
      list_skills
      exit 0
      ;;
    --agent)
      if [[ -z "${2:-}" || "$2" == -* ]]; then
        echo "Error: --agent requires a value (claude or amp)"
        exit 1
      fi
      AGENT="$2"
      shift 2
      ;;
    -*)
      echo "Error: Unknown option '$1'. Use --help for usage."
      exit 1
      ;;
    *)
      if [[ -z "$SKILL_NAME" ]]; then
        SKILL_NAME="$1"
      else
        TASK="$1"
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

# Validate skill name provided
if [[ -z "$SKILL_NAME" ]]; then
  echo "Error: Skill name required"
  echo ""
  show_help
  exit 1
fi

# Validate skill exists
SKILL_FILE="$SKILLS_DIR/$SKILL_NAME/SKILL.md"
if [[ ! -f "$SKILL_FILE" ]]; then
  echo "Error: Skill '$SKILL_NAME' not found"
  echo ""
  list_skills
  exit 1
fi

# Verify CLI is installed
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

# Extract skill content (skip YAML frontmatter)
# This handles the --- delimited frontmatter at the start of the file
SKILL_CONTENT=$(awk '
  BEGIN { in_frontmatter=0; found_end=0 }
  /^---$/ && NR==1 { in_frontmatter=1; next }
  /^---$/ && in_frontmatter { in_frontmatter=0; found_end=1; next }
  !in_frontmatter && found_end { print }
' "$SKILL_FILE")

# Build full prompt
FULL_PROMPT="$SKILL_CONTENT"
if [[ -n "$TASK" ]]; then
  FULL_PROMPT="$FULL_PROMPT

---

## Task

$TASK"
fi

echo "Running skill '$SKILL_NAME' with $AGENT..."
echo ""

# Run with appropriate agent
set +e
if [[ "$AGENT" == "amp" ]]; then
  echo "$FULL_PROMPT" | amp --dangerously-allow-all
  EXIT_CODE=$?
else
  claude -p "$FULL_PROMPT" \
    --dangerously-skip-permissions \
    --allowedTools "Bash,Read,Edit,Write,Grep,Glob"
  EXIT_CODE=$?
fi
set -e

if [[ $EXIT_CODE -ne 0 ]]; then
  echo ""
  echo "ERROR: Skill '$SKILL_NAME' failed with $AGENT (exit code: $EXIT_CODE)"
  echo "Check if '$AGENT' CLI is installed and authenticated."
  exit $EXIT_CODE
fi
