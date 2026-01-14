# Documentation Plan: Research-Ralph

## Overview

- **Target Audience:** Developers/Researchers who want to run autonomous research scouting
- **Documentation Standard:** Diátaxis (Tutorials, How-To, Explanations, Reference)
- **Estimated Documents:** 12 documents
- **Current State:** README.md is comprehensive but outdated (doesn't reflect per-research folders)

---

## Gap Analysis

### Existing Documentation

| Document | Status | Issue |
|----------|--------|-------|
| `README.md` | **Outdated** | Shows old workflow (root rrd.json), not per-research folders |
| `CLAUDE.md` | Current | Good technical reference, updated for v2.1 |
| `AGENTS.md` | Current | Synced with CLAUDE.md |
| `skills/rrd/SKILL.md` | Current | RRD skill documentation |
| `rrd.json.example` | Current | Example RRD format |

### Missing Documentation

- Getting started tutorial (step-by-step first run)
- How-to guides for common tasks
- Architecture explanation
- Configuration reference
- Troubleshooting guide

---

## Tutorials (Learning-Oriented)

### 1. Getting Started Tutorial
- **Priority:** HIGH
- **Purpose:** First-time user onboarding - run first research in 10 minutes
- **Covers:**
  - Prerequisites check (jq, Claude/Amp/Codex CLI)
  - Creating first RRD with skill.sh
  - Running research with ralph.sh
  - Understanding the output
- **Estimated length:** 1,000-1,500 words
- **Prerequisites:** None
- **Location:** `docs/tutorials/getting-started.md`

### 2. Customizing Research Parameters Tutorial
- **Priority:** MEDIUM
- **Purpose:** Learn to tailor research to specific needs
- **Covers:**
  - Understanding RRD fields
  - Adjusting keywords and time windows
  - Setting scoring thresholds
  - Adding domain glossary
- **Estimated length:** 800-1,000 words
- **Prerequisites:** Getting Started
- **Location:** `docs/tutorials/customizing-research.md`

---

## How-To Guides (Task-Oriented)

### 1. How to Resume Interrupted Research
- **Priority:** HIGH
- **Purpose:** Continue research after interruption
- **Covers:** Checking status, rerunning ralph.sh, handling errors
- **Estimated length:** 400-600 words
- **Location:** `docs/how-to/resume-research.md`

### 2. How to Use Different AI Agents
- **Priority:** MEDIUM
- **Purpose:** Switch between Claude, Amp, and Codex
- **Covers:** Agent flags, authentication, performance differences
- **Estimated length:** 500-700 words
- **Location:** `docs/how-to/switch-agents.md`

### 3. How to Manage Multiple Research Projects
- **Priority:** HIGH
- **Purpose:** Run and organize multiple concurrent research topics
- **Covers:** Per-research folders, switching between projects, git workflow
- **Estimated length:** 500-700 words
- **Location:** `docs/how-to/multiple-projects.md`

### 4. How to Handle Rate Limits and Blocks
- **Priority:** MEDIUM
- **Purpose:** Deal with API rate limits from arXiv, GitHub, etc.
- **Covers:** GITHUB_TOKEN setup, fallback sources, blocked_sources field
- **Estimated length:** 400-600 words
- **Location:** `docs/how-to/handle-rate-limits.md`

### 5. How to Extract and Use Research Insights
- **Priority:** MEDIUM
- **Purpose:** Work with the insights extracted during research
- **Covers:** Insights structure, cross-references, generating reports
- **Estimated length:** 500-700 words
- **Location:** `docs/how-to/use-insights.md`

---

## Explanations (Understanding-Oriented)

### 1. Architecture Overview
- **Priority:** HIGH
- **Purpose:** Explain how Research-Ralph works internally
- **Covers:**
  - Stateless iteration model
  - Memory persistence (rrd.json, progress.txt)
  - Two-phase workflow (DISCOVERY → ANALYSIS)
  - Agent invocation mechanism
- **Estimated length:** 1,500-2,000 words
- **Location:** `docs/explanations/architecture.md`

### 2. Evaluation Rubric Explained
- **Priority:** MEDIUM
- **Purpose:** Deep dive into paper scoring methodology
- **Covers:**
  - Six dimensions explained with examples
  - How scores translate to decisions
  - Customizing thresholds
- **Estimated length:** 800-1,000 words
- **Location:** `docs/explanations/evaluation-rubric.md`

---

## Reference (Information-Oriented)

### 1. RRD Schema Reference
- **Priority:** HIGH
- **Purpose:** Complete field-by-field RRD documentation
- **Format:** Structured reference with types, defaults, examples
- **Location:** `docs/reference/rrd-schema.md`

### 2. CLI Reference
- **Priority:** HIGH
- **Purpose:** All CLI commands and options
- **Covers:**
  - `ralph.sh` - all arguments and flags
  - `skill.sh` - all arguments and flags
  - Exit codes and error messages
- **Location:** `docs/reference/cli.md`

### 3. Configuration Reference
- **Priority:** MEDIUM
- **Purpose:** All configurable options
- **Covers:**
  - Environment variables (GITHUB_TOKEN)
  - RRD settings
  - Agent-specific options
- **Location:** `docs/reference/configuration.md`

---

## Immediate Actions

### 1. Update README.md (Priority: CRITICAL)

The README is outdated and shows the old workflow. Update to reflect v2.1:

**Current (wrong):**
```bash
./ralph.sh [max_iterations]
```

**Should be:**
```bash
./skill.sh rrd "Topic"  # Creates researches/{topic}-{date}/
./ralph.sh researches/{folder} [iterations]
```

**Changes needed:**
- Update Quick Start section with new folder-based workflow
- Update Key Files table (add researches/ folder)
- Remove/update Archiving section (archive/ no longer used)
- Update all command examples
- Remove reference to ralph.webp (file deleted)

---

## Recommended Document Creation Order

1. **README.md update** (Critical - blocks user onboarding)
2. **Getting Started Tutorial** (Unblocks new users)
3. **CLI Reference** (Unblocks power users)
4. **How to Manage Multiple Projects** (Key v2.1 feature)
5. **Architecture Overview** (Helps understanding)
6. **RRD Schema Reference** (Complete reference)
7. **How to Resume Interrupted Research** (Common need)
8. **How to Handle Rate Limits** (Common issue)
9. **Remaining how-to guides**
10. **Remaining tutorials and explanations**

---

## Proposed Folder Structure

```
docs/
├── DOCUMENTATION_PLAN.md     # This file
├── tutorials/
│   ├── getting-started.md
│   └── customizing-research.md
├── how-to/
│   ├── resume-research.md
│   ├── switch-agents.md
│   ├── multiple-projects.md
│   ├── handle-rate-limits.md
│   └── use-insights.md
├── explanations/
│   ├── architecture.md
│   └── evaluation-rubric.md
└── reference/
    ├── rrd-schema.md
    ├── cli.md
    └── configuration.md
```

---

## Timeline Suggestion

| Phase | Documents | Est. Effort |
|-------|-----------|-------------|
| **Phase 1** | README.md update | 30 min |
| **Phase 2** | Getting Started, CLI Reference | 2-3 hours |
| **Phase 3** | Architecture, RRD Schema | 2-3 hours |
| **Phase 4** | How-to guides (5) | 3-4 hours |
| **Phase 5** | Remaining tutorials, explanations | 2-3 hours |

**Total estimated effort:** 10-14 hours

---

## Next Steps

1. [ ] Review and approve this plan
2. [ ] Update README.md immediately (critical)
3. [ ] Create docs/ folder structure
4. [ ] Write Getting Started tutorial
5. [ ] Iterate based on user feedback
