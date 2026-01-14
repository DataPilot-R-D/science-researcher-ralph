# CLI Reference

Complete reference for Research-Ralph command-line tools.

## ralph.sh

Main research loop script that runs autonomous research sessions.

### Usage

```bash
./ralph.sh <research_folder> [-p papers] [-i iterations] [--agent name]
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<research_folder>` | Yes | - | Path to research folder containing `rrd.json` |
| `-p, --papers <N>` | No | from rrd.json | Target papers count (auto-sets iterations to N+5) |
| `-i, --iterations <N>` | No | auto-calculated | Override max iterations |
| `--agent <name>` | No | claude | AI agent to use: `claude`, `amp`, or `codex` |
| `-h, --help` | No | - | Show help message |

### Examples

```bash
# Basic usage with defaults (papers from rrd.json, auto iterations)
./ralph.sh researches/robotics-2026-01-14

# Set 30 target papers (iterations auto = 35)
./ralph.sh researches/robotics-2026-01-14 -p 30

# Override iterations if needed
./ralph.sh researches/robotics-2026-01-14 -p 30 -i 100

# Use Amp agent
./ralph.sh researches/robotics-2026-01-14 --agent amp

# Short folder name (resolved to researches/)
./ralph.sh robotics-2026-01-14
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Research completed successfully (all papers analyzed) |
| 1 | Error or max iterations reached without completion |

### Output

- **Console**: Progress updates for each iteration
- **Files**: Updates `rrd.json` and `progress.txt` in the research folder
- **Report**: Auto-generates `research-report.md` when research completes

### Research Report Contents

When all papers are analyzed, the report includes:
- Executive summary with key metrics
- Top scoring papers (tiered by score range)
- Key insights grouped by category
- Commercial ecosystem map (companies, open-source projects)
- Research quality self-assessment (0-100 scores)
- Prioritized follow-up recommendations

### Completion Signal

Research-Ralph exits successfully when it outputs:
```
<promise>COMPLETE</promise>
```

This indicates all papers in `papers_pool` have been analyzed.

---

## skill.sh

Skill runner for creating research projects and other tasks.

### Usage

```bash
./skill.sh <skill_name> "<task_description>" [--agent amp|claude|codex]
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<skill_name>` | Yes | - | Name of skill to run |
| `"<task_description>"` | Yes | - | Description passed to the skill |
| `--agent <name>` | No | claude | AI agent to use |
| `--list` | No | - | List available skills |
| `-h, --help` | No | - | Show help message |

### Available Skills

| Skill | Description |
|-------|-------------|
| `rrd` | Generate a Research Requirements Document |

### Examples

```bash
# List available skills
./skill.sh --list

# Create a new research project
./skill.sh rrd "Research quantum computing applications in machine learning"

# Use Amp agent
./skill.sh rrd "Research NLP transformers" --agent amp
```

### RRD Skill Output

When running the `rrd` skill, it creates:
```
researches/{sanitized-topic}-{date}/
└── rrd.json
```

The folder name is derived from the task description:
- Converted to lowercase
- Non-alphanumeric characters replaced with hyphens
- Truncated to 40 characters
- Date appended in YYYY-MM-DD format

---

## Environment Variables

### GITHUB_TOKEN

Set for higher GitHub API rate limits when searching for implementations.

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

| Authentication | Rate Limit |
|----------------|------------|
| Unauthenticated | 10 requests/minute |
| Authenticated | 30 requests/minute |

---

## File Paths

### Research Folder Structure

```
researches/{name}-{date}/
├── rrd.json           # Research Requirements Document
├── progress.txt       # Research findings log
└── research-report.md # Auto-generated comprehensive report
```

### Project Files

| File | Purpose |
|------|---------|
| `ralph.sh` | Main research loop script |
| `skill.sh` | Skill runner |
| `prompt.md` | Agent instructions |
| `rrd.json.example` | Example RRD format |
| `AGENTS.md` | Research patterns and gotchas |
| `CLAUDE.md` | Claude Code specific guidance |

---

## Debugging

### Check Research Status

```bash
# Current phase and statistics
cat researches/{folder}/rrd.json | jq '.phase, .statistics'

# All paper statuses
cat researches/{folder}/rrd.json | jq '.papers_pool[] | {id, title, status, score}'

# Presented papers only
cat researches/{folder}/rrd.json | jq '.papers_pool[] | select(.status == "presented")'

# Rejected papers
cat researches/{folder}/rrd.json | jq '.papers_pool[] | select(.status == "rejected")'
```

### View Research Log

```bash
# Full log
cat researches/{folder}/progress.txt

# Last 50 lines
tail -50 researches/{folder}/progress.txt
```

### List All Research Projects

```bash
ls -la researches/
```

---

## Error Handling

### Rate Limit Errors

Research-Ralph handles rate limits automatically:
- **429 (Too Many Requests)**: Waits 30s, then retries
- **403 (Forbidden)**: Skips to next source
- **3 consecutive failures**: Source added to `blocked_sources`

### Agent Failures

- **3 consecutive agent failures**: Script aborts with error
- **Network errors**: Quick retry after 2s
- **Timeouts**: Quick retry after 2s

### Recovery

To resume after an error:
```bash
# Just run again - picks up from current state
./ralph.sh researches/{folder}
```
