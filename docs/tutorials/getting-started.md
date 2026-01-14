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

## Step 1: Create a Research Project

Every research run starts with a Research Requirements Document (RRD). Use the `rrd` skill to generate one:

```bash
./skill.sh rrd "Research robotics and embodied AI, focusing on sim2real transfer"
```

The skill will ask clarifying questions about:
- **Keywords**: Search terms for finding papers
- **Time window**: How recent the papers should be
- **Target papers**: How many papers to discover
- **Scoring threshold**: Minimum score to present a paper

After answering, you'll see:
```
Created research folder: researches/research-robotics-and-embodied-2026-01-14/
```

Your research folder now contains `rrd.json` with your configuration.

## Step 2: Run Research-Ralph

Start the autonomous research loop:

```bash
./ralph.sh researches/research-robotics-and-embodied-2026-01-14
```

You'll see:
```
Starting Research-Ralph v2.1.0
  Research: researches/research-robotics-and-embodied-2026-01-14
  Agent: claude
  Project: Research: Robotics and Embodied AI
  Phase: DISCOVERY
  Papers: 0 analyzed / 20 target
  Max iterations: 10
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
- Scores using a 6-dimension rubric (0-30 points)
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

When Research-Ralph completes (or you stop it), check your results:

### Presented Papers
Papers that scored >= 18/30 and are worth investigating:
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
./ralph.sh researches/research-robotics-and-embodied-2026-01-14 20
```

### Use a Different Agent
```bash
./ralph.sh researches/research-robotics-and-embodied-2026-01-14 --agent amp
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
    └── research-report.md # Optional: final report
```

## Next Steps

- **Customize research parameters**: Edit `rrd.json` to adjust keywords, thresholds, or add exclusions
- **Run multiple projects**: Create separate research folders for different topics
- **Generate reports**: Ask the agent to create a summary report from the findings

See the [CLI Reference](../reference/cli.md) for all available options.
