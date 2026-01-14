# How to Extract and Use Research Insights

Research-Ralph extracts insights from every paper it analyzes, even rejected ones. This guide shows how to work with these insights.

## Understanding Insights

Insights are valuable findings extracted during paper analysis:
- Key techniques or methods
- Implementation details
- Limitations or challenges
- Cross-references to other papers
- Emerging patterns

## Viewing Insights

### All Insights
```bash
cat researches/your-folder/rrd.json | jq '.insights'
```

### Insights with Context
```bash
cat researches/your-folder/rrd.json | jq '.insights[] | {insight: .text, source: .source_paper, type: .type}'
```

### Count Insights
```bash
cat researches/your-folder/rrd.json | jq '.insights | length'
```

## Insight Structure

Each insight in `rrd.json` typically contains:

```json
{
  "text": "The insight content",
  "source_paper": "arxiv_2401.12345",
  "type": "technique|limitation|trend|cross_reference",
  "extracted_at": "2026-01-14T10:30:00Z"
}
```

## Finding Specific Insights

### By Type
```bash
# Find all technique insights
cat researches/your-folder/rrd.json | jq '.insights[] | select(.type == "technique")'

# Find cross-references
cat researches/your-folder/rrd.json | jq '.insights[] | select(.type == "cross_reference")'
```

### By Keyword
```bash
# Find insights mentioning "transformer"
cat researches/your-folder/rrd.json | jq '.insights[] | select(.text | test("transformer"; "i"))'
```

### From Specific Paper
```bash
# Find insights from a specific paper
cat researches/your-folder/rrd.json | jq '.insights[] | select(.source_paper == "arxiv_2401.12345")'
```

## Cross-Reference Clusters

Research-Ralph identifies papers that relate to each other:

```bash
# Find cluster insights
cat researches/your-folder/rrd.json | jq '.insights[] | select(.cross_cluster != null)'
```

Clusters might include:
- Papers using the same benchmark
- Papers from the same research group
- Competing approaches to the same problem

## Using Insights for Reports

### Export to Markdown
```bash
echo "# Research Insights" > insights.md
echo "" >> insights.md
cat researches/your-folder/rrd.json | jq -r '.insights[] | "- **[\(.source_paper)]**: \(.text)"' >> insights.md
```

### Group by Type
```bash
echo "# Insights by Type" > insights-grouped.md

echo "## Techniques" >> insights-grouped.md
cat researches/your-folder/rrd.json | jq -r '.insights[] | select(.type == "technique") | "- \(.text)"' >> insights-grouped.md

echo "## Limitations" >> insights-grouped.md
cat researches/your-folder/rrd.json | jq -r '.insights[] | select(.type == "limitation") | "- \(.text)"' >> insights-grouped.md
```

## Combining with Paper Data

Link insights back to full paper information:

```bash
# For each insight, show the paper's title and score
cat researches/your-folder/rrd.json | jq '
  .insights[] as $insight |
  .papers_pool[] | select(.id == $insight.source_paper) |
  {
    insight: $insight.text,
    paper_title: .title,
    paper_score: .score,
    paper_status: .status
  }
'
```

## Progress.txt for Detailed Context

The `progress.txt` file contains narrative context around insights:

```bash
# Search for insight-related entries
grep -A 5 "insight\|finding\|notable" researches/your-folder/progress.txt
```

## Tips

- **Don't ignore rejected papers**: They often contain valuable insights about what doesn't work
- **Look for patterns**: Multiple insights pointing to the same technique suggest importance
- **Cross-reference clusters**: Papers in the same cluster may share implementation approaches
- **Check progress.txt**: Contains more detailed reasoning than the structured JSON
