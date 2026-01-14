# How to Resume Interrupted Research

Research-Ralph is designed to be resumable. If your research session is interrupted, you can pick up exactly where you left off.

## Why Research Can Be Interrupted

- Network connectivity issues
- Rate limits from sources (arXiv, GitHub)
- System restarts or terminal closures
- Manually stopping the process (Ctrl+C)

## Resuming Research

Simply run the same command again:

```bash
./ralph.sh researches/your-research-folder
```

Research-Ralph automatically:
1. Reads the current state from `rrd.json`
2. Identifies papers with `status: "pending"` or `status: "analyzing"`
3. Continues from where it stopped

## Check Current State Before Resuming

```bash
# See phase and progress
cat researches/your-folder/rrd.json | jq '{phase, analyzed: .statistics.total_analyzed, target: .requirements.target_papers}'

# Count pending papers
cat researches/your-folder/rrd.json | jq '[.papers_pool[] | select(.status == "pending")] | length'

# See what was being analyzed when interrupted
cat researches/your-folder/rrd.json | jq '.papers_pool[] | select(.status == "analyzing")'
```

## Handling Stuck "analyzing" Status

If a paper is stuck with `status: "analyzing"` (interrupted mid-analysis), Research-Ralph will re-analyze it on the next run.

To manually reset it to pending:
```bash
# View the stuck paper
cat researches/your-folder/rrd.json | jq '.papers_pool[] | select(.status == "analyzing")'

# Reset using jq (backup first!)
cp researches/your-folder/rrd.json researches/your-folder/rrd.json.backup
jq '(.papers_pool[] | select(.status == "analyzing")).status = "pending"' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

## Running More Iterations

If you hit the iteration limit without completing:

```bash
# Run 20 more iterations
./ralph.sh researches/your-folder 20
```

## Troubleshooting

**"All papers analyzed but no COMPLETE signal"**
- Check if any papers have `status: "analyzing"` (stuck)
- Verify `papers_pool` isn't empty

**"Agent keeps failing"**
- Check `progress.txt` for error details
- Verify network connectivity
- Check if sources are rate-limited (see [Handle Rate Limits](handle-rate-limits.md))
