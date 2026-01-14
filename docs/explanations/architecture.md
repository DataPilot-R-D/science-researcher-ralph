# Architecture Overview

This document explains how Research-Ralph works internally, helping you understand its design and behavior.

## Core Concept: Stateless Iterations

Research-Ralph runs AI agents in a loop, where **each iteration is completely stateless**. The agent has no memory of previous iterations - it starts fresh every time.

```
┌─────────────────────────────────────────────────────────────┐
│                      ralph.sh Loop                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ Iter 1  │ -> │ Iter 2  │ -> │ Iter 3  │ -> ...          │
│  │ (fresh) │    │ (fresh) │    │ (fresh) │                 │
│  └────┬────┘    └────┬────┘    └────┬────┘                 │
│       │              │              │                       │
│       v              v              v                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Persistent Storage                      │   │
│  │  • rrd.json (state, papers, insights)               │   │
│  │  • progress.txt (findings log)                       │   │
│  │  • AGENTS.md (patterns, learned gotchas)            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Memory Persistence

Since agents are stateless, all memory persists through files:

| File | Purpose | Read | Write |
|------|---------|------|-------|
| `rrd.json` | State, papers, insights, statistics | Every iteration | Updated after each action |
| `progress.txt` | Detailed findings, patterns | For context | Appended each iteration |
| `AGENTS.md` | Patterns, gotchas, workflow tips | Every iteration | When patterns discovered |

## Two-Phase Workflow

Research runs through two distinct phases:

### DISCOVERY Phase

**Goal**: Find papers matching the research requirements.

```
┌─────────────────────────────────────────┐
│           DISCOVERY Phase               │
│                                         │
│  Search Sources:                        │
│  • arXiv API                           │
│  • Google Scholar                       │
│  • Web (blogs, GitHub)                 │
│                                         │
│  For each paper found:                  │
│  1. Extract metadata                    │
│  2. Assign priority score (1-5)         │
│  3. Add to papers_pool with "pending"   │
│                                         │
│  Transition when:                       │
│  papers_pool.length >= target_papers    │
└─────────────────────────────────────────┘
```

### ANALYSIS Phase

**Goal**: Deep-analyze each paper and make decisions.

```
┌─────────────────────────────────────────┐
│           ANALYSIS Phase                │
│                                         │
│  ONE paper per iteration:               │
│                                         │
│  1. Select highest-priority pending     │
│  2. Set status = "analyzing"            │
│  3. Read full paper content             │
│  4. Search for implementations          │
│  5. Check commercialization             │
│  6. Score using [rubric](evaluation-rubric.md) (0-30) │
│  7. Decide: PRESENT/REJECT/EXTRACT      │
│  8. Extract insights                    │
│  9. Update status and log findings      │
│                                         │
│  Complete when:                         │
│  All papers have status != "pending"    │
└─────────────────────────────────────────┘
```

## Agent Invocation

The `ralph.sh` script invokes agents differently based on the selected backend:

### Claude Code
```bash
claude -p "$PROMPT" \
  --dangerously-skip-permissions \
  --allowedTools "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch"
```

### Amp
```bash
echo "$PROMPT" | amp --dangerously-allow-all
```

### Codex
```bash
echo "$PROMPT" | codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --output-last-message "$TEMP_FILE" -
```

## Completion Detection

Research-Ralph monitors agent output for the completion signal:

```
<promise>COMPLETE</promise>
```

When detected, the loop exits successfully. This signal is output by the agent when all papers in `papers_pool` have been analyzed (no more `pending` or `analyzing` statuses).

## Error Handling

### Retry Logic
```
Error Type          | Action              | Delay
--------------------|---------------------|-------
429 (Rate Limit)    | Retry               | 30s
403 (Forbidden)     | Skip source         | 0s
Timeout             | Retry               | 2s
Network Error       | Retry               | 2s
3 consecutive fails | Abort               | -
```

### Source Blocking
After 3 consecutive failures from a source:
1. Source added to `blocked_sources`
2. Agent uses fallback sources
3. Logged in `progress.txt`

## Data Flow

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   prompt.md  │────>│   Agent     │────>│   Output     │
│  (instructions)    │  (Claude/   │     │  (findings)  │
└──────────────┘     │   Amp/Codex)│     └──────┬───────┘
                     └──────┬──────┘            │
                            │                   │
       ┌────────────────────┼───────────────────┘
       │                    │
       v                    v
┌──────────────┐     ┌──────────────┐
│  rrd.json    │<───>│ progress.txt │
│  (state)     │     │ (log)        │
└──────────────┘     └──────────────┘
```

## Why This Architecture?

### Advantages

1. **Resumability**: Crash at any point, resume from exact state
2. **Debuggability**: Inspect `rrd.json` and `progress.txt` at any time
3. **Agent-agnostic**: Any AI agent can continue work started by another
4. **Version control**: Git tracks all state changes
5. **Isolation**: Each research project is independent

### Trade-offs

1. **No cross-iteration context**: Agent can't remember what it "learned" last iteration
2. **File I/O overhead**: State saved/loaded every iteration
3. **Limited coordination**: Hard to do multi-step planning across iterations

## File Locations

```
project-root/
├── ralph.sh              # Loop controller
├── skill.sh              # Skill runner
├── prompt.md             # Agent instructions
├── AGENTS.md             # Patterns (agent reads/writes)
├── CLAUDE.md             # Claude-specific guidance
└── researches/
    └── {name}-{date}/
        ├── rrd.json      # Research state
        └── progress.txt  # Findings log
```

---

## Related Documentation

- [Evaluation Rubric](evaluation-rubric.md) - How papers are scored during ANALYSIS
- [RRD Schema](../reference/rrd-schema.md) - Complete `rrd.json` field reference
- [CLI Reference](../reference/cli.md) - Command-line options for `ralph.sh`
- [Handle Rate Limits](../how-to/handle-rate-limits.md) - Error handling in practice
