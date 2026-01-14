#!/bin/bash
# skill.sh - Run skills with Claude Code, Amp, or Codex
# Usage: ./skill.sh <skill-name> [task] [--agent amp|claude|codex]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
AGENT="claude"

show_help() {
  echo "skill.sh - Run skills with either Claude Code or Amp"
  echo ""
  echo "Usage: ./skill.sh <skill-name> [task] [--agent amp|claude|codex]"
  echo ""
  echo "Options:"
  echo "  --list           List available skills"
  echo "  --agent <name>   Agent to use: 'claude', 'amp', or 'codex' (default: claude)"
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
        echo "Error: --agent requires a value (claude, amp, or codex)"
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
if [[ "$AGENT" != "claude" && "$AGENT" != "amp" && "$AGENT" != "codex" ]]; then
  echo "Error: Invalid agent '$AGENT'. Must be 'claude', 'amp', or 'codex'."
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
if ! command -v "$AGENT" &> /dev/null; then
  echo "Error: '$AGENT' CLI not found in PATH."
  [[ "$AGENT" == "amp" ]] && echo "Install it from: https://ampcode.com"
  [[ "$AGENT" == "claude" ]] && echo "Install it from: https://claude.ai/code"
  [[ "$AGENT" == "codex" ]] && echo "Install it from: https://openai.com/codex"
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

# Special handling for rrd skill: create research folder
RESEARCH_DIR=""
if [[ "$SKILL_NAME" == "rrd" ]]; then
  if [[ -z "$TASK" ]]; then
    echo "Error: RRD skill requires a task description"
    echo "Usage: ./skill.sh rrd \"Your research topic description\""
    exit 1
  fi

  # Generate folder name from task description
  # Format: researches/{sanitized-name}-{date}
  RESEARCH_NAME=$(echo "$TASK" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | cut -c1-40)
  RESEARCH_DATE=$(date +%Y-%m-%d)
  RESEARCH_DIR="$SCRIPT_DIR/researches/${RESEARCH_NAME}-${RESEARCH_DATE}"

  mkdir -p "$RESEARCH_DIR"
  echo "Created research folder: $RESEARCH_DIR"
  echo ""

  # Add folder path to prompt so agent knows where to save
  FULL_PROMPT="$FULL_PROMPT

---

## Output Location

Save all files to the research folder: $RESEARCH_DIR/
- Save rrd.json to: $RESEARCH_DIR/rrd.json
- progress.txt will be created automatically by ralph.sh"
fi

echo "Running skill '$SKILL_NAME' with $AGENT..."
echo ""

# Run with appropriate agent
if [[ "$AGENT" == "amp" ]]; then
  echo "$FULL_PROMPT" | amp --dangerously-allow-all
elif [[ "$AGENT" == "codex" ]]; then
  echo "$FULL_PROMPT" | codex exec --dangerously-bypass-approvals-and-sandbox -
else
  claude -p "$FULL_PROMPT" \
    --dangerously-skip-permissions \
    --allowedTools "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch"
fi

# Show next steps for rrd skill
if [[ "$SKILL_NAME" == "rrd" && -n "$RESEARCH_DIR" ]]; then
  echo ""
  echo "Research folder ready: $RESEARCH_DIR"
  echo ""
  echo "Next step:"
  echo "  ./ralph.sh $RESEARCH_DIR [max_iterations]"
fi

exit 0
