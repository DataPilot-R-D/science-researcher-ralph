---
name: rrd
description: "Generate a Research Requirements Document (RRD) for a research topic. Use when scouting for papers, analyzing research areas, or when asked to create research requirements. Triggers on: create rrd, research requirements, scout papers, analyze research, find papers."
---

# RRD Generator

Create detailed Research Requirements Documents that guide autonomous research scouting.

---

## The Job

1. Receive a research topic/area description from the user
2. Infer focus area and keywords from the topic
3. Generate RRD with sensible defaults
4. **Set a clear, concise `project` name** (3-6 words describing the research focus)
   - Example: `"project": "Research: Blockchain KVM Robot Operations"`
   - This becomes the directory name, so make it meaningful
5. Add `open_questions` if topic is ambiguous
6. Save to `rrd.json`

**Important:** Do NOT start researching. Just create the RRD.

---

## Autonomous Generation

Generate the RRD immediately without asking questions. Use these defaults:

| Field | Default |
|-------|---------|
| `time_window_days` | 90 |
| `target_papers` | 20 |
| `min_score_to_present` | 18 |
| `sources` | ["arXiv", "Google Scholar", "web"] |
| `mission.blue_ocean_scoring` | true |
| `mission.min_combined_score` | 25 |

**Infer from topic description:**
- `focus_area` - Primary research domain (robotics, NLP, ML, etc.)
- `keywords` - 5-8 specific, searchable terms related to the topic
- `description` - Clear research objective

**If the topic is ambiguous**, add questions to `open_questions` array:

```json
"open_questions": [
  {
    "field": "focus_area",
    "question": "Should this focus on theoretical foundations or practical implementations?",
    "options": ["A: Theoretical", "B: Practical", "C: Both"],
    "current_default": "Both"
  }
]
```

**At the end, if there are open questions, output this warning:**

```
---
RRD saved to: {path}/rrd.json

WARNING: There are open questions in the RRD. Review and edit rrd.json before running ralph.sh:
- {list each question}
```

---

## RRD Structure

Generate the RRD with these fields:

### Required Fields

```json
{
  "project": "Research: [Topic Name]",
  "branchName": "research/[topic-slug]",
  "description": "Clear description of research objective and what we're looking for",

  "mission": {
    "blue_ocean_scoring": true,
    "min_blue_ocean_score": 12,
    "min_combined_score": 25,
    "strategic_focus": "balanced"
  },

  "requirements": {
    "focus_area": "Primary domain (robotics, NLP, etc.)",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "time_window_days": 90,
    "historical_lookback_days": 1095,
    "target_papers": 20,
    "sources": ["arXiv", "Google Scholar", "web"],
    "min_score_to_present": 18
  },

  "domain_glossary": {
    "enabled": false,
    "terms": {}
  },

  "open_questions": [],

  "phase": "DISCOVERY",

  "timing": {
    "research_started_at": "<ISO8601 timestamp when RRD created>",
    "discovery": {
      "started_at": "<same as research_started_at>",
      "ended_at": null,
      "duration_seconds": null
    },
    "analysis": {
      "started_at": null,
      "ended_at": null,
      "duration_seconds": null,
      "papers_analyzed": 0,
      "avg_seconds_per_paper": null
    },
    "complete": {
      "ended_at": null
    }
  },

  "papers_pool": [],
  "insights": [],
  "visited_urls": [],
  "blocked_sources": [],
  "statistics": {
    "total_discovered": 0,
    "total_analyzed": 0,
    "total_presented": 0,
    "total_rejected": 0,
    "total_insights_extracted": 0,
    "discovery_metrics": {
      "sources_tried": [],
      "sources_successful": [],
      "sources_blocked": [],
      "source_failure_reasons": {}
    },
    "analysis_metrics": {
      "avg_combined_score": 0,
      "avg_execution_score": 0,
      "avg_blue_ocean_score": 0,
      "combined_score_distribution": {"0-17": 0, "18-24": 0, "25-34": 0, "35-50": 0},
      "blue_ocean_distribution": {"0-7": 0, "8-11": 0, "12-15": 0, "16-20": 0}
    }
  }
}
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| `project` | Human-readable project name |
| `branchName` | Topic identifier used for archive folder naming (not git branches) |
| `description` | What we're researching and why |
| `mission` | Blue ocean scoring configuration (see below) |
| `focus_area` | Primary research domain |
| `keywords` | Search terms for paper discovery |
| `time_window_days` | How recent papers should be |
| `historical_lookback_days` | Fallback window for foundational papers (optional, default: 1095 = 3 years) |
| `target_papers` | How many papers to collect |
| `sources` | Where to search (arXiv, Scholar, web) |
| `min_score_to_present` | Threshold score (0-30) for PRESENT decision (legacy, use mission.min_combined_score) |
| `phase` | Current phase: DISCOVERY, ANALYSIS, or COMPLETE |
| `timing` | Phase timestamps for progress tracking (see Timing Configuration below) |
| `domain_glossary` | Optional: domain-specific term definitions to improve LLM reasoning |
| `open_questions` | Questions for user to answer if topic was ambiguous |
| `discovery_metrics` | Tracks which sources were tried, succeeded, or blocked |
| `analysis_metrics` | Tracks average score and score distribution |

#### Mission Configuration

| Field | Description |
|-------|-------------|
| `mission.blue_ocean_scoring` | Enable strategic blue ocean scoring (default: true) |
| `mission.min_blue_ocean_score` | Minimum blue ocean score (0-20) for EXTRACT_INSIGHTS (default: 12) |
| `mission.min_combined_score` | Minimum combined score (0-50) for PRESENT (default: 25) |
| `mission.strategic_focus` | Focus preset: "balanced", "market_creation", "defensibility", "speed" |

#### Timing Configuration

| Field | Description |
|-------|-------------|
| `timing.research_started_at` | ISO8601 timestamp when RRD was created |
| `timing.discovery.started_at` | When DISCOVERY phase began (same as research_started_at) |
| `timing.discovery.ended_at` | When DISCOVERY phase ended |
| `timing.discovery.duration_seconds` | Calculated duration of DISCOVERY phase |
| `timing.analysis.started_at` | When ANALYSIS phase began |
| `timing.analysis.ended_at` | When ANALYSIS phase ended |
| `timing.analysis.duration_seconds` | Calculated duration of ANALYSIS phase |
| `timing.analysis.papers_analyzed` | Count of papers analyzed (for avg calculation) |
| `timing.analysis.avg_seconds_per_paper` | Average time per paper analysis |
| `timing.complete.ended_at` | When research was fully completed |

**RRD Generator initializes:** `research_started_at` and `discovery.started_at` with current ISO8601 timestamp.

---

## Evaluation Rubric

Papers are scored on TWO rubrics (see `MISSION.md` for full criteria):

**Execution Rubric (0-30):**
1. **Novelty/Differentiation** - How new is this approach?
2. **Implementation Feasibility** - Can a small team build this?
3. **Time-to-POC** - How quickly can we prototype?
4. **Value/Market Pull** - Is there clear demand?
5. **Defensibility/Moat** - What's the competitive advantage?
6. **Adoption Friction** - How easy to deploy? (higher = easier)

**Blue Ocean Rubric (0-20):**
7. **Market Creation** - New market or existing competition?
8. **First-Mover Window** - Time until competitors replicate?
9. **Network/Data Effects** - Does value compound over time?
10. **Strategic Clarity** - How focused is the opportunity?

**Decision Thresholds (Combined 0-50):**
- Combined >= 35 = **PRESENT (Priority)** — Blue ocean opportunity
- Combined >= 25 = **PRESENT** — Strong overall score
- Combined 18-24 with Execution >= 18 OR Blue Ocean >= 12 = **EXTRACT_INSIGHTS**
- Otherwise = **REJECT**

Include this rubric explanation in the RRD description or notes if the user needs context.

---

## Output

- **Format:** JSON
- **Location:** Research folder (path provided at end of prompt)
- **Filename:** `rrd.json`
- The research folder path will be provided in the "Output Location" section at the end of the prompt

---

## Example RRD

```json
{
  "project": "Research: Robotics & Embodied AI",
  "branchName": "research/robotics-embodied-ai",
  "description": "Scout recent advances in robotics, embodied AI, and sim2real transfer. Focus on papers with implementation potential for a small startup team. Looking for novel manipulation techniques, efficient sim2real methods, and practical robot learning approaches.",

  "mission": {
    "blue_ocean_scoring": true,
    "min_blue_ocean_score": 12,
    "min_combined_score": 25,
    "strategic_focus": "balanced"
  },

  "requirements": {
    "focus_area": "robotics",
    "keywords": [
      "embodied AI",
      "robot manipulation",
      "sim2real transfer",
      "dexterous manipulation",
      "robot learning",
      "visuomotor policy"
    ],
    "time_window_days": 90,
    "historical_lookback_days": 1095,
    "target_papers": 20,
    "sources": ["arXiv", "Google Scholar", "web"],
    "min_score_to_present": 18
  },

  "domain_glossary": {
    "enabled": true,
    "terms": {
      "DoF": "Degrees of Freedom",
      "EEF": "End Effector",
      "sim2real": "Simulation to Real-world Transfer",
      "VLA": "Vision-Language-Action model"
    }
  },

  "open_questions": [],

  "phase": "DISCOVERY",

  "timing": {
    "research_started_at": "2025-01-15T10:00:00Z",
    "discovery": {
      "started_at": "2025-01-15T10:00:00Z",
      "ended_at": null,
      "duration_seconds": null
    },
    "analysis": {
      "started_at": null,
      "ended_at": null,
      "duration_seconds": null,
      "papers_analyzed": 0,
      "avg_seconds_per_paper": null
    },
    "complete": {
      "ended_at": null
    }
  },

  "papers_pool": [],
  "insights": [],
  "visited_urls": [],
  "blocked_sources": [],
  "statistics": {
    "total_discovered": 0,
    "total_analyzed": 0,
    "total_presented": 0,
    "total_rejected": 0,
    "total_insights_extracted": 0,
    "discovery_metrics": {
      "sources_tried": [],
      "sources_successful": [],
      "sources_blocked": [],
      "source_failure_reasons": {}
    },
    "analysis_metrics": {
      "avg_combined_score": 0,
      "avg_execution_score": 0,
      "avg_blue_ocean_score": 0,
      "combined_score_distribution": {"0-17": 0, "18-24": 0, "25-34": 0, "35-50": 0},
      "blue_ocean_distribution": {"0-7": 0, "8-11": 0, "12-15": 0, "16-20": 0}
    }
  }
}
```

---

## Checklist

Before saving the RRD:

- [ ] Set concise `project` name (3-6 words, becomes directory name)
- [ ] Inferred focus_area from topic description
- [ ] Generated 5-8 specific, searchable keywords
- [ ] Used sensible defaults for time_window, target_papers, sources
- [ ] Added open_questions if any ambiguity exists
- [ ] Saved to the research folder path provided in the prompt
- [ ] Printed warning if open_questions is non-empty
