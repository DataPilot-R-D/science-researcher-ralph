# Research-Ralph Agent Instructions

## Overview

Research-Ralph is an autonomous research scouting agent that discovers, analyzes, and evaluates research papers. It runs an AI agent (Claude Code, Amp, or Codex) repeatedly until all papers are analyzed.

## Sync Policy

Keep research patterns and gotchas in this file in sync with `CLAUDE.md`. When updating one, update the other.

## Commands

```bash
# Create a new research (creates folder in researches/)
./skill.sh rrd "Your research topic description"
# Creates: researches/{topic}-{date}/rrd.json

# Run research on a folder
./ralph.sh researches/{folder-name} [max_iterations]

# Examples
./ralph.sh researches/robotics-llms-2026-01-14
./ralph.sh researches/robotics-llms-2026-01-14 20
./ralph.sh researches/robotics-llms-2026-01-14 --agent amp

# List available skills
./skill.sh --list
```

## Folder Structure

```
researches/
├── robotics-llms-2026-01-14/
│   ├── rrd.json           # Research requirements and paper data
│   ├── progress.txt       # Research findings log
│   └── research-report.md # Optional: final report
└── quantum-ai-2026-01-15/
    ├── rrd.json
    └── progress.txt
```

## Key Files

| File/Folder | Purpose |
|-------------|---------|
| `ralph.sh` | Main research loop script |
| `skill.sh` | Skill runner (creates research folders for rrd skill) |
| `prompt.md` | Agent instructions for research workflow |
| `researches/` | Per-research artifact folders |
| `researches/{name}/rrd.json` | Research Requirements Document |
| `researches/{name}/progress.txt` | Research findings log |
| `rrd.json.example` | Example RRD format |
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

**Threshold:** Score >= `min_score_to_present` (default: 18) = PRESENT, otherwise REJECT or EXTRACT_INSIGHTS

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
- **Web search blocks:** DuckDuckGo HTML can trigger bot challenges; use GitHub API or alternate sources
- **Duplicate papers:** Same paper on arXiv and publisher site; dedupe by title
- **PDF parsing:** Some PDFs are image-only; note limitations
- **Semantic label mismatch:** Robot object/action labels that do not map cleanly to English can degrade LLM explanations; consider a translation dictionary
- **Hallucination risk:** unless you enforce "only claim what you can cite/link", the agent can invent details when it can't read the paper properly

## Source Fallback Strategy

When searching for papers and implementations, use this fallback hierarchy:

**Implementation checks:** GitHub API → arXiv → Semantic Scholar → WebSearch
**Paper discovery:** arXiv API → Google Scholar → web

**Rate limit handling:**
- 429/503 → wait 60s, retry (max 2 retries)
- 403 → skip to next source, log in progress.txt
- 3 consecutive blocks → add to `blocked_sources`

**GitHub API (preferred for implementation checks):**
```
https://api.github.com/search/repositories?q="{paper_title}"+language:python
```

**GitHub API Authentication (recommended):**
Set `GITHUB_TOKEN` environment variable for higher rate limits:
- Unauthenticated: 10 requests/minute
- Authenticated: 30 requests/minute

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

The agent will automatically use `Authorization: token $GITHUB_TOKEN` header when available.

**If all sources blocked:** Extract URLs from paper's Related Work section

## Rate Limiting Configuration

| Source | Delay | Retry on 429 | Retry on 403 |
|--------|-------|--------------|--------------|
| arXiv API | 3s | Yes (60s backoff) | No |
| Google Scholar | 5s | Yes | No (use fallback) |
| GitHub API | 1s | Yes | No |
| WebSearch | 2s | Yes | No |

If a source is blocked 3 consecutive iterations → move to `blocked_sources` and use fallback.

## Cross-Reference Patterns

When analyzing papers, actively identify cross-reference clusters:
- **Same benchmark:** e.g., LIBERO used by InternVLA-A1, Dream-VLA, π₀.₅
- **Same dataset:** e.g., Open-X Embodiment
- **Same authors/institutions:** Track prolific labs and researchers
- **Competing approaches:** e.g., MoT vs Diffusion vs Flow Matching for VLA backbone

Add `cross_cluster` field to insights when patterns emerge:
```json
{"cross_cluster": "VLA_ARCHITECTURES", "papers": ["arxiv_X", "arxiv_Y"]}
```

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
- Memory persists via `researches/{name}/rrd.json` and `researches/{name}/progress.txt`
- Each research topic has its own isolated folder
- Cross-reference papers to find connections
- Update this file with domain-specific learnings
- Keep this file mirrored in `CLAUDE.md` so Claude Code gets the same updated guidance

## Git Workflow (Checkpoints)

Use git commits as checkpoints so it's easy to review/revert research progress:
- Commit after each iteration (and any milestone like phase change)
- Stage files from the research folder: `researches/{name}/rrd.json`, `researches/{name}/progress.txt`
- Commit message examples:
  - `discovery: add N papers`
  - `analysis: <paper_id> <PRESENT|REJECT|EXTRACT_INSIGHTS> (<score>/30)`
  - `docs: update research patterns/workflow`
  - `milestone: phase -> <DISCOVERY|ANALYSIS|COMPLETE>`

## Doc Safety (Rollback)

If an agent auto-edits `AGENTS.md` / `CLAUDE.md` and you want to revert:
- Baseline copies: `docs-baseline/AGENTS.md`, `docs-baseline/CLAUDE.md` (do not edit these)
- Restore command: `./restore-docs.sh`
- If you approve the current docs as the new baseline: `cp AGENTS.md docs-baseline/AGENTS.md && cp CLAUDE.md docs-baseline/CLAUDE.md`
