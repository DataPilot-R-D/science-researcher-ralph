# Configuration Reference

All configurable options for Research-Ralph.

## Config file

Default location:
- `~/.research-ralph/config.yaml`

Create or view config via:
```bash
# Show all config
research-ralph config

# Set a value
research-ralph config default_agent=amp

# Alternate flag form
research-ralph --config default_papers=30
research-ralph --config=
```

### Config keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `research_dir` | string | `~/research` | Directory you use for projects (shown in UI; project creation uses current working directory) |
| `default_agent` | string | `claude` | Default agent to use |
| `default_papers` | int | `20` | Default target papers for new projects |
| `live_output` | bool | `true` | Stream agent output during runs |
| `max_consecutive_failures` | int | `3` | Abort after this many consecutive failures |

---

## Environment variables

### GITHUB_TOKEN

GitHub Personal Access Token for higher API rate limits.

| Setting | Value |
|---------|-------|
| Required | No (but recommended) |
| Effect | Increases GitHub API from 10 to 30 req/min |
| Scope needed | `public_repo` (read-only) |

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Create at: https://github.com/settings/tokens

---

## RRD configuration

All settings in `rrd.json` under `requirements`:

### Search settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `focus_area` | string | - | Primary domain (robotics, NLP, etc.) |
| `keywords` | string[] | - | Search terms |
| `time_window_days` | number | 30 | Recent paper window |
| `historical_lookback_days` | number | 1095 | Foundational paper window |
| `target_papers` | number | 20 | Papers to collect |
| `sources` | string[] | ["arXiv", "Google Scholar", "web"] | Search sources |

### Evaluation settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_score_to_present` | number | 18 | Legacy execution-only threshold (0-30) |

### Mission settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mission.blue_ocean_scoring` | bool | true | Enable strategic scoring |
| `mission.min_combined_score` | number | 25 | Minimum combined score (0-50) to present |
| `mission.min_blue_ocean_score` | number | 12 | Minimum blue ocean score (0-20) |
| `mission.strategic_focus` | string | balanced | balanced, execution, or blue_ocean |

### Adjusting settings

Edit `rrd.json` directly:

```bash
# View current settings
cat researches/your-folder/rrd.json | jq '.requirements'

# Modify (example: change threshold to 20)
jq '.requirements.min_score_to_present = 20' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

---

## CLI options

See the [CLI Reference](cli.md) for flags and subcommands.

---

## Agent configuration

Agent invocation is defined in `ralph/core/agent_runner.py` (research loop) and `ralph/core/skill_runner.py` (RRD creation).

### Claude Code

Invoked with:
```bash
claude -p "$PROMPT" \
  --dangerously-skip-permissions \
  --allowedTools "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch"
```

### Amp

Invoked with:
```bash
echo "$PROMPT" | amp --dangerously-allow-all
```

### Codex

Invoked with:
```bash
echo "$PROMPT" | codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --output-last-message "$TEMP_FILE" -
```

---

## Rate limit configuration

Defined in `AGENTS.md` and `prompt.md` and applied by the agent:

| Source | Delay | Retry on 429 | Retry on 403 |
|--------|-------|--------------|--------------|
| arXiv API | 3s | Yes (60s) | No |
| Google Scholar | 5s | Yes | No |
| GitHub API | 1s | Yes | No |
| WebSearch | 2s | Yes | No |

To modify: edit `AGENTS.md` (keep `CLAUDE.md` in sync).

---

## Retry configuration

Built into `ralph/core/agent_runner.py` (RETRY_CONFIG) and `ralph/core/research_loop.py`:

| Setting | Value |
|---------|-------|
| Max consecutive failures | Configurable (`max_consecutive_failures`, default 3) |
| 429 retry delay | 30s |
| Network error retry delay | 2s |
| Timeout retry delay | 2s |

---

## File locations

Default paths:

| File | Purpose | Configurable |
|------|---------|--------------|
| `~/.research-ralph/config.yaml` | CLI config | Yes |
| `researches/` | Research folders (common convention) | No |
| `prompt.md` | Agent instructions | No |
| `AGENTS.md` | Patterns/gotchas | No |
| `skills/` | Skill definitions | No |

---

## Customization examples

### Stricter scoring

Only present papers scoring 22+:
```json
"requirements": {
  "min_score_to_present": 22
}
```

### Longer time window

Look back 90 days for papers:
```json
"requirements": {
  "time_window_days": 90
}
```

### More papers

Collect 50 papers before analysis:
```json
"requirements": {
  "target_papers": 50
}
```

### arXiv only

Disable other sources:
```json
"requirements": {
  "sources": ["arXiv"]
}
```

### Add domain terms

Help the agent understand jargon:
```json
"domain_glossary": {
  "enabled": true,
  "terms": {
    "RL": "Reinforcement Learning",
    "RLHF": "Reinforcement Learning from Human Feedback",
    "PPO": "Proximal Policy Optimization"
  }
}
```

---

## Related documentation

- [RRD Schema](rrd-schema.md) - Complete field-by-field reference
- [Customizing Research](../tutorials/customizing-research.md) - Hands-on customization guide
- [Handle Rate Limits](../how-to/handle-rate-limits.md) - Rate limit configuration in practice
- [Switch Agents](../how-to/switch-agents.md) - Agent-specific configuration
