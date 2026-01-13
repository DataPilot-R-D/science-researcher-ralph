# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Ralph is an autonomous AI agent loop that runs an AI coding agent (Claude Code or Amp) repeatedly until all PRD items are complete. Each iteration spawns a fresh agent instance with clean context. Memory persists via git history, `progress.txt`, and `prd.json`.

## Commands

```bash
# Run Ralph with Claude Code (default)
./ralph.sh [max_iterations]

# Run Ralph with Amp
./ralph.sh [max_iterations] --agent amp

# Run a skill
./skill.sh <skill-name> [task] [--agent amp|claude]
./skill.sh --list                    # List available skills
./skill.sh prd "Create a PRD for X"  # Generate a PRD
./skill.sh ralph tasks/prd-X.md      # Convert PRD to JSON

# Flowchart development
cd flowchart && npm install    # Install dependencies
cd flowchart && npm run dev    # Start dev server
cd flowchart && npm run build  # Build (runs tsc -b && vite build)
cd flowchart && npm run lint   # Run ESLint
```

## Architecture

### Core Loop (`ralph.sh`)
1. Parses `--agent` flag (default: `claude`, option: `amp`)
2. Archives previous run if switching to a different feature branch
3. Invokes the selected agent with `prompt.md`
   - Claude: `claude -p "..." --dangerously-skip-permissions --allowedTools "..."`
   - Amp: `cat prompt.md | amp --dangerously-allow-all`
4. Checks output for `<promise>COMPLETE</promise>` to exit
5. Repeats until completion or max iterations reached

### Memory Model
Each iteration is stateless. Cross-iteration memory is limited to:
- Git history (commits from previous iterations)
- `progress.txt` (append-only learnings log with consolidated patterns at top)
- `prd.json` (tracks which stories have `passes: true`)

### Key Files
| File | Purpose |
|------|---------|
| `ralph.sh` | Bash loop spawning fresh agent instances |
| `skill.sh` | Generic skill runner for both Claude Code and Amp |
| `prompt.md` | Agent-agnostic instructions for each iteration |
| `prd.json` | User stories with `passes` status |
| `progress.txt` | Append-only learnings; `## Codebase Patterns` section at top for reusable knowledge |
| `skills/prd/SKILL.md` | Skill for generating PRDs |
| `skills/ralph/SKILL.md` | Skill for converting PRDs to JSON |

### Flowchart (`flowchart/`)
Interactive React Flow visualization for presentations. Built with:
- React 19 + TypeScript
- @xyflow/react for flowchart rendering
- Vite for bundling

The `App.tsx` implements a step-through presentation where nodes/edges appear progressively via opacity transitions.

## PRD Format

Stories in `prd.json` must be:
- **Small**: Completable in one context window (one agent iteration)
- **Ordered by dependency**: Schema → backend → UI
- **Verifiable**: Acceptance criteria must be checkable, not vague

Frontend stories should include browser verification in acceptance criteria.

## Workflow Pattern

When Ralph runs a story:
1. Picks highest priority story where `passes: false`
2. Implements the story
3. Runs quality checks (typecheck, tests)
4. Commits if checks pass
5. Updates `prd.json` to mark `passes: true`
6. Appends learnings to `progress.txt`
7. Updates relevant `AGENTS.md` files with reusable patterns

## Stop Condition

When all stories have `passes: true`, output `<promise>COMPLETE</promise>` to exit the loop.
