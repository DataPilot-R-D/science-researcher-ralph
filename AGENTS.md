# Research-Ralph Agent Instructions

## Overview

Research-Ralph is an autonomous research scouting agent that discovers, analyzes, and evaluates research papers. It runs an AI agent (Claude Code, Amp, or Codex) repeatedly until all papers are analyzed.

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

## Key Files

| File | Purpose |
|------|---------|
| `ralph.sh` | Bash loop spawning fresh agent instances |
| `skill.sh` | Generic skill runner for Claude Code, Amp, and Codex |
| `prompt.md` | Agent instructions for research workflow |
| `rrd.json` | Research Requirements Document with papers and status |
| `rrd.json.example` | Example RRD format |
| `progress.txt` | Append-only research findings log |
| `skills/rrd/` | Skill for generating RRDs |

## Research Workflow

### Two Phases

1. **DISCOVERY Phase**
   - Search arXiv, Google Scholar, and web for papers
   - Collect papers matching RRD keywords and criteria
   - Assign initial priority scores
   - Transition to ANALYSIS when target count reached

2. **ANALYSIS Phase**
   - ONE paper per iteration (deep analysis)
   - Read full paper (not just abstract)
   - Search for implementations (GitHub, blogs)
   - Check if commercialized
   - Score using rubric (0-30)
   - Decide: PRESENT / REJECT / EXTRACT_INSIGHTS

### Evaluation Rubric

Score 0-5 on each dimension (total 0-30):

| Dimension | Question |
|-----------|----------|
| Novelty | How new/different is this approach? |
| Feasibility | Can a small team build this? |
| Time-to-POC | How quickly can we prototype? |
| Value/Market | Is there clear demand? |
| Defensibility | What's the competitive advantage? |
| Adoption | How easy to deploy? |

**Threshold:** Score >= 18 = PRESENT, otherwise REJECT or EXTRACT_INSIGHTS

## Source Access Patterns

### arXiv API

```
https://export.arxiv.org/api/query?search_query=all:{keyword}&sortBy=submittedDate&sortOrder=descending&max_results=50
```

- Free, no auth required
- Rate limit: 3 requests per second
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

## Patterns

- Each iteration spawns a fresh agent instance with clean context
- Memory persists via `rrd.json` and `progress.txt`
- ONE paper per ANALYSIS iteration (deep research requires full context)
- Always extract insights, even from rejected papers
- Cross-reference papers to find connections
- Update this file with domain-specific learnings
