# Research-Ralph

[![Status: Active](https://img.shields.io/badge/status-active-brightgreen)](https://github.com/DataPilot-R-D/science-researcher-ralph)
[![Version: 2.1.0](https://img.shields.io/badge/version-2.1.0-blue)](https://github.com/DataPilot-R-D/science-researcher-ralph/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

Research-Ralph is an autonomous AI research scouting agent that discovers, analyzes, and evaluates research papers. Each research project gets its own folder with all artifacts, and each iteration spawns a fresh agent instance with clean context.

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

### 1. Create a Research Project

Use the RRD skill to generate research requirements:

```bash
./skill.sh rrd "Research robotics and embodied AI, focusing on sim2real transfer"
```

This creates a research folder with your RRD:
```
researches/research-robotics-and-embodied-2026-01-14/
└── rrd.json
```

Answer the clarifying questions to configure your research parameters.

### 2. Run Research-Ralph

```bash
# Run with Claude Code (default)
./ralph.sh researches/research-robotics-and-embodied-2026-01-14

# Run with more iterations
./ralph.sh researches/research-robotics-and-embodied-2026-01-14 20

# Run with Amp
./ralph.sh researches/research-robotics-and-embodied-2026-01-14 --agent amp

# Run with Codex
./ralph.sh researches/research-robotics-and-embodied-2026-01-14 --agent codex
```

Default is 10 iterations. Default agent is Claude Code CLI.

You'll see output like:
```
Starting Research-Ralph v2.1.0
  Research: researches/research-robotics-and-embodied-2026-01-14
  Agent: claude
  Project: Research: Robotics and Embodied AI
  Phase: DISCOVERY
  Papers: 0 analyzed / 20 target
  Max iterations: 10

=======================================================
  Research-Ralph Iteration 1 of 10 (claude)
=======================================================
  Phase: DISCOVERY
```

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

## Folder Structure

Each research project gets its own folder:

```
researches/
├── robotics-llms-2026-01-14/
│   ├── rrd.json           # Research requirements and paper data
│   ├── progress.txt       # Research findings log
│   └── research-report.md # Auto-generated when complete
└── quantum-ai-2026-01-15/
    ├── rrd.json
    └── progress.txt
```

## Key Files

| File/Folder | Purpose |
|-------------|---------|
| `ralph.sh` | Main research loop script |
| `skill.sh` | Skill runner (creates research folders) |
| `prompt.md` | Instructions given to each agent instance |
| `researches/` | Per-research artifact folders |
| `researches/{name}/rrd.json` | Research Requirements Document |
| `researches/{name}/progress.txt` | Research findings log |
| `researches/{name}/research-report.md` | Auto-generated comprehensive report |
| `rrd.json.example` | Example RRD format for reference |
| `skills/rrd/SKILL.md` | Skill for generating RRDs |
| `AGENTS.md` | Research patterns and gotchas |
| `CLAUDE.md` | Same guidance for Claude Code |

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

**Threshold:** Score >= `min_score_to_present` (default: 18) = PRESENT, otherwise REJECT or EXTRACT_INSIGHTS

## Critical Concepts

### Each Iteration = Fresh Context

Each iteration spawns a **new agent instance** with clean context. The only memory between iterations is:
- `researches/{name}/rrd.json` (papers pool, status, insights)
- `researches/{name}/progress.txt` (detailed findings)
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

### Research Report

When research completes, Research-Ralph automatically generates `research-report.md` with:

- **Executive Summary**: Key metrics and findings overview
- **Top Scoring Papers**: Tiered by score (Tier 1: High-Impact, Tier 2: Strong, Tier 3: Threshold)
- **Key Insights by Category**: Grouped findings from all papers
- **Commercial Ecosystem Map**: Companies, valuations, and open-source projects found
- **Research Quality Self-Assessment**: Coverage, depth, accuracy scores (0-100)
- **Recommendations**: Prioritized follow-up actions

## Debugging

Check current state:

```bash
# See research status
cat researches/{folder}/rrd.json | jq '.phase, .statistics'

# See paper statuses
cat researches/{folder}/rrd.json | jq '.papers_pool[] | {id, title, status, score}'

# See research findings
cat researches/{folder}/progress.txt

# See presented papers
cat researches/{folder}/rrd.json | jq '.papers_pool[] | select(.status == "presented")'

# List all research projects
ls researches/
```

## Rate Limits

For higher GitHub API rate limits, set your token:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

- Unauthenticated: 10 requests/minute
- Authenticated: 30 requests/minute

## Doc Safety (Rollback)

The research agent may auto-edit `AGENTS.md` / `CLAUDE.md` to improve the workflow. If you want to revert those doc edits:
- Restore from baseline: `./restore-docs.sh`
- Baseline files live in `docs-baseline/` (do not edit these)
- If you approve the current docs as the new baseline: `cp AGENTS.md docs-baseline/AGENTS.md && cp CLAUDE.md docs-baseline/CLAUDE.md`

## Git Workflow (Checkpoints)

To make research progress easy to track and revert, commit state/doc updates regularly:
- Stage files from the research folder: `researches/{name}/rrd.json`, `researches/{name}/progress.txt`
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

## Contributing

Contributions are welcome! Please:

1. Open an issue first to discuss proposed changes
2. Fork the repository and create a feature branch
3. Submit a pull request with a clear description

For bug reports, include your OS, agent version, and steps to reproduce.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [Claude Code documentation](https://claude.ai/code)
- [Amp documentation](https://ampcode.com/manual)
- [Codex documentation](https://openai.com/codex)
