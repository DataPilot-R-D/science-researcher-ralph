# Customizing Research Parameters

This tutorial teaches you how to tailor Research-Ralph to your specific needs by adjusting keywords, thresholds, time windows, and other settings.

## Prerequisites

- Completed the [Getting Started](getting-started.md) tutorial
- Have a research folder with `rrd.json`

## Understanding the RRD

The Research Requirements Document (`rrd.json`) controls all research behavior. Open your RRD:

```bash
cat researches/your-folder/rrd.json | jq '.requirements'
```

You'll see something like:
```json
{
  "focus_area": "robotics",
  "keywords": ["embodied AI", "robot manipulation"],
  "time_window_days": 30,
  "target_papers": 20,
  "sources": ["arXiv", "Google Scholar", "web"],
  "min_score_to_present": 18
}
```
Mission thresholds live under `mission` and control combined scoring (see Step 3).

## Step 1: Refine Your Keywords

Keywords determine what papers Research-Ralph finds. Good keywords are:
- **Specific**: "transformer attention mechanism" not just "AI"
- **Varied**: Include synonyms and related terms
- **Domain-appropriate**: Use terminology from your field

### Adding Keywords

```bash
# View current keywords
cat researches/your-folder/rrd.json | jq '.requirements.keywords'

# Add a keyword
jq '.requirements.keywords += ["new keyword"]' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

### Example: Robotics Research

```json
"keywords": [
  "embodied AI",
  "robot manipulation",
  "sim2real transfer",
  "dexterous manipulation",
  "visuomotor policy",
  "vision-language-action"
]
```

### Example: NLP Research

```json
"keywords": [
  "large language models",
  "transformer architecture",
  "instruction tuning",
  "RLHF",
  "chain-of-thought",
  "in-context learning"
]
```

## Step 2: Adjust the Time Window

The `time_window_days` controls how recent papers should be.

| Setting | Use Case |
|---------|----------|
| 7 | Cutting-edge, conference deadlines |
| 30 | Recent developments (default) |
| 90 | Quarterly survey |
| 365 | Annual review |

```bash
# Set to 90 days
jq '.requirements.time_window_days = 90' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

For foundational papers, use `historical_lookback_days`:
```bash
# Look back 3 years for seminal papers
jq '.requirements.historical_lookback_days = 1095' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

## Step 3: Set Your Scoring Threshold

Primary thresholds live under `mission`:

| Field | Range | Meaning |
|-------|-------|---------|
| `mission.min_combined_score` | 0-50 | Minimum combined score to present |
| `mission.min_blue_ocean_score` | 0-20 | Minimum blue ocean score when strategic scoring is enabled |

`requirements.min_score_to_present` is a legacy execution-only threshold.

```bash
# Stricter combined threshold
jq '.mission.min_combined_score = 30' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json

# Raise the blue ocean minimum
jq '.mission.min_blue_ocean_score = 14' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

See [Evaluation Rubric](../explanations/evaluation-rubric.md) for how scores work.

## Step 4: Configure Sources

Control where Research-Ralph searches:

```json
"sources": ["arXiv", "Google Scholar", "web"]
```

| Source | Best For |
|--------|----------|
| arXiv | CS, physics, math preprints |
| Google Scholar | Broader academic coverage |
| web | Implementations, blog posts |

### arXiv Only (Fastest, Most Reliable)

```bash
jq '.requirements.sources = ["arXiv"]' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

### All Sources (Most Comprehensive)

```bash
jq '.requirements.sources = ["arXiv", "Google Scholar", "web"]' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

## Step 5: Add Domain Glossary

Help the AI understand domain-specific terms:

```bash
# Enable glossary and add terms
jq '.domain_glossary = {
  "enabled": true,
  "terms": {
    "VLA": "Vision-Language-Action model",
    "DoF": "Degrees of Freedom",
    "EEF": "End Effector",
    "sim2real": "Simulation to Real-world Transfer"
  }
}' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

This improves the agent's understanding when reading papers.

## Step 6: Set Target Paper Count

Adjust `target_papers` based on your needs:

| Count | Use Case |
|-------|----------|
| 5-10 | Quick survey, focused topic |
| 15-25 | Standard survey (default: 20) |
| 30-50 | Comprehensive review |
| 50+ | Exhaustive coverage |

```bash
# Quick survey
jq '.requirements.target_papers = 10' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

## Complete Example: Custom Configuration

Here's a fully customized RRD for a specific use case:

```json
{
  "project": "Research: Vision-Language Models for Robotics",
  "branchName": "research/vlm-robotics",
  "description": "Survey VLM applications in robot manipulation, focusing on practical implementations",

  "mission": {
    "blue_ocean_scoring": true,
    "min_blue_ocean_score": 12,
    "min_combined_score": 28,
    "strategic_focus": "balanced"
  },

  "requirements": {
    "focus_area": "robotics",
    "keywords": [
      "vision-language-action",
      "VLA robot",
      "multimodal robot learning",
      "language-conditioned manipulation"
    ],
    "time_window_days": 60,
    "historical_lookback_days": 730,
    "target_papers": 15,
    "sources": ["arXiv", "web"]
  },

  "domain_glossary": {
    "enabled": true,
    "terms": {
      "VLA": "Vision-Language-Action model",
      "RT-1": "Robotics Transformer 1",
      "RT-2": "Robotics Transformer 2",
      "OpenVLA": "Open Vision-Language-Action model"
    }
  }
}
```

## Verification

After customizing, verify your changes:

```bash
# Check all requirements
cat researches/your-folder/rrd.json | jq '.requirements'

# Validate JSON is still valid
jq empty researches/your-folder/rrd.json && echo "Valid JSON"

# Run research with new settings
research-ralph --run researches/your-folder
```

## Tips

1. **Start narrow, then broaden**: Begin with specific keywords, add more if you don't find enough papers
2. **Check progress.txt**: See what searches are working and adjust
3. **Iterate**: Run a few iterations, check results, then refine
4. **Backup before editing**: `cp rrd.json rrd.json.backup`

## Common Customization Patterns

### Academic Literature Review
```json
"mission": { "min_combined_score": 22 },
"time_window_days": 365,
"target_papers": 50,
"sources": ["arXiv", "Google Scholar"]
```

### Startup Technology Scouting
```json
"mission": { "min_combined_score": 28 },
"time_window_days": 30,
"target_papers": 20,
"sources": ["arXiv", "web"]
```

### Conference Preparation
```json
"mission": { "min_combined_score": 25 },
"time_window_days": 7,
"target_papers": 10,
"sources": ["arXiv"]
```

---

## Related Documentation

- [RRD Schema Reference](../reference/rrd-schema.md) - Complete field documentation
- [Configuration Reference](../reference/configuration.md) - All configurable options
- [Evaluation Rubric](../explanations/evaluation-rubric.md) - Understanding scores
- [Getting Started](getting-started.md) - First-time setup
