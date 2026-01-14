# How to Manage Multiple Research Projects

Research-Ralph organizes each research topic into its own folder, making it easy to run multiple projects concurrently or switch between them.

## Folder Structure

Each research project lives in `researches/`:

```
researches/
├── robotics-llms-2026-01-14/
│   ├── rrd.json
│   ├── progress.txt
│   └── research-report.md
├── quantum-computing-2026-01-15/
│   ├── rrd.json
│   └── progress.txt
└── nlp-transformers-2026-01-16/
    ├── rrd.json
    └── progress.txt
```

## Creating Multiple Projects

```bash
# Create first research
./skill.sh rrd "Research robotics and embodied AI"
# Creates: researches/research-robotics-and-embodied-2026-01-14/

# Create second research
./skill.sh rrd "Research quantum computing applications"
# Creates: researches/research-quantum-computing-2026-01-14/

# Create third research
./skill.sh rrd "Research NLP transformers"
# Creates: researches/research-nlp-transformers-2026-01-14/
```

## Listing All Projects

```bash
# Simple list
ls researches/

# With details
ls -la researches/

# See status of each project
for dir in researches/*/; do
  echo "=== $(basename "$dir") ==="
  cat "$dir/rrd.json" | jq '{phase, analyzed: .statistics.total_analyzed, presented: .statistics.total_presented}'
done
```

## Running Projects

### Sequential (One at a Time)

```bash
# Run first project
./ralph.sh researches/robotics-llms-2026-01-14

# When done, run second project
./ralph.sh researches/quantum-computing-2026-01-15
```

### Concurrent (Multiple Terminals)

Open multiple terminal windows/tabs:

```bash
# Terminal 1
./ralph.sh researches/robotics-llms-2026-01-14

# Terminal 2
./ralph.sh researches/quantum-computing-2026-01-15
```

Note: Be mindful of rate limits when running concurrently.

## Checking Project Status

```bash
# Quick status for one project
cat researches/robotics-llms-2026-01-14/rrd.json | jq '.phase, .statistics'

# Compare all projects
for dir in researches/*/; do
  name=$(basename "$dir")
  phase=$(cat "$dir/rrd.json" | jq -r '.phase')
  analyzed=$(cat "$dir/rrd.json" | jq -r '.statistics.total_analyzed')
  presented=$(cat "$dir/rrd.json" | jq -r '.statistics.total_presented')
  echo "$name: $phase ($analyzed analyzed, $presented presented)"
done
```

## Git Workflow

Track each project's progress with git:

```bash
# After running research
git add researches/robotics-llms-2026-01-14/
git commit -m "analysis: robotics research - 5 papers analyzed"

# Track multiple projects
git add researches/
git commit -m "research: progress on robotics and quantum projects"
```

## Archiving Completed Research

Move completed projects to a separate location:

```bash
# Create archive directory (outside researches/)
mkdir -p archive/

# Move completed project
mv researches/robotics-llms-2026-01-14 archive/

# Or keep in researches/ and rename
mv researches/robotics-llms-2026-01-14 researches/DONE-robotics-llms-2026-01-14
```

## Tips

- **Naming**: Folder names are auto-generated from your topic description + date
- **Isolation**: Each project is completely independent
- **Resumable**: Switch between projects freely - state is preserved
- **Cleanup**: Delete a folder to remove a project entirely
