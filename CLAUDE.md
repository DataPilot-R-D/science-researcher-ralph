# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Research-Ralph is an autonomous research scouting agent that discovers, analyzes, and evaluates research papers. It runs an AI agent (Claude Code, Amp, or Codex) repeatedly until all papers in the Research Requirements Document (RRD) are analyzed.

## Commands

```bash
# Run Research-Ralph with Claude Code (default)
./ralph.sh [max_iterations]

# Run Research-Ralph with Amp
./ralph.sh [max_iterations] --agent amp

# Run Research-Ralph with Codex
./ralph.sh [max_iterations] --agent codex

# Create a Research Requirements Document
./skill.sh rrd "Your research topic description"

# List available skills
./skill.sh --list
```

## Architecture

### Core Loop (`ralph.sh`)
1. Parses `--agent` flag (default: `claude`, options: `amp`, `codex`)
2. Archives previous research if switching to different topic (via branchName)
3. Invokes the selected agent with `prompt.md`
   - Claude: `claude -p "..." --dangerously-skip-permissions --allowedTools "..."`
   - Amp: `cat prompt.md | amp --dangerously-allow-all`
   - Codex: `codex exec --dangerously-bypass-approvals-and-sandbox -`
4. Checks output for `<promise>COMPLETE</promise>` to exit
5. Repeats until completion or max iterations reached

### Memory Model
Each iteration is stateless. Cross-iteration memory is limited to:
- `rrd.json` (papers pool, status, insights, statistics)
- `progress.txt` (detailed findings log with patterns at top)
- `AGENTS.md` (reusable research patterns)

### Key Files
| File | Purpose |
|------|---------|
| `ralph.sh` | Bash loop spawning fresh agent instances |
| `skill.sh` | Generic skill runner for Claude Code, Amp, and Codex |
| `prompt.md` | Agent instructions for research workflow |
| `rrd.json` | Research Requirements Document with papers and status |
| `rrd.json.example` | Example RRD format for reference |
| `progress.txt` | Append-only research findings log |
| `skills/rrd/SKILL.md` | Skill for generating RRDs |

## Research Workflow

### Two Phases

**DISCOVERY Phase:**
- Search arXiv, Google Scholar, web for papers
- Collect papers matching keywords and criteria
- Assign initial priority scores (1-5)
- Transition to ANALYSIS when target count reached

**ANALYSIS Phase:**
- ONE paper per iteration (deep analysis)
- Read full paper content (not just abstract)
- Search for implementations (GitHub, blogs)
- Check if commercialized
- Score using rubric (0-30)
- Decide: PRESENT / REJECT / EXTRACT_INSIGHTS

### Evaluation Rubric

Papers scored 0-5 on each dimension (total 0-30):

| Dimension | Question |
|-----------|----------|
| Novelty | How new/different is this approach? |
| Feasibility | Can a small team build this? |
| Time-to-POC | How quickly can we prototype? |
| Value/Market | Is there clear demand? |
| Defensibility | What's the competitive advantage? |
| Adoption | How easy to deploy? |

**Threshold:** Score >= 18 = PRESENT

## RRD Format

The `rrd.json` file contains:
- `project`, `branchName`, `description` - Research metadata
- `requirements` - Keywords, time window, target papers, sources
- `phase` - DISCOVERY, ANALYSIS, or COMPLETE
- `papers_pool` - All discovered papers with status and analysis
- `insights` - Extracted valuable findings
- `statistics` - Counts for tracking progress

## Stop Condition

When all papers in `papers_pool` have been analyzed (status != "pending"), Research-Ralph outputs `<promise>COMPLETE</promise>` to exit the loop.
