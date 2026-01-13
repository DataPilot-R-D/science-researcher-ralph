# Research-Ralph

![Ralph](ralph.webp)

Research-Ralph is an autonomous AI research scouting agent that discovers, analyzes, and evaluates research papers. Each iteration spawns a fresh agent instance with clean context. Memory persists via `rrd.json` (Research Requirements Document), `progress.txt`, and `AGENTS.md`.

**Supported Agents:**
- [Claude Code CLI](https://claude.ai/code) (default)
- [Amp CLI](https://ampcode.com)
- [Codex CLI](https://openai.com/codex)

Based on [Geoffrey Huntley's Ralph pattern](https://ghuntley.com/ralph/), adapted for research scouting.

## Prerequisites

Choose ONE of the following AI agents:
- [Claude Code CLI](https://claude.ai/code) installed and authenticated (default)
- [Amp CLI](https://ampcode.com) installed and authenticated
- [Codex CLI](https://openai.com/codex) installed and authenticated

Also required:
- `jq` installed (`brew install jq` on macOS)

## Quick Start

### 1. Create a Research Requirements Document (RRD)

Use the RRD skill to generate research requirements:

```bash
./skill.sh rrd "Research robotics and embodied AI, focusing on sim2real transfer"
```

Answer the clarifying questions. The skill saves output to `rrd.json`.

### 2. Run Research-Ralph

```bash
# Run with Claude Code (default)
./ralph.sh [max_iterations]

# Run with Amp
./ralph.sh [max_iterations] --agent amp

# Run with Codex
./ralph.sh [max_iterations] --agent codex
```

Default is 10 iterations. Default agent is Claude Code CLI.

Research-Ralph will:
1. **DISCOVERY Phase:** Search arXiv, Google Scholar, and web for papers matching your requirements
2. **ANALYSIS Phase:** Deep-analyze ONE paper per iteration:
   - Read the full paper (not just abstract)
   - Search for implementations (GitHub, blogs)
   - Check if commercialized
   - Score using evaluation rubric
   - Decide: PRESENT / REJECT / EXTRACT_INSIGHTS
3. Update `rrd.json` with findings
4. Append detailed analysis to `progress.txt`
5. Repeat until all papers analyzed

## Key Files

| File | Purpose |
|------|---------|
| `ralph.sh` | The bash loop that spawns fresh agent instances |
| `skill.sh` | Run skills with Claude Code, Amp, or Codex |
| `prompt.md` | Instructions given to each agent instance |
| `rrd.json` | Research Requirements Document with papers and status |
| `rrd.json.example` | Example RRD format for reference |
| `progress.txt` | Append-only research findings log |
| `skills/rrd/` | Skill for generating RRDs |
| `AGENTS.md` | Research patterns and gotchas for the loop agent |
| `CLAUDE.md` | Same guidance for Claude Code (kept in sync with `AGENTS.md`) |
| `docs-baseline/` | Baseline copies of `AGENTS.md` / `CLAUDE.md` for rollback |
| `restore-docs.sh` | Restore `AGENTS.md` / `CLAUDE.md` from `docs-baseline/` |

## Research Workflow

### Two Phases

**DISCOVERY Phase:**
- Search arXiv, Google Scholar, and web for papers
- Collect papers matching keywords and criteria
- Assign initial priority scores (1-5)
- Transition to ANALYSIS when target count reached

**ANALYSIS Phase (ONE paper per iteration):**
- Read full paper content
- Search for GitHub implementations
- Search for blog posts and discussions
- Check if commercialized
- Score using evaluation rubric
- Decide: PRESENT / REJECT / EXTRACT_INSIGHTS
- Extract insights (even from rejected papers)

### Evaluation Rubric

Papers are scored 0-5 on each dimension (total 0-30):

| Dimension | Question |
|-----------|----------|
| **Novelty** | How new/different is this approach? |
| **Feasibility** | Can a small team build this? |
| **Time-to-POC** | How quickly can we prototype? |
| **Value/Market** | Is there clear demand? |
| **Defensibility** | What's the competitive advantage? |
| **Adoption** | How easy to deploy? |

**Threshold:** Score >= 18 = PRESENT, otherwise REJECT or EXTRACT_INSIGHTS

## Critical Concepts

### Each Iteration = Fresh Context

Each iteration spawns a **new agent instance** with clean context. The only memory between iterations is:
- `rrd.json` (papers pool, status, insights)
- `progress.txt` (detailed findings)
- `AGENTS.md` (research patterns)

### Deep Research

Research-Ralph reads **full papers**, not just abstracts. This is deep research that requires thorough analysis of methodology, results, and limitations.

### Insights Are Always Extracted

Even rejected papers can have valuable insights. Research-Ralph extracts and preserves findings from every paper analyzed.

### Cross-Reference Insights

Research-Ralph looks for connections between papers:
- Similar techniques
- Papers that build on each other
- Complementary approaches
- Conflicting claims

### Stop Condition

When all papers in `papers_pool` have been analyzed, Research-Ralph outputs `<promise>COMPLETE</promise>` and exits.

## Debugging

Check current state:

```bash
# See research status
cat rrd.json | jq '.phase, .statistics'

# See paper statuses
cat rrd.json | jq '.papers_pool[] | {id, title, status, score}'

# See research findings
cat progress.txt

# See presented papers
cat rrd.json | jq '.papers_pool[] | select(.status == "presented")'
```

## Archiving

Research-Ralph automatically archives previous runs when you start a new research topic (different `branchName`). Archives are saved to `archive/YYYY-MM-DD-topic-name/`.

## Doc Safety (Rollback)

The research agent may auto-edit `AGENTS.md` / `CLAUDE.md` to improve the workflow. If you want to revert those doc edits:
- Restore from baseline: `./restore-docs.sh`
- Baseline files live in `docs-baseline/` (do not edit these)
- If you approve the current docs as the new baseline: `cp AGENTS.md docs-baseline/AGENTS.md && cp CLAUDE.md docs-baseline/CLAUDE.md`

## Git Workflow (Checkpoints)

To make research progress easy to track and revert, commit state/doc updates regularly:
- Commit after each iteration (and any milestone like phase change)
- Stage only the relevant files (avoid `git add .`); typically: `rrd.json`, `progress.txt`, `AGENTS.md`, `CLAUDE.md`
- Commit message examples:
  - `discovery: add N papers`
  - `analysis: <paper_id> <PRESENT|REJECT|EXTRACT_INSIGHTS> (<score>/30)`
  - `docs: update research patterns/workflow`
  - `milestone: phase -> <DISCOVERY|ANALYSIS|COMPLETE>`

## Skills

Skills are reusable prompts that work with Claude Code, Amp, and Codex.

### Available Skills

| Skill | Description |
|-------|-------------|
| `rrd` | Generate an RRD from research topic description |

### Running Skills

```bash
# List available skills
./skill.sh --list

# Run a skill with Claude Code (default)
./skill.sh rrd "Research robotics and embodied AI"

# Run a skill with Amp
./skill.sh rrd "Research NLP transformers" --agent amp

# Run a skill with Codex
./skill.sh rrd "Research computer vision" --agent codex
```

## RRD Format

The Research Requirements Document (`rrd.json`) contains:

```json
{
  "project": "Research: [Topic]",
  "branchName": "research/[topic-slug]",
  "description": "Research objective and scope",
  "requirements": {
    "focus_area": "robotics",
    "keywords": ["embodied AI", "manipulation", "sim2real"],
    "time_window_days": 30,
    "target_papers": 20,
    "sources": ["arXiv", "Google Scholar", "web"],
    "min_score_to_present": 18
  },
  "phase": "DISCOVERY | ANALYSIS | COMPLETE",
  "papers_pool": [...],
  "insights": [...],
  "visited_urls": [],
  "blocked_sources": [],
  "statistics": {...}
}
```

See `rrd.json.example` for the complete schema with all fields.

## References

- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [Claude Code documentation](https://claude.ai/code)
- [Amp documentation](https://ampcode.com/manual)
- [Codex documentation](https://openai.com/codex)
