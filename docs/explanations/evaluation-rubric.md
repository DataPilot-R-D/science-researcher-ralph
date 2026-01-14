# Evaluation Rubric Explained

Research-Ralph evaluates papers using a 6-dimension scoring rubric. This document explains each dimension and how scores translate to decisions.

## Overview

Each paper is scored 0-5 on six dimensions, giving a total score of 0-30:

| Score | Meaning |
|-------|---------|
| 0 | Not applicable / No evidence |
| 1 | Very poor |
| 2 | Below average |
| 3 | Average |
| 4 | Good |
| 5 | Excellent |

## The Six Dimensions

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

## Decision Thresholds

Based on total score (0-30):

| Score Range | Decision | Meaning |
|-------------|----------|---------|
| >= 18 | **PRESENT** | Worth investigating further |
| 12-17 | **EXTRACT_INSIGHTS** | Not a primary candidate, but has valuable learnings |
| < 12 | **REJECT** | Not relevant or not feasible |

The default threshold (`min_score_to_present`) is 18, but can be adjusted in `rrd.json`.

## Score Distribution

Track how papers are distributed across score ranges:

```json
"score_distribution": {
  "0-11": 3,   // Rejected
  "12-17": 5, // Extract insights
  "18-23": 4, // Presented (solid)
  "24-30": 2  // Presented (excellent)
}
```

## Customizing Thresholds

Adjust `min_score_to_present` in your `rrd.json`:

```json
"requirements": {
  "min_score_to_present": 20  // Stricter (default: 18)
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

## Tips for Consistent Scoring

1. **Calibrate early**: Score a few papers, then review consistency
2. **Document reasoning**: The agent should explain each dimension's score
3. **Consider context**: A 3 in "Novelty" for a mature field is different from a new field
4. **Look at the total**: Individual scores matter less than the overall picture
5. **Extract insights anyway**: Even low-scoring papers can have valuable findings
