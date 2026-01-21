# CLI Reference

Complete reference for Research-Ralph command-line tools.

## research-ralph

Primary Python CLI for Research-Ralph. Run without arguments to open the interactive menu.
If you installed via Poetry, use `poetry run research-ralph`.

### Flag-based usage

```bash
research-ralph [--new "<topic>"] [--run <project>] [--status <project>] [--list] \
  [--reset <project>] [--config [key=value]] [--papers N] [--iterations N] \
  [--agent claude|amp|codex] [--force] [--version]
```

### Subcommands

```bash
research-ralph create "<topic>" [--papers N] [--agent claude|amp|codex]
research-ralph run <project> [--papers N] [--iterations N] [--agent claude|amp|codex] [--force]
research-ralph status <project>
research-ralph list
research-ralph reset <project> [--yes]
research-ralph config [key[=value]]
research-ralph init [--yes]
```

### Core flags

| Flag | Description |
|------|-------------|
| `--new "<topic>"` | Create a new research project using the built-in RRD skill |
| `--run <project>` | Run research on a project (name or path) |
| `--status <project>` | Show detailed status for a project |
| `--list` | List all research projects |
| `--reset <project>` | Reset a project to DISCOVERY phase (creates backup) |
| `--config [key=value]` | View or set CLI config |
| `--version` | Show version and exit |
| `-h, --help` | Show help message |

### Run options

| Option | Description |
|--------|-------------|
| `-p, --papers <N>` | Target papers count (auto-sets iterations to N+6) |
| `-i, --iterations <N>` | Override max iterations (default: auto-calculated) |
| `--agent <name>` | AI agent to use: `claude`, `amp`, or `codex` |
| `--force` | Allow `--papers` to override target_papers on in-progress research |

### Examples

```bash
# Interactive menu
research-ralph

# Create a new project
research-ralph --new "Research robotics and embodied AI"

# List all projects
research-ralph --list

# Run research on a project folder
research-ralph --run researches/robotics-2026-01-14

# Override papers and iterations
research-ralph --run researches/robotics-2026-01-14 -p 30 -i 100

# Use a different agent
research-ralph --run researches/robotics-2026-01-14 --agent amp

# Reset a project
research-ralph --reset researches/robotics-2026-01-14
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Research completed successfully |
| 1 | Error or max iterations reached without completion |
| 130 | Interrupted (Ctrl+C) |

### Output

- **Console**: Progress updates for each iteration
- **Files**: Updates `rrd.json` and `progress.txt` in the project folder
- **Report**: Auto-generates `research-report.md` when research completes

### Research report contents

When all papers are analyzed, the report includes:
- Executive summary with key metrics
- Top scoring papers (tiered by score range)
- Key insights grouped by category
- Commercial ecosystem map (companies, open-source projects)
- Research quality self-assessment (0-100 scores)
- Prioritized follow-up recommendations

### Completion signal

Research-Ralph exits successfully when it outputs:
```
<promise>COMPLETE</promise>
```

This indicates all papers in `papers_pool` have been analyzed.

---

## RRD creation output

`research-ralph --new` (or `create`) generates:
```
<project-slug>-YYYY-MM-DD/
└── rrd.json
```

The folder name is derived from the RRD `project` field (preferred) or the input topic:
- Converted to lowercase
- Non-alphanumeric characters replaced with hyphens
- Truncated to 40-50 characters
- Date appended in YYYY-MM-DD format

Projects are created in the current working directory; examples use a `researches/` folder for organization.

### Path resolution tips

- Use `research-ralph --run .` from inside a project folder.
- You can pass an absolute path or a folder name under the current directory.
- If you keep projects under `researches/`, use `researches/<name>`.

---

## Environment variables

### GITHUB_TOKEN

Set for higher GitHub API rate limits when searching for implementations.

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

| Authentication | Rate limit |
|----------------|------------|
| Unauthenticated | 10 requests/minute |
| Authenticated | 30 requests/minute |

---

## File paths

### Project files

| File | Purpose |
|------|---------|
| `ralph/cli.py` | Python CLI entrypoint (`research-ralph`) |
| `prompt.md` | Agent instructions |
| `rrd.json.example` | Example RRD format |
| `AGENTS.md` | Research patterns and gotchas |
| `CLAUDE.md` | Claude Code specific guidance |
| `skills/rrd/SKILL.md` | RRD skill definition |

---

## Debugging

### Check research status

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

### View research log

```bash
# Full log
cat researches/{folder}/progress.txt

# Last 50 lines
tail -50 researches/{folder}/progress.txt
```

### List all research projects

```bash
ls -la researches/
```

---

## Error handling

### Rate limit errors

Research-Ralph handles rate limits automatically:
- **429 (Too Many Requests)**: Waits 30s, then retries
- **403 (Forbidden)**: Skips to next source
- **3 consecutive failures**: Source added to `blocked_sources`

### Agent failures

- **Max consecutive failures**: Controlled by `max_consecutive_failures` in config
- **Network errors**: Quick retry after 2s
- **Timeouts**: Quick retry after 2s

### Recovery

To resume after an error:
```bash
# Just run again - picks up from current state
research-ralph --run researches/{folder}
```
