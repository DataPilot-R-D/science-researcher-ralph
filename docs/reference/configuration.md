# Configuration Reference

All configurable options for Research-Ralph.

## Environment Variables

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

## RRD Configuration

All settings in `rrd.json` under `requirements`:

### Search Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `focus_area` | string | - | Primary domain (robotics, NLP, etc.) |
| `keywords` | string[] | - | Search terms |
| `time_window_days` | number | 30 | Recent paper window |
| `historical_lookback_days` | number | 1095 | Foundational paper window |
| `target_papers` | number | 20 | Papers to collect |
| `sources` | string[] | ["arXiv", "Google Scholar", "web"] | Search sources |

### Evaluation Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_score_to_present` | number | 18 | PRESENT threshold (0-30) |

### Adjusting Settings

Edit `rrd.json` directly:

```bash
# View current settings
cat researches/your-folder/rrd.json | jq '.requirements'

# Modify (example: change threshold to 20)
jq '.requirements.min_score_to_present = 20' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

---

## Script Options

### ralph.sh

| Option | Default | Description |
|--------|---------|-------------|
| `<research_folder>` | (required) | Path to research folder |
| `[max_iterations]` | 10 | Maximum loop iterations |
| `--agent <name>` | claude | Agent: claude, amp, codex |

### skill.sh

| Option | Default | Description |
|--------|---------|-------------|
| `<skill_name>` | (required) | Skill to run (e.g., rrd) |
| `"<description>"` | (required) | Task description |
| `--agent <name>` | claude | Agent: claude, amp, codex |
| `--list` | - | List available skills |

---

## Agent Configuration

### Claude Code

Invoked with:
```bash
claude -p "$PROMPT" \
  --dangerously-skip-permissions \
  --allowedTools "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch"
```

Allowed tools can be modified in `ralph.sh` (line ~167).

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

## Rate Limit Configuration

Built into `ralph.sh` (not configurable via file):

| Source | Delay | Retry on 429 | Retry on 403 |
|--------|-------|--------------|--------------|
| arXiv API | 3s | Yes (60s) | No |
| Google Scholar | 5s | Yes | No |
| GitHub API | 1s | Yes | No |
| WebSearch | 2s | Yes | No |

To modify: edit `ralph.sh` or `AGENTS.md` (which the agent reads).

---

## Retry Configuration

Built into `ralph.sh`:

| Setting | Value | Location |
|---------|-------|----------|
| Max consecutive failures | 3 | Line ~229 |
| 429 retry delay | 30s | Line ~255 |
| Network error retry delay | 2s | Lines ~268-272 |
| Timeout retry delay | 2s | Lines ~268-272 |

---

## File Locations

Default paths (relative to project root):

| File | Purpose | Configurable |
|------|---------|--------------|
| `researches/` | Research folders | No |
| `prompt.md` | Agent instructions | No (path in ralph.sh) |
| `AGENTS.md` | Patterns/gotchas | No |
| `skills/` | Skill definitions | No |

---

## Customization Examples

### Stricter Scoring

Only present papers scoring 22+:
```json
"requirements": {
  "min_score_to_present": 22
}
```

### Longer Time Window

Look back 90 days for papers:
```json
"requirements": {
  "time_window_days": 90
}
```

### More Papers

Collect 50 papers before analysis:
```json
"requirements": {
  "target_papers": 50
}
```

### arXiv Only

Disable other sources:
```json
"requirements": {
  "sources": ["arXiv"]
}
```

### Add Domain Terms

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

## Related Documentation

- [RRD Schema](rrd-schema.md) - Complete field-by-field reference
- [Customizing Research](../tutorials/customizing-research.md) - Hands-on customization guide
- [Handle Rate Limits](../how-to/handle-rate-limits.md) - Rate limit configuration in practice
- [Switch Agents](../how-to/switch-agents.md) - Agent-specific configuration
