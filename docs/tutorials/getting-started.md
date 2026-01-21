# Getting Started with Research-Ralph

This tutorial walks you through running your first autonomous research session with Research-Ralph. By the end, you'll have discovered and analyzed research papers on a topic of your choice.

## Prerequisites

Before starting, ensure you have:

### 1. An AI Agent CLI (choose one)

- **Claude Code** (default): Install from [claude.ai/code](https://claude.ai/code)
- **Amp**: Install from [ampcode.com](https://ampcode.com)
- **Codex**: Install from [openai.com/codex](https://openai.com/codex)

Verify installation:
```bash
# For Claude Code
claude --version

# For Amp
amp --version

# For Codex
codex --version
```

### 2. jq (JSON processor)

```bash
# macOS
brew install jq

# Linux
apt install jq

# Verify
jq --version
```

If you did not install the CLI globally, prefix commands below with `poetry run`.

## Step 1: Create a Research Project

Every research run starts with a Research Requirements Document (RRD). Use the built-in creation command:

```bash
research-ralph --new "Research robotics and embodied AI, focusing on sim2real transfer"
```

After creation, you'll see:
```
Research project created: researches/research-robotics-and-embodied-2026-01-14
```

Your research folder now contains `rrd.json`. If `open_questions` are present, review and edit them before running research.
Projects are created in the current directory; examples assume you keep them under `researches/` (run `research-ralph --new` from that directory or move the folder after creation).

## Step 2: Run Research-Ralph

Start the autonomous research loop:

```bash
research-ralph --run researches/research-robotics-and-embodied-2026-01-14
```

You'll see:
```
Research-Ralph - Starting Research Loop

  Project: Research: Robotics and Embodied AI
  Path: researches/research-robotics-and-embodied-2026-01-14
  Agent: claude
  Phase: DISCOVERY
  Papers: 0/20 analyzed
  Max iterations: 26
```

### What Happens During Research

**DISCOVERY Phase:**
- Searches arXiv, Google Scholar, and the web
- Collects papers matching your keywords
- Assigns initial priority scores
- Transitions to ANALYSIS when target count is reached

**ANALYSIS Phase:**
- Analyzes ONE paper per iteration (deep dive)
- Reads full paper content, not just abstracts
- Searches for implementations on GitHub
- Scores using a dual rubric (0-50 combined)
- Decides: PRESENT, REJECT, or EXTRACT_INSIGHTS

## Step 3: Monitor Progress

While Research-Ralph runs, you can check progress:

```bash
# See current phase and stats
cat researches/research-robotics-and-embodied-2026-01-14/rrd.json | jq '.phase, .statistics'

# See paper statuses
cat researches/research-robotics-and-embodied-2026-01-14/rrd.json | jq '.papers_pool[] | {title, status, score}'

# Read detailed findings
cat researches/research-robotics-and-embodied-2026-01-14/progress.txt
```

## Step 4: Review Results

When Research-Ralph completes, it automatically generates a comprehensive `research-report.md`. You can also check individual results:

### Research Report
When all papers are analyzed, a report is auto-generated with:
- Executive summary and key metrics
- Top scoring papers (tiered by score)
- Key insights grouped by category
- Commercial ecosystem map
- Research quality self-assessment
- Prioritized recommendations

```bash
cat researches/research-robotics-and-embodied-2026-01-14/research-report.md
```

### Presented Papers
Papers marked `presented` in the RRD:
```bash
cat researches/research-robotics-and-embodied-2026-01-14/rrd.json | jq '.papers_pool[] | select(.status == "presented")'
```

### Extracted Insights
Valuable findings from all analyzed papers:
```bash
cat researches/research-robotics-and-embodied-2026-01-14/rrd.json | jq '.insights'
```

### Full Research Log
The `progress.txt` file contains detailed analysis notes, cross-references, and discovered patterns.

## Common Options

### Run More Iterations
```bash
research-ralph --run researches/research-robotics-and-embodied-2026-01-14 --iterations 20
```

### Use a Different Agent
```bash
research-ralph --run researches/research-robotics-and-embodied-2026-01-14 --agent amp
```

### Resume Interrupted Research
Just run the same command again - Research-Ralph picks up where it left off based on paper statuses in `rrd.json`.

## Folder Structure

Each research project lives in its own folder:
```
researches/
└── research-robotics-and-embodied-2026-01-14/
    ├── rrd.json           # Research config and paper data
    ├── progress.txt       # Detailed findings log
    └── research-report.md # Auto-generated when complete
```

## Next Steps

- **Customize research parameters**: See [Customizing Research](./customizing-research.md) for tuning keywords, thresholds, and sources
- **Run multiple projects**: Create separate research folders for different topics
- **Understand scoring**: See [Evaluation Rubric](../explanations/evaluation-rubric.md) for how papers are scored

See the [CLI Reference](../reference/cli.md) for all available options.
