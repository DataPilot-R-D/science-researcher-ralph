---
name: rrd
description: "Generate a Research Requirements Document (RRD) for a research topic. Use when scouting for papers, analyzing research areas, or when asked to create research requirements. Triggers on: create rrd, research requirements, scout papers, analyze research, find papers."
---

# RRD Generator

Create detailed Research Requirements Documents that guide autonomous research scouting.

---

## The Job

1. Receive a research topic/area description from the user
2. Ask 3-5 essential clarifying questions (with lettered options)
3. Generate a structured RRD based on answers
4. Save to `rrd.json`

**Important:** Do NOT start researching. Just create the RRD.

---

## Step 1: Clarifying Questions

Ask only critical questions where the initial prompt is ambiguous. Focus on:

- **Focus Area:** What's the primary research domain?
- **Keywords:** What specific topics/terms to search for?
- **Time Window:** How recent should the papers be?
- **Depth:** How many papers to analyze?
- **Criteria:** What makes a paper worth presenting?

### Format Questions Like This:

```
1. What is the primary research focus?
   A. Robotics & embodied AI
   B. Machine learning / deep learning
   C. Natural language processing
   D. Computer vision
   E. Other: [please specify]

2. How far back should we look for papers?
   A. Last 7 days (very recent)
   B. Last 30 days (recent)
   C. Last 90 days (quarter)
   D. Last 365 days (year)

3. How many papers should we target for analysis?
   A. 5-10 (quick survey)
   B. 10-20 (standard survey)
   C. 20-50 (comprehensive survey)
   D. 50+ (exhaustive survey)

4. What's most important when evaluating papers?
   A. Novel approaches/methods
   B. Implementation feasibility for small teams
   C. Commercial/market potential
   D. Academic rigor/citations
   E. Combination of above

5. Which sources should we prioritize?
   A. arXiv only
   B. arXiv + Google Scholar
   C. arXiv + Google Scholar + Web (blogs, GitHub)
   D. All sources equally
```

This lets users respond with "1A, 2B, 3B, 4E, 5C" for quick iteration.

---

## Step 2: RRD Structure

Generate the RRD with these fields:

### Required Fields

```json
{
  "project": "Research: [Topic Name]",
  "branchName": "research/[topic-slug]",
  "description": "Clear description of research objective and what we're looking for",

  "requirements": {
    "focus_area": "Primary domain (robotics, NLP, etc.)",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "time_window_days": 30,
    "target_papers": 20,
    "sources": ["arXiv", "Google Scholar", "web"],
    "min_score_to_present": 18
  },

  "phase": "DISCOVERY",
  "papers_pool": [],
  "insights": [],
  "presented": [],
  "rejected": [],
  "visited_urls": [],
  "blocked_sources": [],
  "statistics": {
    "total_discovered": 0,
    "total_analyzed": 0,
    "total_presented": 0,
    "total_rejected": 0,
    "total_insights_extracted": 0
  }
}
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| `project` | Human-readable project name |
| `branchName` | Topic identifier used for archive folder naming (not git branches) |
| `description` | What we're researching and why |
| `focus_area` | Primary research domain |
| `keywords` | Search terms for paper discovery |
| `time_window_days` | How recent papers should be |
| `target_papers` | How many papers to collect |
| `sources` | Where to search (arXiv, Scholar, web) |
| `min_score_to_present` | Threshold score (0-30) for PRESENT decision |
| `phase` | Current phase: DISCOVERY, ANALYSIS, or COMPLETE |

---

## Evaluation Rubric

Papers are scored 0-5 on each dimension (total 0-30):

1. **Novelty/Differentiation** - How new is this approach?
2. **Implementation Feasibility** - Can a small team build this?
3. **Time-to-POC** - How quickly can we prototype?
4. **Value/Market Pull** - Is there clear demand?
5. **Defensibility/Moat** - What's the competitive advantage?
6. **Adoption Friction** - How easy to deploy? (higher = easier)

**Threshold:** Score >= 18 → PRESENT, else REJECT or EXTRACT_INSIGHTS

Include this rubric explanation in the RRD description or notes if the user needs context.

---

## Output

- **Format:** JSON
- **Location:** Project root
- **Filename:** `rrd.json`

---

## Example RRD

```json
{
  "project": "Research: Robotics & Embodied AI",
  "branchName": "research/robotics-embodied-ai",
  "description": "Scout recent advances in robotics, embodied AI, and sim2real transfer. Focus on papers with implementation potential for a small startup team. Looking for novel manipulation techniques, efficient sim2real methods, and practical robot learning approaches.",

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
    "time_window_days": 30,
    "target_papers": 20,
    "sources": ["arXiv", "Google Scholar", "web"],
    "min_score_to_present": 18
  },

  "phase": "DISCOVERY",
  "papers_pool": [],
  "insights": [],
  "presented": [],
  "rejected": [],
  "visited_urls": [],
  "blocked_sources": [],
  "statistics": {
    "total_discovered": 0,
    "total_analyzed": 0,
    "total_presented": 0,
    "total_rejected": 0,
    "total_insights_extracted": 0
  }
}
```

---

## Checklist

Before saving the RRD:

- [ ] Asked clarifying questions with lettered options
- [ ] Incorporated user's answers
- [ ] Keywords are specific and searchable
- [ ] Time window matches user's needs
- [ ] Target paper count is realistic
- [ ] Sources are appropriate for the domain
- [ ] Saved to `rrd.json`
