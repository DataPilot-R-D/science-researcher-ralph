# Evaluation Rubric Explained

Research-Ralph evaluates papers using a **dual scoring system**: an Execution rubric (0-30) and a Blue Ocean rubric (0-20), giving a combined score of 0-50.

## Overview

Papers are scored on **TWO rubrics**:

1. **Execution Rubric (0-30)**: Can we build this? Is it feasible?
2. **Blue Ocean Rubric (0-20)**: Should we build this? Is it strategically valuable?

### Score Meanings

Each dimension is scored 0-5:

| Score | Meaning |
|-------|---------|
| 0 | Not applicable / No evidence |
| 1 | Very poor |
| 2 | Below average |
| 3 | Average |
| 4 | Good |
| 5 | Excellent |

## Execution Rubric (0-30)

The six execution dimensions assess implementation viability:

### 1. Novelty / Differentiation (0-5)

**Question**: How new or different is this approach?

| Score | Criteria |
|-------|----------|
| 5 | Completely new paradigm, no prior work |
| 4 | Significant innovation on existing methods |
| 3 | Meaningful improvement with novel elements |
| 2 | Incremental improvement |
| 1 | Minor variation of existing work |
| 0 | Direct copy or already well-known |

**What to look for**:
- Novel architectures or algorithms
- New combinations of existing techniques
- First application to a new domain
- Breakthrough results on benchmarks

### 2. Implementation Feasibility (0-5)

**Question**: Can a small team build this?

| Score | Criteria |
|-------|----------|
| 5 | Can implement in days with standard tools |
| 4 | Weeks of work, well-documented approach |
| 3 | Months of work, requires some expertise |
| 2 | Significant resources or rare expertise needed |
| 1 | Requires large team or special hardware |
| 0 | Impractical for small teams |

**What to look for**:
- Code availability (GitHub, etc.)
- Hardware requirements (GPUs, TPUs, robots)
- Data requirements
- Dependencies on proprietary systems
- Clear methodology description

### 3. Time-to-POC (0-5)

**Question**: How quickly can we prototype this?

| Score | Criteria |
|-------|----------|
| 5 | Days (code available, simple setup) |
| 4 | 1-2 weeks |
| 3 | 1 month |
| 2 | 2-3 months |
| 1 | 6+ months |
| 0 | Unclear or very long timeline |

**What to look for**:
- Existing implementations
- Standard libraries/frameworks used
- Clear reproducibility instructions
- Availability of pretrained models
- Test datasets accessibility

### 4. Value / Market Pull (0-5)

**Question**: Is there clear demand for this?

| Score | Criteria |
|-------|----------|
| 5 | Solves urgent, well-funded problem |
| 4 | Clear market need, active buyers |
| 3 | Growing interest, some demand signals |
| 2 | Potential need, not yet validated |
| 1 | Nice to have, unclear demand |
| 0 | Academic interest only |

**What to look for**:
- Industry applications mentioned
- Commercial partners or funding
- Real-world deployment examples
- Market size indicators
- Pain points addressed

### 5. Defensibility / Moat (0-5)

**Question**: What's the competitive advantage?

| Score | Criteria |
|-------|----------|
| 5 | Patentable, unique data, or network effects |
| 4 | Significant expertise barrier |
| 3 | First-mover advantage possible |
| 2 | Some differentiation potential |
| 1 | Easily replicated |
| 0 | Commodity approach |

**What to look for**:
- Patent potential
- Unique datasets or data collection methods
- Proprietary training techniques
- Integration complexity (harder to switch)
- Brand/trust requirements

### 6. Adoption Friction (0-5)

**Question**: How easy is it to deploy?

| Score | Criteria |
|-------|----------|
| 5 | Drop-in replacement, no changes needed |
| 4 | Minor integration work |
| 3 | Moderate changes required |
| 2 | Significant workflow changes |
| 1 | Major infrastructure changes |
| 0 | Complete system overhaul needed |

**What to look for**:
- API compatibility
- Standard interfaces
- Migration path from existing solutions
- Training requirements for users
- Regulatory considerations

---

## Blue Ocean Rubric (0-20)

The four blue ocean dimensions assess strategic value and market positioning. See `MISSION.md` for the full framework.

### 7. Market Creation (0-5)

**Question**: Does this create a new market or compete in existing?

| Score | Criteria |
|-------|----------|
| 5 | Creates entirely new category |
| 4 | Opens adjacent market |
| 3 | Serves underserved segment |
| 2 | Better mousetrap in known market |
| 1 | Me-too product |
| 0 | Saturated/commodity market |

**What to look for**:
- Is this solving a problem no one else is solving?
- Does it create new demand vs serving existing demand?
- Could this define a new product category?

### 8. First-Mover Window (0-5)

**Question**: How long before competitors can replicate?

| Score | Criteria |
|-------|----------|
| 5 | 24+ months |
| 4 | 18-24 months |
| 3 | 12-18 months |
| 2 | 6-12 months |
| 1 | 3-6 months |
| 0 | <3 months |

**What to look for**:
- How novel is the architecture?
- Are there proprietary data requirements?
- How complex is the training/implementation?
- Is the paper already widely cited/replicated?

### 9. Network/Data Effects (0-5)

**Question**: Does value compound over time?

| Score | Criteria |
|-------|----------|
| 5 | Strong network effects (each user adds value) |
| 4 | Data flywheel (more data = better product) |
| 3 | High switching costs |
| 2 | Brand loyalty only |
| 1 | Weak lock-in |
| 0 | No compounding effects |

**What to look for**:
- Does usage generate valuable data?
- Do more users make the product better?
- Is there ecosystem integration potential?
- What are the switching costs?

### 10. Strategic Clarity (0-5)

**Question**: How focused is the opportunity?

| Score | Criteria |
|-------|----------|
| 5 | Single, clear use case |
| 4 | 2-3 related applications |
| 3 | Platform potential |
| 2 | Too broad / unfocused |
| 1 | Unclear positioning |
| 0 | Confused / contradictory |

**What to look for**:
- Can you explain the use case in one sentence?
- Is the target customer clear?
- Are there too many potential applications (lack of focus)?

---

## Decision Thresholds

Based on combined score (0-50):

| Combined Score | Decision | Meaning |
|----------------|----------|---------|
| >= 35 | **PRESENT (Priority)** | Blue ocean opportunity — high strategic value |
| >= 25 | **PRESENT** | Strong overall score |
| 18-24 | **EXTRACT_INSIGHTS** | Not a primary candidate, but valuable learnings |
| < 18 | **REJECT** | Not relevant or not feasible |

**Alternative paths to EXTRACT_INSIGHTS** (even if combined < 25):
- Execution score >= 18 (technically solid, weak strategy)
- Blue Ocean score >= 12 (strategic potential, execution challenges)

The default threshold (`min_combined_score`) is 25, but can be adjusted in `rrd.json`.

## Score Distribution

Track how papers are distributed across score ranges:

```json
"analysis_metrics": {
  "avg_combined_score": 32,
  "avg_execution_score": 21,
  "avg_blue_ocean_score": 11,
  "combined_score_distribution": {
    "0-17": 2,    // Rejected
    "18-24": 5,   // Extract insights
    "25-34": 8,   // Presented (solid)
    "35-50": 5    // Presented (priority)
  },
  "blue_ocean_distribution": {
    "0-7": 3,     // Red ocean
    "8-11": 7,    // Purple ocean
    "12-15": 6,   // Blue ocean adjacent
    "16-20": 4    // True blue ocean
  }
}
```

## Customizing Thresholds

Adjust thresholds in your `rrd.json`:

```json
"mission": {
  "blue_ocean_scoring": true,
  "min_combined_score": 30,   // Stricter (default: 25)
  "min_blue_ocean_score": 14  // Require stronger strategic value (default: 12)
}
```

**When to raise the threshold**:
- You want only the best papers
- You're getting too many presentations
- The domain is well-researched

**When to lower the threshold**:
- Exploring a new domain
- Want broader coverage
- Papers are consistently scoring low

**When to disable blue ocean scoring**:
- For pure technical research (no commercialization focus)
- Set `"blue_ocean_scoring": false` in the mission config

## Tips for Consistent Scoring

1. **Calibrate early**: Score a few papers, then review consistency
2. **Document reasoning**: The agent should explain each dimension's score
3. **Consider context**: A 3 in "Novelty" for a mature field is different from a new field
4. **Look at the total**: Individual scores matter less than the overall picture
5. **Extract insights anyway**: Even low-scoring papers can have valuable findings

---

## Related Documentation

- [Architecture Overview](architecture.md) - How scoring fits into the ANALYSIS phase
- [Configuration Reference](../reference/configuration.md) - Adjusting `min_score_to_present`
- [Use Research Insights](../how-to/use-insights.md) - Working with extracted findings
- [Customizing Research](../tutorials/customizing-research.md) - Tailoring scoring thresholds
