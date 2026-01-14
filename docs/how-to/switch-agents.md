# How to Use Different AI Agents

Research-Ralph supports three AI agent backends. Choose based on your preferences and available subscriptions.

## Available Agents

| Agent | Default | Command Flag |
|-------|---------|--------------|
| Claude Code | Yes | `--agent claude` |
| Amp | No | `--agent amp` |
| Codex | No | `--agent codex` |

## Switching Agents

### For ralph.sh (Research Loop)

```bash
# Use Claude Code (default)
./ralph.sh researches/your-folder

# Use Amp
./ralph.sh researches/your-folder --agent amp

# Use Codex
./ralph.sh researches/your-folder --agent codex
```

### For skill.sh (Creating RRDs)

```bash
# Use Claude Code (default)
./skill.sh rrd "Your research topic"

# Use Amp
./skill.sh rrd "Your research topic" --agent amp

# Use Codex
./skill.sh rrd "Your research topic" --agent codex
```

## Agent Installation

### Claude Code
```bash
# Install from https://claude.ai/code
# Verify installation
claude --version
```

### Amp
```bash
# Install from https://ampcode.com
# Verify installation
amp --version
```

### Codex
```bash
# Install from https://openai.com/codex
# Verify installation
codex --version
```

## Mixing Agents

You can use different agents for different phases:

```bash
# Create RRD with Claude
./skill.sh rrd "Quantum computing research"

# Run research with Amp
./ralph.sh researches/quantum-computing-2026-01-14 --agent amp
```

The research state is stored in `rrd.json`, so any agent can continue work started by another.

## Agent-Specific Notes

### Claude Code
- Uses `--dangerously-skip-permissions` for autonomous operation
- Allowed tools: Bash, Read, Edit, Write, Grep, Glob, WebFetch, WebSearch

### Amp
- Uses `--dangerously-allow-all` flag
- Receives prompt via stdin

### Codex
- Uses `--dangerously-bypass-approvals-and-sandbox`
- Outputs captured via `--output-last-message`

## Troubleshooting

**"Agent not found in PATH"**
- Ensure the CLI is installed and in your PATH
- Check with: `which claude` / `which amp` / `which codex`

**"Authentication failed"**
- Re-authenticate with the agent's CLI
- Check your subscription/API access
