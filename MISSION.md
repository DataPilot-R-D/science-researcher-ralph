# Research-Ralph Mission

## Primary Objective

Discover research with **blue ocean potential**: innovations that create new markets rather than compete in existing ones.

The goal is to find papers that could become products, features, or competitive advantages for a small team — prioritizing opportunities where you can **define** the market rather than fight for share in crowded spaces.

---

## Success Metrics

A successful research run should achieve:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Blue Ocean Papers | >= 20% of presented | Papers with `blue_ocean_score >= 12` |
| Market Creation Signals | >= 3 insights | Insights tagged with undefined/emerging market |
| First-Mover Opportunities | >= 2 papers | Papers with `first_mover_window >= 12 months` |
| Strategic Clarity | 100% of presented | All presented papers have clear positioning statement |
| Implementation Path | >= 50% of presented | Papers with GitHub repos or clear build path |

---

## Blue Ocean Framework

### What is Blue Ocean?

Blue ocean strategy focuses on **creating uncontested market space** rather than competing in existing "red ocean" markets where competitors fight over shrinking profits.

For research scouting, this means prioritizing papers that:
- **Define new problem categories** (not incremental improvements)
- **Enable capabilities that don't exist yet** (not faster/cheaper versions)
- **Create demand** rather than serve existing demand
- **Have compounding value** (network effects, data moats, ecosystem lock-in)

### Red Ocean vs Blue Ocean Examples

| Red Ocean (Avoid) | Blue Ocean (Target) |
|-------------------|---------------------|
| "Faster transformer inference" | "Zero-shot robot learning from video" |
| "Better object detection accuracy" | "Self-supervised 3D world models" |
| "Improved chatbot responses" | "AI agents that autonomously debug code" |
| "More efficient fine-tuning" | "Models that learn from single demonstrations" |

---

## Blue Ocean Evaluation Rubric

Score each paper 0-5 on four strategic dimensions (total 0-20):

### 1. Market Creation (0-5)

**Question:** Does this create a new market or compete in an existing one?

| Score | Criteria | Example |
|-------|----------|---------|
| 5 | Creates entirely new category | First VLA (Vision-Language-Action) models |
| 4 | Opens adjacent market | Applying LLMs to robotics control |
| 3 | Serves underserved segment | Enterprise-focused AI agents |
| 2 | Better mousetrap in known market | Faster diffusion sampling |
| 1 | Me-too product | Another chatbot framework |
| 0 | Saturated/commodity market | Generic image classifiers |

### 2. First-Mover Window (0-5)

**Question:** How long before competitors can replicate this?

| Score | Window | Factors That Extend Window |
|-------|--------|---------------------------|
| 5 | > 24 months | Novel architecture + proprietary data + complex training |
| 4 | 18-24 months | Novel architecture + significant engineering |
| 3 | 12-18 months | New approach but reproducible with effort |
| 2 | 6-12 months | Clear methodology, moderate complexity |
| 1 | 3-6 months | Well-documented, easy to replicate |
| 0 | < 3 months | Simple technique, already being copied |

### 3. Network/Data Effects (0-5)

**Question:** Does the value compound over time with usage?

| Score | Effect Type | Example |
|-------|-------------|---------|
| 5 | Strong network effects | Each user/deployment makes product better for all |
| 4 | Data flywheel | More usage = more data = better model = more usage |
| 3 | High switching costs | Deep integration, custom training, workflow lock-in |
| 2 | Brand/trust moat | Reputation-based advantage only |
| 1 | Weak lock-in | Easy to switch, commodity APIs |
| 0 | No compounding | Value doesn't increase with scale |

### 4. Strategic Clarity (0-5)

**Question:** How focused and clear is the opportunity?

| Score | Clarity Level | Indicator |
|-------|--------------|-----------|
| 5 | Single clear use case | "This solves X for Y" in one sentence |
| 4 | 2-3 related applications | Clear primary + adjacent opportunities |
| 3 | Platform potential | Could enable multiple products (risky but high upside) |
| 2 | Too broad | "Can be used for anything" = unfocused |
| 1 | Unclear positioning | Hard to explain who needs this |
| 0 | Confused/contradictory | Claims don't match capabilities |

---

## Scoring Integration

### Combined Score Formula

```
combined_score = execution_score + blue_ocean_score
               = (novelty + feasibility + time_to_poc + value_market + defensibility + adoption)
               + (market_creation + first_mover_window + network_effects + strategic_clarity)
               = 0-30 (execution) + 0-20 (blue ocean) = 0-50 total
```

### Decision Thresholds

| Combined Score | Decision | Rationale |
|----------------|----------|-----------|
| >= 35 | **PRESENT (Priority)** | Exceptional execution + strong blue ocean |
| >= 25 | **PRESENT** | Strong overall score |
| 18-24 | **EXTRACT_INSIGHTS** | Valuable learnings, not primary candidate |
| < 18 | **REJECT** | Not viable or too competitive |

### Alternative Decision Path

Even if combined score < 25, consider **EXTRACT_INSIGHTS** if:
- `execution_score >= 18` (technically solid, weak strategy)
- `blue_ocean_score >= 12` (strategic potential, execution challenges)

---

## Per-Research Customization

Override mission parameters in your `rrd.json`:

```json
{
  "mission": {
    "blue_ocean_scoring": true,
    "min_blue_ocean_score": 12,
    "min_combined_score": 25,
    "strategic_focus": "balanced"
  }
}
```

### Strategic Focus Presets

| Preset | Emphasis | Use When |
|--------|----------|----------|
| `market_creation` | Market Creation 2x weight | Looking for category-defining opportunities |
| `defensibility` | First-Mover + Network Effects 2x | Building durable competitive advantages |
| `speed` | Time-to-POC + Strategic Clarity 2x | Need rapid market entry |
| `balanced` | Equal weights (default) | General research scouting |

---

## Agent Directives

When analyzing papers, you MUST:

1. **Score both rubrics** — Execution (0-30) AND Blue Ocean (0-20)
2. **Classify the market** — Is this red ocean, purple ocean, or blue ocean?
3. **Estimate first-mover window** — Consider: research maturity, implementation complexity, data requirements, competitive landscape
4. **Identify compounding effects** — Network effects, data moats, ecosystem lock-in, switching costs
5. **Assess strategic clarity** — Can you explain the opportunity in one sentence?
6. **Note commercial signals** — Existing companies, acquisitions, funding in this space

### Score Breakdown Format

Store scores in this structure:

```json
{
  "score_breakdown": {
    "execution": {
      "novelty": 4,
      "feasibility": 3,
      "time_to_poc": 3,
      "value_market": 4,
      "defensibility": 3,
      "adoption": 4
    },
    "blue_ocean": {
      "market_creation": 4,
      "first_mover_window": 3,
      "network_effects": 3,
      "strategic_clarity": 4
    },
    "execution_total": 21,
    "blue_ocean_total": 14,
    "combined_total": 35
  }
}
```

---

## Examples

### True Blue Ocean (Combined: 42/50)

```
Paper: "Learning Robot Manipulation from Human Video Without Actions"

Execution Score: 24/30
- Novelty: 5 (First to eliminate action labels entirely)
- Feasibility: 4 (Requires video data, not robot demonstrations)
- Time-to-POC: 3 (Novel architecture, moderate complexity)
- Value/Market: 5 (Huge demand for easier robot training)
- Defensibility: 4 (Architectural innovations + training recipe)
- Adoption: 3 (Needs integration work)

Blue Ocean Score: 18/20
- Market Creation: 5 (New category: video-only robot learning)
- First-Mover Window: 5 (24+ months due to novel approach)
- Network Effects: 4 (Data flywheel from deployments)
- Strategic Clarity: 4 (Clear use case + adjacent applications)

Decision: PRESENT (Priority) — Category-defining opportunity
```

### Red Ocean (Combined: 26/50)

```
Paper: "Accelerating Transformer Inference with Dynamic Sparsity"

Execution Score: 20/30
- Novelty: 3 (Incremental improvement on known techniques)
- Feasibility: 4 (Well-documented approach)
- Time-to-POC: 4 (Clear implementation path)
- Value/Market: 4 (Performance always valued)
- Defensibility: 2 (Easy to replicate)
- Adoption: 3 (Requires model changes)

Blue Ocean Score: 6/20
- Market Creation: 1 (Crowded inference optimization space)
- First-Mover Window: 1 (Similar papers already appearing)
- Network Effects: 2 (Some switching costs)
- Strategic Clarity: 2 (Generic "faster inference" positioning)

Decision: EXTRACT_INSIGHTS — Technical value but no strategic differentiation
```

---

## Value to User

Research-Ralph with blue ocean scoring delivers:

| Value | Description |
|-------|-------------|
| **Strategic filtering** | Don't waste time on papers in crowded markets |
| **Market timing** | Identify first-mover windows before they close |
| **Defensibility focus** | Prioritize opportunities with lasting advantages |
| **Clear positioning** | Every presented paper has a crisp opportunity statement |
| **Actionable output** | Papers scored for both "can we build it?" AND "should we build it?" |

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-15 | Initial version with blue ocean framework | Research-Ralph |
