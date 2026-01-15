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
TEMP_DIR=""
if [[ "$SKILL_NAME" == "rrd" ]]; then
  if [[ -z "$TASK" ]]; then
    echo "Error: RRD skill requires a task description"
    echo "Usage: ./skill.sh rrd \"Your research topic description\""
    exit 1
  fi

  RESEARCH_DATE=$(date +%Y-%m-%d)

  # Create temp directory (will be renamed after agent generates topic slug)
  TEMP_NAME="rrd-temp-$$-$(date +%s)"
  TEMP_DIR="$SCRIPT_DIR/researches/$TEMP_NAME"
  mkdir -p "$TEMP_DIR"

  # Add folder path to prompt so agent knows where to save
  FULL_PROMPT="$FULL_PROMPT

---

## Output Location

Save all files to the research folder: $TEMP_DIR/
- Save rrd.json to: $TEMP_DIR/rrd.json
- progress.txt will be created automatically by ralph.sh

**Note:** The \`project\` field in rrd.json will be used for the directory name, so make it concise and descriptive (3-6 words)."
fi

echo "Running skill '$SKILL_NAME' with $AGENT..."
echo ""

# Run with appropriate agent and capture output
if [[ "$AGENT" == "amp" ]]; then
  OUTPUT=$(echo "$FULL_PROMPT" | amp --dangerously-allow-all 2>&1) || true
  echo "$OUTPUT"
elif [[ "$AGENT" == "codex" ]]; then
  OUTPUT=$(echo "$FULL_PROMPT" | codex exec --dangerously-bypass-approvals-and-sandbox - 2>&1) || true
  echo "$OUTPUT"
else
  OUTPUT=$(claude -p "$FULL_PROMPT" \
    --dangerously-skip-permissions \
    --allowedTools "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch" 2>&1) || true
  echo "$OUTPUT"
fi

# For rrd skill: rename temp directory to final name based on project name from rrd.json
if [[ "$SKILL_NAME" == "rrd" && -d "$TEMP_DIR" ]]; then
  RESEARCH_NAME=""

  # Try to extract project name from rrd.json (most reliable - agent always generates this)
  if [[ -f "$TEMP_DIR/rrd.json" ]] && command -v jq &> /dev/null; then
    # Extract project field, remove "Research: " prefix, convert to kebab-case
    PROJECT_NAME=$(jq -r '.project // empty' "$TEMP_DIR/rrd.json" 2>/dev/null | sed 's/^Research: //')
    if [[ -n "$PROJECT_NAME" ]]; then
      RESEARCH_NAME=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | cut -c1-50)
    fi
  fi

  # Fallback: truncate task description (convert newlines to spaces first)
  if [[ -z "$RESEARCH_NAME" ]]; then
    RESEARCH_NAME=$(printf '%s' "$TASK" | tr '\n' ' ' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | cut -c1-40)
  fi

  RESEARCH_DIR="$SCRIPT_DIR/researches/${RESEARCH_NAME}-${RESEARCH_DATE}"

  # Rename temp to final (handle collision by appending number)
  if [[ -d "$RESEARCH_DIR" ]]; then
    i=1
    while [[ -d "${RESEARCH_DIR}-$i" ]]; do ((i++)); done
    RESEARCH_DIR="${RESEARCH_DIR}-$i"
  fi

  mv "$TEMP_DIR" "$RESEARCH_DIR"

  # Update branchName in rrd.json to match new directory
  if [[ -f "$RESEARCH_DIR/rrd.json" ]]; then
    # Use jq if available
    if command -v jq &> /dev/null; then
      jq --arg bn "research/${RESEARCH_NAME}" '.branchName = $bn' "$RESEARCH_DIR/rrd.json" > "$RESEARCH_DIR/rrd.json.tmp" && mv "$RESEARCH_DIR/rrd.json.tmp" "$RESEARCH_DIR/rrd.json"
    fi
  fi

  echo ""
  echo "Research folder ready: $RESEARCH_DIR"
  echo ""
  echo "Next step:"
  echo "  ./ralph.sh $RESEARCH_DIR [-p papers] [-i iterations]"
fi

exit 0
