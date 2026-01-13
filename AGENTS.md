# Ralph Agent Instructions

## Overview

Ralph is an autonomous AI agent loop that runs an AI coding agent (Claude Code or Amp) repeatedly until all PRD items are complete. Each iteration is a fresh agent instance with clean context.

## Commands

```bash
# Run Ralph with Claude Code (default)
./ralph.sh [max_iterations]

# Run Ralph with Amp
./ralph.sh [max_iterations] --agent amp

# Run the flowchart dev server
cd flowchart && npm run dev

# Build the flowchart
cd flowchart && npm run build
```

## Key Files

- `ralph.sh` - The bash loop that spawns fresh agent instances
- `prompt.md` - Agent-agnostic instructions given to each iteration
- `prd.json.example` - Example PRD format
- `flowchart/` - Interactive React Flow diagram explaining how Ralph works

## Flowchart

The `flowchart/` directory contains an interactive visualization built with React Flow. It's designed for presentations - click through to reveal each step with animations.

To run locally:
```bash
cd flowchart
npm install
npm run dev
```

## Patterns

- Each iteration spawns a fresh agent instance with clean context
- Memory persists via git history, `progress.txt`, and `prd.json`
- Stories should be small enough to complete in one context window
- Always update AGENTS.md with discovered patterns for future iterations
