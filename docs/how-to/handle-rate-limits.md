# How to Handle Rate Limits and Blocks

Research-Ralph accesses multiple external sources that may impose rate limits. This guide explains how to handle them.

## Common Rate Limit Errors

| Error Code | Source | Meaning |
|------------|--------|---------|
| 429 | Any | Too Many Requests |
| 403 | Any | Forbidden (often rate limit or block) |
| 503 | arXiv | Service temporarily unavailable |

## Automatic Handling

Research-Ralph handles rate limits automatically:

1. **429 errors**: Waits 30 seconds, then retries
2. **403 errors**: Skips to next source
3. **3 consecutive failures**: Adds source to `blocked_sources` and moves on

Check `progress.txt` for rate limit events:
```bash
grep -i "rate\|limit\|blocked\|429\|403" researches/your-folder/progress.txt
```

## GitHub API Rate Limits

GitHub has strict rate limits for unauthenticated requests.

### Unauthenticated
- **Limit**: 10 requests/minute
- **Symptoms**: Frequent 403 errors when checking for implementations

### Authenticated (Recommended)
- **Limit**: 30 requests/minute

Set your GitHub token:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Create a token at: https://github.com/settings/tokens
- Required scope: `public_repo` (read-only access)

Add to your shell profile for persistence:
```bash
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
# or ~/.zshrc for zsh
```

## arXiv Rate Limits

arXiv is conservative with rate limits.

**Best practices**:
- Research-Ralph adds 3-second delays between requests
- If blocked, wait and retry later
- Avoid running multiple research sessions simultaneously

## Google Scholar

Google Scholar aggressively blocks automated access.

**If blocked**:
- Research-Ralph falls back to other sources
- Source gets added to `blocked_sources`
- Manual browser access may work (CAPTCHA)

## Checking Blocked Sources

```bash
cat researches/your-folder/rrd.json | jq '.blocked_sources'
```

## Resetting Blocked Sources

If you want to retry a previously blocked source:

```bash
# Backup first
cp researches/your-folder/rrd.json researches/your-folder/rrd.json.backup

# Clear blocked sources
jq '.blocked_sources = []' researches/your-folder/rrd.json > tmp.json && mv tmp.json researches/your-folder/rrd.json
```

## Source Fallback Strategy

When a source fails, Research-Ralph uses this hierarchy:

**For paper discovery**:
1. arXiv API
2. Google Scholar
3. Web search

**For implementation checks**:
1. GitHub API
2. arXiv (code links)
3. Semantic Scholar
4. Web search

## Reducing Rate Limit Issues

1. **Set GITHUB_TOKEN**: Most impactful improvement
2. **Run one project at a time**: Avoid concurrent requests
3. **Use reasonable iteration counts**: Don't rush discovery
4. **Wait between runs**: If heavily rate-limited, wait 10-15 minutes

## Troubleshooting

**"All sources blocked"**
- Wait 15-30 minutes for rate limits to reset
- Check your network (VPN/proxy issues)
- Try with GITHUB_TOKEN set

**"GitHub keeps returning 403"**
- Verify GITHUB_TOKEN is set: `echo $GITHUB_TOKEN`
- Check token hasn't expired
- Verify token has correct scopes

**"arXiv returning 503"**
- arXiv may be under maintenance
- Check https://status.arxiv.org
- Wait and retry later
