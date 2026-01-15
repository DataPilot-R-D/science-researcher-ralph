#!/bin/bash
# Research-Ralph - Autonomous research scouting agent loop
# Usage: ./ralph.sh <research_folder> [options]
#        ./ralph.sh --list
#        ./ralph.sh --status <research_folder>
#        ./ralph.sh --reset <research_folder>

set -e

# Version
RALPH_VERSION="3.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
  echo "Research-Ralph v$RALPH_VERSION - Autonomous research scouting agent"
  echo ""
  echo "Usage: ./ralph.sh <research_folder> [options]"
  echo "       ./ralph.sh --list"
  echo "       ./ralph.sh --status <research_folder>"
  echo "       ./ralph.sh --reset <research_folder>"
  echo ""
  echo "Commands:"
  echo "  --list                List all research projects with status"
  echo "  --status <folder>     Show detailed status of a research project"
  echo "  --reset <folder>      Reset research to DISCOVERY phase"
  echo ""
  echo "Run Options:"
  echo "  -p, --papers <N>      Target papers count (auto-sets iterations to N+5)"
  echo "  -i, --iterations <N>  Override max iterations (default: auto-calculated)"
  echo "  --agent <name>        AI agent: 'claude', 'amp', or 'codex' (default: claude)"
  echo "  --force               Force operations (e.g., override target_papers)"
  echo "  -h, --help            Show this help message"
  echo ""
  echo "Examples:"
  echo "  ./ralph.sh --list                                        # List all researches"
  echo "  ./ralph.sh --status researches/robotics-2026-01-14       # Check status"
  echo "  ./ralph.sh --reset researches/robotics-2026-01-14        # Reset to start"
  echo "  ./ralph.sh researches/robotics-2026-01-14                # Run research"
  echo "  ./ralph.sh researches/robotics-2026-01-14 -p 30          # 30 papers"
  echo "  ./ralph.sh researches/robotics-2026-01-14 --agent amp    # Use Amp agent"
  echo ""
  echo "Workflow:"
  echo "  1. Create research: ./skill.sh rrd \"Research topic description\""
  echo "  2. Run research:    ./ralph.sh researches/<folder-name>"
  echo "  3. Check status:    ./ralph.sh --status researches/<folder-name>"
  echo "  4. View results:    cat researches/<folder-name>/progress.txt"
}

# Default values
MAX_ITERATIONS=10
ITERATIONS_EXPLICIT=false  # Track if user explicitly set iterations
AGENT="claude"  # Default to Claude Code CLI
RESEARCH_DIR=""
TARGET_PAPERS=""  # Empty = use rrd.json value
FORCE_FLAG=false  # Force operations like target_papers override

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# COMMAND FUNCTIONS
# ============================================================================

# List all research projects with status
cmd_list() {
  echo -e "${BLUE}Research-Ralph v$RALPH_VERSION${NC} - Research Projects"
  echo ""

  if [[ ! -d "$SCRIPT_DIR/researches" ]]; then
    echo "No researches folder found."
    echo "Create one with: ./skill.sh rrd \"Your research topic\""
    exit 0
  fi

  local count=0
  for dir in "$SCRIPT_DIR/researches"/*/; do
    [[ ! -d "$dir" ]] && continue
    local name=$(basename "$dir")
    local rrd="$dir/rrd.json"

    if [[ -f "$rrd" ]]; then
      # Issue 6: Check if jq can parse the file first
      if ! jq empty "$rrd" 2>/dev/null; then
        printf "  %-40s ${RED}INVALID JSON${NC}\n" "$name"
        count=$((count + 1))  # Issue 12: Use safe increment
        continue
      fi

      local phase=$(jq -r '.phase // "UNKNOWN"' "$rrd")
      local target=$(jq -r '.requirements.target_papers // 0' "$rrd")
      local analyzed=$(jq -r '.statistics.total_analyzed // 0' "$rrd")
      local pending=$(jq '[.papers_pool[] | select(.status == "pending")] | length' "$rrd" 2>/dev/null || echo "?")

      # Color-code by phase
      case $phase in
        DISCOVERY) phase_color="${YELLOW}$phase${NC}" ;;
        ANALYSIS)  phase_color="${BLUE}$phase${NC}" ;;
        COMPLETE)  phase_color="${GREEN}$phase${NC}" ;;
        *)         phase_color="${RED}$phase${NC}" ;;
      esac

      printf "  %-40s %b  %s/%s analyzed, %s pending\n" "$name" "$phase_color" "$analyzed" "$target" "$pending"
      count=$((count + 1))  # Issue 12: Use safe increment
    else
      printf "  %-40s ${RED}NO RRD${NC}\n" "$name"
      count=$((count + 1))  # Issue 12: Use safe increment
    fi
  done

  if [[ $count -eq 0 ]]; then
    echo "No research projects found."
    echo "Create one with: ./skill.sh rrd \"Your research topic\""
  fi
  echo ""
  exit 0
}

# Show detailed status of a research project
cmd_status() {
  local folder="$1"

  # Resolve folder path
  if [[ -d "$folder" ]]; then
    RESEARCH_DIR="$folder"
  elif [[ -d "$SCRIPT_DIR/researches/$folder" ]]; then
    RESEARCH_DIR="$SCRIPT_DIR/researches/$folder"
  elif [[ -d "$SCRIPT_DIR/$folder" ]]; then
    RESEARCH_DIR="$SCRIPT_DIR/$folder"
  else
    echo -e "${RED}Error:${NC} Research folder not found: $folder"
    exit 1
  fi

  local rrd="$RESEARCH_DIR/rrd.json"
  if [[ ! -f "$rrd" ]]; then
    echo -e "${RED}Error:${NC} rrd.json not found in $RESEARCH_DIR"
    exit 1
  fi

  # Issue 7: Validate JSON before extracting values
  if ! jq empty "$rrd" 2>/dev/null; then
    echo -e "${RED}Error:${NC} rrd.json is corrupted or malformed"
    echo "  File: $rrd"
    echo "  Try: ./ralph.sh --reset $folder to start fresh"
    exit 1
  fi

  # Extract data (with fallbacks for jq failures - Issue 7, 10)
  local project=$(jq -r '.project // "Unknown"' "$rrd" 2>/dev/null || echo "Unknown")
  local phase=$(jq -r '.phase // "UNKNOWN"' "$rrd" 2>/dev/null || echo "UNKNOWN")
  local target=$(jq -r '.requirements.target_papers // 0' "$rrd" 2>/dev/null || echo "0")
  local pool=$(jq '.papers_pool | length' "$rrd" 2>/dev/null || echo "0")
  local analyzed=$(jq -r '.statistics.total_analyzed // 0' "$rrd" 2>/dev/null || echo "0")
  local presented=$(jq -r '.statistics.total_presented // 0' "$rrd" 2>/dev/null || echo "0")
  local rejected=$(jq -r '.statistics.total_rejected // 0' "$rrd" 2>/dev/null || echo "0")
  local pending=$(jq '[.papers_pool[] | select(.status == "pending")] | length' "$rrd" 2>/dev/null || echo "0")
  local analyzing=$(jq '[.papers_pool[] | select(.status == "analyzing")] | length' "$rrd" 2>/dev/null || echo "0")
  local insights=$(jq -r '.statistics.total_insights_extracted // 0' "$rrd" 2>/dev/null || echo "0")

  # Issue 10: Ensure target is a valid integer for division
  if ! [[ "$target" =~ ^[0-9]+$ ]]; then
    target=0
  fi
  if ! [[ "$analyzed" =~ ^[0-9]+$ ]]; then
    analyzed=0
  fi

  # Color-code phase
  case $phase in
    DISCOVERY) phase_display="${YELLOW}$phase${NC}" ;;
    ANALYSIS)  phase_display="${BLUE}$phase${NC}" ;;
    COMPLETE)  phase_display="${GREEN}$phase${NC}" ;;
    *)         phase_display="${RED}$phase${NC}" ;;
  esac

  echo -e "${BLUE}Research-Ralph v$RALPH_VERSION${NC} - Status Report"
  echo ""
  echo -e "  ${BLUE}Project:${NC}  $project"
  echo -e "  ${BLUE}Folder:${NC}   $RESEARCH_DIR"
  echo -e "  ${BLUE}Phase:${NC}    $phase_display"
  echo ""
  echo -e "  ${BLUE}Papers:${NC}"
  echo "    Target:    $target"
  echo "    In Pool:   $pool"
  echo "    Analyzed:  $analyzed"
  echo "    Presented: $presented"
  echo "    Rejected:  $rejected"
  echo "    Pending:   $pending"
  [[ "$analyzing" -gt 0 ]] && echo -e "    ${YELLOW}Analyzing: $analyzing (stuck - will be re-analyzed)${NC}"
  echo ""
  echo -e "  ${BLUE}Insights:${NC} $insights extracted"
  echo ""

  # Progress bar
  if [[ "$target" -gt 0 ]]; then
    local pct=$((analyzed * 100 / target))
    local filled=$((pct / 5))
    local empty=$((20 - filled))
    printf "  ${BLUE}Progress:${NC} ["
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' '-'
    printf "] %d%%\n" "$pct"
  fi
  echo ""

  # Recommendations
  if [[ "$phase" == "COMPLETE" ]]; then
    echo -e "  ${GREEN}✓ Research complete!${NC}"
    echo "    View report: cat $RESEARCH_DIR/research-report.md"
  elif [[ "$analyzing" -gt 0 ]]; then
    echo -e "  ${YELLOW}! Papers stuck in 'analyzing' status will be re-analyzed on next run${NC}"
  elif [[ "$pool" -lt "$target" && "$phase" == "ANALYSIS" ]]; then
    echo -e "  ${YELLOW}! Pool ($pool) < Target ($target) - will revert to DISCOVERY${NC}"
  fi
  echo ""
  exit 0
}

# Reset research to DISCOVERY phase (backs up rrd.json and progress.txt)
cmd_reset() {
  local folder="$1"

  # Resolve folder path
  if [[ -d "$folder" ]]; then
    RESEARCH_DIR="$folder"
  elif [[ -d "$SCRIPT_DIR/researches/$folder" ]]; then
    RESEARCH_DIR="$SCRIPT_DIR/researches/$folder"
  elif [[ -d "$SCRIPT_DIR/$folder" ]]; then
    RESEARCH_DIR="$SCRIPT_DIR/$folder"
  else
    echo -e "${RED}Error:${NC} Research folder not found: $folder"
    exit 1
  fi

  local rrd="$RESEARCH_DIR/rrd.json"
  if [[ ! -f "$rrd" ]]; then
    echo -e "${RED}Error:${NC} rrd.json not found in $RESEARCH_DIR"
    exit 1
  fi

  local timestamp=$(date +%Y%m%d_%H%M%S)

  # Create backup of rrd.json (Issue 1: verify success)
  local rrd_backup="$rrd.backup.$timestamp"
  if ! cp "$rrd" "$rrd_backup"; then
    echo -e "${RED}Error:${NC} Failed to create rrd.json backup"
    echo "  Check disk space and permissions: $RESEARCH_DIR"
    exit 1
  fi
  echo -e "${BLUE}Backup created:${NC} $rrd_backup"

  # Create backup of progress.txt (Issue 9: backup progress.txt too)
  local progress="$RESEARCH_DIR/progress.txt"
  if [[ -f "$progress" ]]; then
    local progress_backup="$progress.backup.$timestamp"
    if ! cp "$progress" "$progress_backup"; then
      echo -e "${RED}Error:${NC} Failed to create progress.txt backup"
      exit 1
    fi
    echo -e "${BLUE}Backup created:${NC} $progress_backup"
  fi

  # Reset rrd.json (Issue 2: verify jq success)
  if ! jq '
    .phase = "DISCOVERY" |
    .papers_pool = [] |
    .insights = [] |
    .statistics.total_discovered = 0 |
    .statistics.total_analyzed = 0 |
    .statistics.total_presented = 0 |
    .statistics.total_rejected = 0 |
    .statistics.total_insights_extracted = 0
  ' "$rrd" > "$rrd.tmp"; then
    echo -e "${RED}Error:${NC} Failed to reset rrd.json"
    rm -f "$rrd.tmp"
    exit 1
  fi

  # Verify output is valid JSON
  if ! jq empty "$rrd.tmp" 2>/dev/null; then
    echo -e "${RED}Error:${NC} Reset produced invalid JSON"
    rm -f "$rrd.tmp"
    exit 1
  fi

  mv "$rrd.tmp" "$rrd"

  # Reset progress.txt (with error checking)
  {
    echo "# Research-Ralph Progress Log"
    echo "Reset: $(date)"
    echo ""
    echo "## Research Patterns"
    echo "- (Patterns discovered during research will be added here)"
    echo ""
    echo "## Cross-Reference Insights"
    echo "- (Connections between papers will be added here)"
    echo ""
    echo "---"
  } > "$progress" || {
    echo -e "${RED}Error:${NC} Failed to reset progress.txt"
    echo "  Check disk space and permissions"
    exit 1
  }

  echo -e "${GREEN}Research reset to DISCOVERY phase${NC}"
  echo "  Papers pool cleared"
  echo "  Progress log reset"
  echo ""
  echo "Run again with: ./ralph.sh $RESEARCH_DIR"
  exit 0
}

# Helper to list available researches (simple version for errors)
list_researches() {
  if [[ -d "$SCRIPT_DIR/researches" ]]; then
    ls -1 "$SCRIPT_DIR/researches/" 2>/dev/null | head -10
  else
    echo "  (none)"
  fi
}

# Show completion summary (used by multiple exit paths)
show_completion_summary() {
  echo ""
  echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  Research-Ralph completed all research tasks!${NC}"
  echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
  echo ""

  # Show summary
  local presented=$(jq -r '.statistics.total_presented // 0' "$RRD_FILE" 2>/dev/null || echo "0")
  local rejected=$(jq -r '.statistics.total_rejected // 0' "$RRD_FILE" 2>/dev/null || echo "0")
  local insights=$(jq -r '.statistics.total_insights_extracted // 0' "$RRD_FILE" 2>/dev/null || echo "0")
  local analyzed=$(jq -r '.statistics.total_analyzed // 0' "$RRD_FILE" 2>/dev/null || echo "0")

  echo -e "  ${BLUE}Summary:${NC}"
  echo "    Papers analyzed:  $analyzed"
  echo "    Papers presented: $presented"
  echo "    Papers rejected:  $rejected"
  echo "    Insights:         $insights"
  echo ""
  echo -e "  ${BLUE}Results in:${NC} $RESEARCH_DIR/"
  echo "    - progress.txt for detailed findings"
  echo "    - rrd.json for full data"
  [[ -f "$RESEARCH_DIR/research-report.md" ]] && echo "    - research-report.md for summary report"
  echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    --list)
      cmd_list
      ;;
    --status)
      if [[ -z "${2:-}" || "$2" == -* ]]; then
        echo -e "${RED}Error:${NC} --status requires a research folder"
        echo "Usage: ./ralph.sh --status <research_folder>"
        exit 1
      fi
      cmd_status "$2"
      ;;
    --reset)
      if [[ -z "${2:-}" || "$2" == -* ]]; then
        echo -e "${RED}Error:${NC} --reset requires a research folder"
        echo "Usage: ./ralph.sh --reset <research_folder>"
        exit 1
      fi
      cmd_reset "$2"
      ;;
    --force)
      FORCE_FLAG=true
      shift
      ;;
    --agent)
      if [[ -z "${2:-}" || "$2" == -* ]]; then
        echo -e "${RED}Error:${NC} --agent requires a value (claude, amp, or codex)"
        exit 1
      fi
      AGENT="$2"
      shift 2
      ;;
    -p|--papers)
      if [[ -z "${2:-}" || ! "$2" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error:${NC} --papers requires a number"
        exit 1
      fi
      TARGET_PAPERS="$2"
      shift 2
      ;;
    -i|--iterations)
      if [[ -z "${2:-}" || ! "$2" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error:${NC} --iterations requires a number"
        exit 1
      fi
      MAX_ITERATIONS="$2"
      ITERATIONS_EXPLICIT=true
      shift 2
      ;;
    -*)
      echo -e "${RED}Error:${NC} Unknown option '$1'. Use --help for usage."
      exit 1
      ;;
    *)
      # First non-option argument is research folder, second is max_iterations
      if [[ -z "$RESEARCH_DIR" ]]; then
        # Try to resolve the research folder path
        if [[ -d "$1" ]]; then
          RESEARCH_DIR="$1"
        elif [[ -d "$SCRIPT_DIR/researches/$1" ]]; then
          RESEARCH_DIR="$SCRIPT_DIR/researches/$1"
        elif [[ -d "$SCRIPT_DIR/$1" ]]; then
          RESEARCH_DIR="$SCRIPT_DIR/$1"
        else
          echo -e "${RED}Error:${NC} Research folder not found: $1"
          echo ""
          echo "Available researches:"
          list_researches
          echo ""
          echo "Create new research: ./skill.sh rrd \"Your research topic\""
          exit 1
        fi
      elif [[ "$1" =~ ^[0-9]+$ ]]; then
        MAX_ITERATIONS="$1"
        ITERATIONS_EXPLICIT=true
      else
        echo "Warning: Ignoring unexpected argument '$1'"
      fi
      shift
      ;;
  esac
done

# Require research folder
if [[ -z "$RESEARCH_DIR" ]]; then
  echo -e "${RED}Error:${NC} Research folder required."
  echo ""
  echo "Usage: ./ralph.sh <research_folder> [-p papers] [-i iterations] [--agent name]"
  echo ""
  echo "Available researches:"
  list_researches
  echo ""
  echo "Create new research: ./skill.sh rrd \"Your research topic\""
  exit 1
fi

# Validate agent
if [[ "$AGENT" != "claude" && "$AGENT" != "amp" && "$AGENT" != "codex" ]]; then
  echo -e "${RED}Error:${NC} Invalid agent '$AGENT'. Must be 'claude', 'amp', or 'codex'."
  exit 1
fi

# Verify CLI is installed before starting
if ! command -v "$AGENT" &> /dev/null; then
  echo -e "${RED}Error:${NC} '$AGENT' CLI not found in PATH."
  [[ "$AGENT" == "amp" ]] && echo "Install it from: https://ampcode.com"
  [[ "$AGENT" == "claude" ]] && echo "Install it from: https://claude.ai/code"
  [[ "$AGENT" == "codex" ]] && echo "Install it from: https://openai.com/codex"
  exit 1
fi

# Verify jq is installed (needed for parsing rrd.json)
if ! command -v jq &> /dev/null; then
  echo -e "${RED}Error:${NC} 'jq' not found in PATH."
  echo "Install it with: brew install jq (macOS) or apt install jq (Linux)"
  exit 1
fi

# File paths within research folder
RRD_FILE="$RESEARCH_DIR/rrd.json"
PROGRESS_FILE="$RESEARCH_DIR/progress.txt"

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

  # Inject research folder path into prompt (replace {{RESEARCH_DIR}} placeholder)
  prompt_content="${prompt_content//\{\{RESEARCH_DIR\}\}/$RESEARCH_DIR}"

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

# Initialize progress file if it doesn't exist
[[ ! -f "$PROGRESS_FILE" ]] && init_progress_file

# Verify RRD file exists before starting
if [[ ! -f "$RRD_FILE" ]]; then
  echo -e "${RED}Error:${NC} rrd.json not found in research folder: $RESEARCH_DIR"
  echo ""
  echo "Expected file: $RRD_FILE"
  echo "Create an RRD first using: ./skill.sh rrd \"Your research topic description\""
  exit 1
fi

# Validate RRD file is valid JSON
if ! jq empty "$RRD_FILE" 2>/dev/null; then
  echo -e "${RED}Error:${NC} rrd.json is not valid JSON"
  echo "Please check the file for syntax errors: $RRD_FILE"
  exit 1
fi

# Validate required fields exist
if ! jq -e '.project' "$RRD_FILE" >/dev/null 2>&1; then
  echo -e "${RED}Error:${NC} rrd.json missing required field 'project'"
  exit 1
fi

if ! jq -e '.requirements.target_papers' "$RRD_FILE" >/dev/null 2>&1; then
  echo -e "${RED}Error:${NC} rrd.json missing required field 'requirements.target_papers'"
  exit 1
fi

# Override target_papers if --papers flag provided
if [[ -n "$TARGET_PAPERS" ]]; then
  # Check if research is already in progress
  CURRENT_PHASE=$(jq -r '.phase // "DISCOVERY"' "$RRD_FILE" 2>/dev/null)
  CURRENT_ANALYZED=$(jq -r '.statistics.total_analyzed // 0' "$RRD_FILE" 2>/dev/null)

  if [[ "$CURRENT_PHASE" != "DISCOVERY" || "$CURRENT_ANALYZED" -gt 0 ]]; then
    CURRENT_TARGET=$(jq -r '.requirements.target_papers // 20' "$RRD_FILE" 2>/dev/null)
    if [[ "$FORCE_FLAG" == "true" ]]; then
      echo -e "${YELLOW}Warning:${NC} Research in progress - forcing target_papers change"
      echo "  Previous: $CURRENT_TARGET → New: $TARGET_PAPERS"
      # Create backup before modifying (Issue 3: verify success)
      local backup_file="$RRD_FILE.backup.$(date +%Y%m%d_%H%M%S)"
      if ! cp "$RRD_FILE" "$backup_file"; then
        echo -e "${RED}Error:${NC} Failed to create backup"
        echo "  Check disk space and permissions: $RESEARCH_DIR"
        exit 1
      fi
      echo -e "${BLUE}Backup created:${NC} $backup_file"
      if ! jq ".requirements.target_papers = $TARGET_PAPERS" "$RRD_FILE" > "$RRD_FILE.tmp"; then
        echo -e "${RED}Error:${NC} Failed to update target_papers"
        rm -f "$RRD_FILE.tmp"
        exit 1
      fi
      mv "$RRD_FILE.tmp" "$RRD_FILE"
    else
      echo -e "${RED}Error:${NC} Cannot change target_papers - research already in progress"
      echo "  Phase: $CURRENT_PHASE, Analyzed: $CURRENT_ANALYZED papers"
      echo "  Current target: $CURRENT_TARGET"
      echo ""
      echo "Options:"
      echo "  1. Run without -p flag to continue with existing target"
      echo "  2. Use --force -p $TARGET_PAPERS to override (creates backup)"
      echo "  3. Use --reset to start fresh"
      exit 1
    fi
  else
    echo "Setting target_papers: $TARGET_PAPERS"
    jq ".requirements.target_papers = $TARGET_PAPERS" "$RRD_FILE" > "$RRD_FILE.tmp" \
      && mv "$RRD_FILE.tmp" "$RRD_FILE"
  fi
fi

# Auto-calculate iterations if not explicitly set
# Formula: papers + 5 (1 for discovery + papers for analysis + 4 buffer)
if [[ "$ITERATIONS_EXPLICIT" == "false" ]]; then
  PAPERS_COUNT=$(jq -r '.requirements.target_papers // 20' "$RRD_FILE")
  MAX_ITERATIONS=$((PAPERS_COUNT + 5))
fi

# Verify prompt.md exists
PROMPT_FILE="$SCRIPT_DIR/prompt.md"
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo -e "${RED}Error:${NC} prompt.md not found at $PROMPT_FILE"
  echo "This file contains the agent instructions and is required."
  exit 1
fi

# Display research info
PROJECT=$(jq -r '.project // "Unknown"' "$RRD_FILE")
PHASE=$(jq -r '.phase // "DISCOVERY"' "$RRD_FILE")
TARGET=$(jq -r '.requirements.target_papers // 0' "$RRD_FILE")
ANALYZED=$(jq -r '.statistics.total_analyzed // 0' "$RRD_FILE")

echo "Starting Research-Ralph v$RALPH_VERSION"
echo "  Research: $RESEARCH_DIR"
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

  # Validate DISCOVERY phase has enough papers before allowing ANALYSIS
  if [[ "$PHASE" == "ANALYSIS" ]]; then
    POOL_COUNT=$(jq '.papers_pool | length' "$RRD_FILE" 2>/dev/null || echo "0")
    TARGET_COUNT=$(jq -r '.requirements.target_papers // 20' "$RRD_FILE" 2>/dev/null || echo "20")

    if [[ "$POOL_COUNT" -lt "$TARGET_COUNT" ]]; then
      echo ""
      echo "  Warning: Only $POOL_COUNT papers in pool, but target is $TARGET_COUNT"
      echo "  Reverting phase to DISCOVERY to collect more papers..."
      jq '.phase = "DISCOVERY"' "$RRD_FILE" > "$RRD_FILE.tmp" && mv "$RRD_FILE.tmp" "$RRD_FILE"
      PHASE="DISCOVERY"
      echo "  Phase: $PHASE (reverted)"
    fi
  fi

  set +e
  OUTPUT=$(run_agent "$PROMPT_FILE")
  EXIT_CODE=$?
  set -e

  if [[ $EXIT_CODE -ne 0 ]]; then
    CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
    echo ""
    echo -e "${RED}Error:${NC} Agent '$AGENT' failed (exit code $EXIT_CODE)."
    echo "  Consecutive failures: $CONSECUTIVE_FAILURES/$MAX_CONSECUTIVE_FAILURES"
    [[ -n "$OUTPUT" ]] && echo "  Last 20 lines:" && echo "$OUTPUT" | tail -20

    # Classify error type and set retry behavior
    RETRY_DELAY=5
    SHOULD_RETRY=true

    if echo "$OUTPUT" | grep -qi "403\|Forbidden"; then
      echo "  Error type: HTTP 403 Forbidden (source block - skipping retry)"
      SHOULD_RETRY=false
    elif echo "$OUTPUT" | grep -qi "429\|Too Many Requests\|rate.limit"; then
      echo "  Error type: Rate limit (429) - extended backoff (30s)"
      RETRY_DELAY=30
    elif echo "$OUTPUT" | grep -qi "bot\|challenge\|captcha\|blocked"; then
      echo "  Error type: Bot challenge detected - skipping retry"
      SHOULD_RETRY=false
    elif echo "$OUTPUT" | grep -qi "timeout\|timed.out"; then
      echo "  Error type: Request timeout - quick retry (2s)"
      RETRY_DELAY=2
    elif echo "$OUTPUT" | grep -qi "network\|connection\|DNS"; then
      echo "  Error type: Network error - quick retry (2s)"
      RETRY_DELAY=2
    fi

    # Skip retry for permanent errors (403, bot blocks)
    if [[ "$SHOULD_RETRY" == "false" ]]; then
      echo "  Skipping retry for this error type, continuing to next iteration..."
      CONSECUTIVE_FAILURES=0  # Reset - this is a known permanent error, not a systemic failure
      continue
    fi

    if [[ $CONSECUTIVE_FAILURES -ge $MAX_CONSECUTIVE_FAILURES ]]; then
      echo ""
      echo -e "${RED}Error:${NC} $MAX_CONSECUTIVE_FAILURES consecutive failures. Aborting."
      echo "Possible causes:"
      echo "  - Agent CLI not properly configured"
      echo "  - Network connectivity issues"
      echo "  - Authentication/API key problems"
      exit 1
    fi

    echo "  Retrying in ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
    continue
  fi

  # Reset on success
  CONSECUTIVE_FAILURES=0

  # Check for completion signal
  PENDING_COUNT=$(jq '[.papers_pool[] | select(.status == "pending" or .status == "analyzing")] | length' "$RRD_FILE" 2>/dev/null || echo "999")
  ANALYZED_COUNT=$(jq -r '.statistics.total_analyzed // 0' "$RRD_FILE" 2>/dev/null || echo "0")
  CURRENT_PHASE=$(jq -r '.phase // "DISCOVERY"' "$RRD_FILE" 2>/dev/null || echo "DISCOVERY")

  # Primary check: explicit completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    if [[ "$PENDING_COUNT" -gt 0 || "$ANALYZED_COUNT" -eq 0 ]]; then
      echo ""
      echo -e "${YELLOW}Warning:${NC} Agent claimed COMPLETE but verification failed!"
      echo "  Pending/analyzing papers: $PENDING_COUNT (should be 0)"
      echo "  Total analyzed: $ANALYZED_COUNT (should be > 0)"
      echo "Ignoring false completion signal, continuing..."
      sleep 2
      continue
    fi

    # Completion verified!
    show_completion_summary
    exit 0
  fi

  # Fallback check: agent said "complete" in plain English AND state is actually complete
  # Issue 8: More robust regex - check for positive completion phrases but exclude negations
  if echo "$OUTPUT" | grep -qi "research.*complete\|all.*papers.*analyzed\|research is complete"; then
    # Make sure it's not a negation like "research is NOT complete"
    if ! echo "$OUTPUT" | grep -qi "not.*complete\|isn't complete\|is not complete\|aren't.*analyzed\|not.*analyzed"; then
      if [[ "$PENDING_COUNT" -eq 0 && "$ANALYZED_COUNT" -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}Note:${NC} Agent indicated completion without exact tag, but state is verified complete"
        show_completion_summary
        exit 0
      fi
    fi
  fi

  # Auto-complete check: if phase is COMPLETE and nothing pending, exit
  if [[ "$CURRENT_PHASE" == "COMPLETE" && "$PENDING_COUNT" -eq 0 && "$ANALYZED_COUNT" -gt 0 ]]; then
    echo ""
    echo -e "${GREEN}Research already complete (detected from rrd.json state)${NC}"
    show_completion_summary
    exit 0
  fi

  # Show iteration delta (Issue 5: track per-iteration progress correctly)
  NEW_ANALYZED=$(jq -r '.statistics.total_analyzed // 0' "$RRD_FILE" 2>/dev/null || echo "0")
  # Ensure it's a valid integer
  if ! [[ "$NEW_ANALYZED" =~ ^[0-9]+$ ]]; then
    NEW_ANALYZED=0
  fi
  if [[ "$NEW_ANALYZED" -gt "$ANALYZED" ]]; then
    echo -e "  ${GREEN}+$((NEW_ANALYZED - ANALYZED)) paper(s) analyzed this iteration${NC}"
  fi
  # Issue 5: Update baseline for next iteration
  ANALYZED=$NEW_ANALYZED

  echo "Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "Research-Ralph reached max iterations ($MAX_ITERATIONS) without completing."
echo "Check $PROGRESS_FILE for current status."
echo "Run again: ./ralph.sh $RESEARCH_DIR [more_iterations]"
exit 1
