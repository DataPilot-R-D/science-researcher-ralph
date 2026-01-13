# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Research-Ralph is an autonomous research scouting agent that discovers, analyzes, and evaluates research papers. It runs an AI agent (Claude Code, Amp, or Codex) repeatedly until all papers in the Research Requirements Document (RRD) are analyzed.

## Sync Policy

Keep research patterns and gotchas in this file in sync with `AGENTS.md`. When updating one, update the other.

## Doc Safety (Rollback)

If automated edits to `AGENTS.md` / `CLAUDE.md` go wrong, restore from baseline:
- Baseline copies: `docs-baseline/AGENTS.md`, `docs-baseline/CLAUDE.md` (do not edit these)
- Restore command: `./restore-docs.sh`
- If you approve the current docs as the new baseline: `cp AGENTS.md docs-baseline/AGENTS.md && cp CLAUDE.md docs-baseline/CLAUDE.md`

## Git Workflow (Checkpoints)

Use git commits as checkpoints so research progress is easy to track and revert:
- Commit after each iteration (and any milestone like phase change)
- Stage only the relevant files (avoid `git add .`); typically: `rrd.json`, `progress.txt`, `AGENTS.md`, `CLAUDE.md`
- Commit message examples:
  - `discovery: add N papers`
  - `analysis: <paper_id> <PRESENT|REJECT|EXTRACT_INSIGHTS> (<score>/30)`
  - `docs: update research patterns/workflow`
  - `milestone: phase -> <DISCOVERY|ANALYSIS|COMPLETE>`

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

**Threshold:** Score >= `min_score_to_present` (default: 18) = PRESENT

## RRD Format

The `rrd.json` file contains:
- `project`, `branchName`, `description` - Research metadata
- `requirements` - Keywords, time window, target papers, sources
- `phase` - DISCOVERY, ANALYSIS, or COMPLETE
- `papers_pool` - All discovered papers with status and analysis
- `insights` - Extracted valuable findings
- `statistics` - Counts for tracking progress

## Stop Condition

When all papers in `papers_pool` have been analyzed (status != "pending" and status != "analyzing"), Research-Ralph outputs `<promise>COMPLETE</promise>` to exit the loop.

## Source Access Patterns

### arXiv API

```
https://export.arxiv.org/api/query?search_query=all:{keyword}&sortBy=submittedDate&sortOrder=descending&max_results=50
```

- Free, no auth required
- Rate limit: Be conservative - 1 request per 3 seconds to avoid blocks
- Returns Atom XML feed

### Google Scholar

- Use WebSearch with keywords
- Add `site:scholar.google.com` for direct results
- Often returns abstracts only (need to follow PDF links)

### PDF Access

- arXiv: Replace `/abs/` with `/pdf/` in URL, add `.pdf`
- Most papers: Check for PDF link in metadata
- Some require institutional access

## Common Gotchas

- **Rate limits:** arXiv blocks rapid requests; add delays between searches
- **Paywalls:** Some papers not freely accessible; note in `blocked_sources`
- **Stale data:** Scholar results can be cached; check dates
- **Duplicate papers:** Same paper on arXiv and publisher site; dedupe by title
- **PDF parsing:** Some PDFs are image-only; note limitations
- **Hallucination risk:** unless you enforce "only claim what you can cite/link", the agent can invent details when it can't read the paper properly

## Operational Rules

- ONE paper per ANALYSIS iteration (deep analysis takes full context)
- Read FULL papers, not just abstracts
- Always extract insights, even from rejected papers
- Track all URLs visited; add to `visited_urls`
- Update statistics after each operation
- When feasible, write small tests or prototype code to validate paper assumptions; record results in `progress.txt` and clean up temp files (or note where the code lives)
- Handle rate limits:
  - Wait 60 seconds before retrying
  - After 3 consecutive failures for a source, add it to `blocked_sources` and move on
  - Log rate limit errors in `progress.txt`
- Process fixes (self-repair):
  - If you notice workflow/instruction issues, log the proposed fix in `progress.txt` (file(s) + change + why)
  - If it's a small doc-only fix, you may edit `AGENTS.md` and `CLAUDE.md` (keep them in sync) and note the change in `progress.txt`
- Follow the Git Workflow (Checkpoints) section for commits

## Patterns

- Each iteration spawns a fresh agent instance with clean context
- Memory persists via `rrd.json` and `progress.txt`
- Cross-reference papers to find connections
- Update this file with domain-specific learnings
