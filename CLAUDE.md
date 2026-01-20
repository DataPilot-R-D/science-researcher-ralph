# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Research-Ralph is an autonomous research scouting agent that discovers, analyzes, and evaluates research papers. It runs an AI agent (Claude Code, Amp, or Codex) repeatedly until all papers in the Research Requirements Document (RRD) are analyzed.

## Sync Policy

Keep research patterns and gotchas in this file in sync with `AGENTS.md`. When updating one, update the other.

## Doc Safety (Rollback)

If automated edits to `AGENTS.md` / `CLAUDE.md` go wrong, restore from baseline:
- Baseline copies: `docs-baseline/AGENTS.md`, `docs-baseline/CLAUDE.md` (do not edit these)
- Restore command: `./restore-docs.sh`
- If you approve the current docs as the new baseline: `cp AGENTS.md docs-baseline/AGENTS.md && cp CLAUDE.md docs-baseline/CLAUDE.md`

## Git Workflow (Checkpoints)

Use git commits as checkpoints so research progress is easy to track and revert:
- Commit after each iteration (and any milestone like phase change)
- Stage files from the research folder: `researches/{name}/rrd.json`, `researches/{name}/progress.txt`
- Commit message examples:
  - `discovery: add N papers`
  - `analysis: <paper_id> <PRESENT|REJECT|EXTRACT_INSIGHTS> (<score>/50)`
  - `docs: update research patterns/workflow`
  - `milestone: phase -> <DISCOVERY|ANALYSIS|COMPLETE>`

## Commands

```bash
# Create a new research (creates folder in researches/)
./skill.sh rrd "Your research topic description"
# Creates: researches/{topic}-{date}/rrd.json

# List all research projects with status
./ralph.sh --list

# Show detailed status of a specific research
./ralph.sh --status researches/{folder-name}

# Reset research to DISCOVERY phase (creates backup)
./ralph.sh --reset researches/{folder-name}

# Run research on a folder
./ralph.sh researches/{folder-name} [options]

# Commands:
#   --list                List all research projects with color-coded status
#   --status <folder>     Show detailed status with progress bar
#   --reset <folder>      Reset research to DISCOVERY phase (creates backup)
#   -h, --help            Show help message

# Run Options:
#   -p, --papers <N>      Target papers count (auto-sets iterations to N+6)
#   -i, --iterations <N>  Override max iterations (default: auto-calculated)
#   --agent <name>        AI agent: 'claude', 'amp', or 'codex' (default: claude)
#   --force               Allow -p to change target_papers on in-progress research

# Examples
./ralph.sh --list                                             # List all researches
./ralph.sh --status researches/robotics-llms-2026-01-14       # Check status
./ralph.sh --reset researches/robotics-llms-2026-01-14        # Reset to start
./ralph.sh researches/robotics-llms-2026-01-14                # Run research
./ralph.sh researches/robotics-llms-2026-01-14 -p 30          # 30 papers, 36 iterations
./ralph.sh researches/robotics-llms-2026-01-14 -p 30 -i 100   # Override iterations
./ralph.sh researches/robotics-llms-2026-01-14 --agent amp    # Use Amp agent
./ralph.sh researches/robotics-llms-2026-01-14 -p 50 --force  # Force change target

# List available skills
./skill.sh --list
```

## Architecture

### Core Loop (`ralph.sh`)
1. Parses research folder path (required) and `--agent` flag
2. Reads `rrd.json` and `progress.txt` from the research folder
3. Invokes the selected agent with `prompt.md`
   - Claude: `claude -p "..." --dangerously-skip-permissions --allowedTools "..."`
   - Amp: `cat prompt.md | amp --dangerously-allow-all`
   - Codex: `codex exec --dangerously-bypass-approvals-and-sandbox -`
4. Checks output for `<promise>COMPLETE</promise>` to exit
5. Repeats until completion or max iterations reached

### Memory Model
Each iteration is stateless. Cross-iteration memory is limited to:
- `researches/{name}/rrd.json` (papers pool, status, insights, statistics)
- `researches/{name}/progress.txt` (detailed findings log with patterns at top)
- `AGENTS.md` (reusable research patterns)

### Folder Structure
```
researches/
├── robotics-llms-2026-01-14/
│   ├── rrd.json           # Research requirements and paper data
│   ├── progress.txt       # Research findings log
│   ├── research-report.md # Generated after analysis
│   └── product-ideas.json # Generated product opportunities
└── quantum-ai-2026-01-15/
    ├── rrd.json
    └── progress.txt
```

### Key Files
| File/Folder | Purpose |
|-------------|---------|
| `ralph.sh` | Main research loop script |
| `skill.sh` | Skill runner (creates research folders for rrd skill) |
| `prompt.md` | Agent instructions for research workflow |
| `MISSION.md` | Agent objectives, success metrics, blue ocean scoring |
| `researches/` | Per-research artifact folders |
| `researches/{name}/rrd.json` | Research Requirements Document |
| `researches/{name}/progress.txt` | Research findings log |
| `researches/{name}/research-report.md` | Auto-generated comprehensive report |
| `researches/{name}/product-ideas.json` | Product opportunities with traceability |
| `rrd.json.example` | Example RRD format for reference |
| `skills/rrd/SKILL.md` | Skill for generating RRDs |

## Research Workflow

### Three Phases

**DISCOVERY Phase:**
- Search arXiv, Google Scholar, web for papers
- Collect papers matching keywords and criteria
- Assign initial priority scores (1-5)
- Transition to ANALYSIS when target count reached

**ANALYSIS Phase:**
- ONE paper per iteration (deep analysis)
- Read full paper content (not just abstract)
- Search for implementations (GitHub, blogs)
- Check if commercialized
- Score using dual rubric (Execution 0-30 + Blue Ocean 0-20 = 0-50 combined)
- Decide: PRESENT / REJECT / EXTRACT_INSIGHTS
- Generate `research-report.md` when all papers analyzed
- Transition to IDEATION

**IDEATION Phase:**
- Synthesize research into product opportunities
- Generate `product-ideas.json` with 3-12 ideas
- Each idea includes: problem, solution, evidence, risks, scores
- Full traceability to source papers and insights
- Transition to COMPLETE when done

### Evaluation Rubric

Papers scored on **TWO rubrics** (see `MISSION.md` for full criteria):

**Execution Rubric (0-30):**

| Dimension | Question |
|-----------|----------|
| Novelty | How new/different is this approach? |
| Feasibility | Can a small team build this? |
| Time-to-POC | How quickly can we prototype? |
| Value/Market | Is there clear demand? |
| Defensibility | What's the competitive advantage? |
| Adoption | How easy to deploy? |

**Blue Ocean Rubric (0-20):**

| Dimension | Question |
|-----------|----------|
| Market Creation | New market or existing competition? |
| First-Mover Window | Time until competitors replicate? |
| Network/Data Effects | Does value compound over time? |
| Strategic Clarity | How focused is the opportunity? |

**Decision Thresholds:**
- Combined >= 35 = **PRESENT (Priority)** — Blue ocean opportunity
- Combined >= 25 = **PRESENT** — Strong overall score
- Combined 18-24 with Execution >= 18 OR Blue Ocean >= 12 = **EXTRACT_INSIGHTS**
- Otherwise = **REJECT**

## RRD Format

The `rrd.json` file contains:
- `project`, `branchName`, `description` - Research metadata
- `mission` - Blue ocean scoring config (optional, enables strategic scoring)
- `requirements` - Keywords, time window, target papers, sources
- `phase` - DISCOVERY, ANALYSIS, IDEATION, or COMPLETE
- `papers_pool` - All discovered papers with status and analysis
- `insights` - Extracted valuable findings
- `statistics` - Counts for tracking progress

## Stop Condition

When all papers are analyzed, Research-Ralph transitions to IDEATION to generate product ideas. After generating `product-ideas.json`, it outputs `<promise>COMPLETE</promise>` to exit the loop.

## Source Access Patterns

### arXiv API

```
https://export.arxiv.org/api/query?search_query=all:{keyword}&sortBy=submittedDate&sortOrder=descending&max_results=50
```

- Free, no auth required
- Rate limit: Be conservative - 1 request per 3 seconds to avoid blocks
- Returns Atom XML feed

### Google Scholar

- Use WebSearch with keywords
- Add `site:scholar.google.com` for direct results
- Often returns abstracts only (need to follow PDF links)

### PDF Access

- arXiv: Replace `/abs/` with `/pdf/` in URL, add `.pdf`
- Most papers: Check for PDF link in metadata
- Some require institutional access

## Common Gotchas

- **Rate limits:** arXiv blocks rapid requests; add delays between searches
- **Paywalls:** Some papers not freely accessible; note in `blocked_sources`
- **Stale data:** Scholar results can be cached; check dates
- **Web search blocks:** DuckDuckGo HTML can trigger bot challenges; use GitHub API or alternate sources
- **TechRxiv/Cloudflare blocks:** TechRxiv can return 403 “Just a moment…” bot challenges for HTML/PDF; try DOI to find mirrors (arXiv/Zenodo/author site), use OpenAlex for metadata, and mark as blocked after repeated failures. If full text is needed, DuckDuckGo HTML (via `r.jina.ai`) can sometimes surface direct Cloudfront `preprint_pdf/*.pdf` mirrors even when TechRxiv/ResearchGate pages are blocked.
- **ACM DL/Cloudflare blocks:** `dl.acm.org` can return 403 “Just a moment…” bot challenges for HTML/PDF; r.jina.ai may not bypass. Prefer author/institution pages, DBLP/OpenAlex metadata, and talk slide decks; mark as blocked after repeated failures
- **Duplicate papers:** Same paper on arXiv and publisher site; dedupe by title
- **Project artifact repos:** Papers tied to large consortia/projects (e.g., EU SNS-JU / 6G-XR) may have public GitHub repos with experiment logs/datasets even if no code is released; useful for validating claims
- **Self-hosted implementation repos:** Some paper code lives on university/lab GitLab or `git.*` domains (not GitHub), so GitHub API searches will miss it; always extract and follow URLs from PDFs (including hyperlink annotations)
- **PDF parsing:** Some PDFs are image-only; note limitations
- **Broken URLs in PDFs:** PDF text extraction can split URLs across line wraps; extract hyperlink annotations (e.g., `pypdf` `/Annots` → `/A` → `/URI`) to recover exact links
- **Non-standard DNS payloads:** Large/new RR types (e.g., attestation blobs) may not be cached/handled by resolvers; compress and fragment into standard RRsets (e.g., AAAA) and prefetch in parallel (often via DoH with the AD flag) to keep verification low-latency.
- **Semantic label mismatch:** Robot object/action labels that do not map cleanly to English can degrade LLM explanations; consider a translation dictionary
- **Hallucination risk:** unless you enforce "only claim what you can cite/link", the agent can invent details when it can't read the paper properly
- **Quantum-only timestamping hits:** Queries like "timestamping"/"secure timestamping authority" can surface QKD/QKG-dependent schemes; treat quantum-network prerequisites as a major adoption constraint for auditable streaming, but extract reusable primitives (universal hashing bounds, explicit collusion assumptions)
- **C2PA durability model:** Treat watermarks/fingerprints as soft bindings used for recovery; the root of trust is the signed manifest + trust list. For streaming, check for piecewise validation support (e.g., fMP4/CMAF + Merkle rows) and explicit “metadata stripped” paths like HDMI capture/social re-encode.
- **Forensic ML attribution is probabilistic:** Detector/source-attribution models provide soft evidence (and can be brittle under re-encoding and adversarial adaptation); never treat them as cryptographic proof — use them to triage when provenance metadata/signatures are missing or stripped.
- **Camera-bus security metadata interoperability (MIPI CSI-2):** per-frame auth tags/metadata may not traverse receiver drivers in a parseable way (some hosts route non-image packets to opaque buffers). Prefer MIPI CSF/CSE (SEP/FSED) end-to-end or explicitly tunnel + decode tags in prototypes before committing to a design.
- **Kubernetes workload attestation allow-list drift:** IMA/whitelist-based pod integrity checks can flag routine helper binaries/containers (e.g., `/pause`, `busybox`) and operator debug actions (`cat`/`curl`) as violations unless whitelists explicitly include them; prefer generating allow lists from images/SBOMs and modeling “approved debug actions” to reduce false positives.
- **Soft-core crypto throughput limits:** real-time per-frame MAC/AEAD at HD-ish resolutions can exceed FPGA soft-core crypto budgets. Treat hardware crypto acceleration (SoC primitives or dedicated engines) as a core requirement and benchmark early (cycles/frame at target fps).
- **ISO BMFF atom reordering (MP4/MOV):** “Fast start” remuxing can move `moov` ahead of `mdat` (and change box order) without changing decoded content. If you use container structure as a provenance signal or commit to it, define canonicalization/allowed transforms so benign remuxes don’t look like tampering.
- **Hash-chain vs Merkle for streaming:** Simple per-frame hash chains (even with periodic anchors) require sequential hashing to verify mid-stream clips (O(k) work) and are brittle for random-access clip validation. Prefer per-segment Merkle trees or skip-list/Merkle-mountain-range commitments when verifiers need random access under loss/editing.
- **“Immediate” vs cryptographic verification:** TESLA-style delayed-disclosure schemes may describe whitelist-based early *use* as “immediate authentication” even though payload integrity is only verified when keys are disclosed. Model this explicitly as provisional/soft validity → final/strong verification and assess application-layer risk.
- **TESLA same-origin discrimination:** Even before identity/origin authentication completes (no cert / no signed key yet), keychain linkage can still cluster packets by sender (detect multiple keychains under the same identifier). Use this as an intermediate spoofing signal, not as authentication.
- **TESLA uncertainty-delay budgeting:** Delayed disclosure creates an uncertainty window that grows with loss/jitter. Model expected delay under packet loss (e.g., CABBA derives Δu ≈ T/2·(1+2p+4p²) assuming up to two missed disclosure periods) and expose provisional → final authenticity states in verifier UX.
- **TESLA interval timing vs MAC jitter:** On contention-based links (e.g., Wi‑Fi beacons with CSMA/CA), transmit delays can push packets outside the intended key interval and break “key must be secret at use-time” checks. Pick interval lengths and a permissible transmit window with safety margins for jitter/reordering, and model this in verifier UX.
- **GNSS-based geolocation attestation is fragile:** Indoor reception and cold-start delays can be tens of seconds, and spoofing/jamming is often out of scope. Treat location claims as an adoption constraint unless the GNSS→host→TPM binding is secured (e.g., external roof/antenna GNSS, device binding/whitelisting, measured daemon) and time-of-check/time-of-use is explicit.
- **Multi-cadence TESLA doesn’t bootstrap:** If you run fast+slow TESLA cadences (different Θ), satisfying loose-time sync and authenticating under the slow cadence does not imply the receiver is safe under the fast cadence. Slow receivers should withhold an “authenticated” flag until the slow cadence validates (or meet the tighter Θ), otherwise fast-cadence forgeries can slip through.
- **Keychain junction burst-loss:** Keychain/delayed-disclosure schemes can fail at junction/disclosure points if multiple special frames are sent back-to-back; a single loss burst can wipe them out and desync receivers. Prefer interleaving (dual keychains) or sparse cross-validation that spreads synchronization opportunities across time; note that increasing overlap `Q` also increases the commitment→disclosure window (~`Q·T`).
- **Low-quality/boilerplate papers:** Some arXiv papers contain internal inconsistencies (e.g., unrelated domain text, duplicated table labels), suggesting template/copy artifacts; treat performance numbers as unvalidated unless methodology + dataset are clearly specified
- **Blockchain security handwaving:** papers may propose “blockchain-based authentication/zero-trust” without quantifying latency/CPU overhead; treat as a limitation and keep blockchain off the real-time loop unless bounded overhead is shown
- **Append-only logs ≠ truth:** Logs/blockchain anchors prove an event was committed, not that it corresponds to ground truth (e.g., sensor-origin). Model the “truth gap” explicitly; pair logs with trusted capture/attestation or non-colluding cross-verification, and treat weakest-link hardware compromise as a first-class risk.
- **Attestation report concatenation attacks:** When combining multiple roots of trust (e.g., TEE + TPM + sensors), avoid returning independent reports that can be mixed-and-matched; require a single cryptographically bound/composite token to prevent report concatenation and ID-spoofing.
- **Offloaded state replay/reset attacks:** If you offload per-session measurement/commitment state outside the root of trust (to scale a stateless signer or attester), an attacker may replay old authenticated states (rollback/fork to hide measurements) or reset to an “empty” state and replay golden measurements. Mitigate with monotonic counters/versioning, append-only chaining, seeding the initial state with a provisioning-time random measurement, and restricting state initialization to authenticated CRTM/boot code that erases credentials before untrusted code runs.
- **VMPL0/no-SVSM spoofing risk (confidential VMs):** Don’t trust “requested from highest privilege” fields alone (e.g., VMPL=0). A provider can boot without the intended isolation layer (SVSM/VMPL enforcement) and still produce seemingly valid reports. Require launch-measurement verification that the expected SVSM/vTPM binaries actually ran at the intended privilege level.
- **Transparency-log anomaly skew:** Anomaly detection over transparency-log artifacts (CT/Sigstore/C2PA anchors) can be dominated by high-volume issuers or infrastructure clusters; stratify by issuer/tenant and/or use per-entity baselines so “anomalies” don’t just reflect producer mix.
- **Transparency logs need witnesses/monitors:** In CT/Sigstore-style designs, the security property depends on independent monitors/witnesses; in practice adopters may skip them or not verify witness state, creating a false sense of auditability. Ship default monitors/probers, make witness verification explicit, and treat missing monitoring as degraded assurance.
- **Opaque identities can break transparency:** If certificates/manifests intentionally hide identity (opaque commitments/anonymized subjects), a transparency log may prove “something was issued/anchored” but not whether it was issued for the correct identity. Plan additional ZK/redaction/audit channels (and verifier UX) for compromise detection under CA/key-registry mis-issuance.
- **OIDC key rotation + bearer replay risk:** If you use OIDC/JWT-based automated CAs (Sigstore-style) to mint signing certs/attestations, IdP JWKs rotate and offline verifiers need a verifiable key-history service (JWK ledger / transparency log + witnesses). Don’t embed raw bearer tokens in long-lived artifacts; use proof-of-knowledge-of-signature or DPoP-like binding to prevent replay.
- **Nonce randomness ≠ consensus security:** “random-looking” nonces (or ML-generated nonces) do not replace a clear consensus/threat model; evaluate what actually secures the system (PoW difficulty, BFT/PoA assumptions) and demand stronger randomness tests than uniqueness/entropy
- **Fast-path authorization vs blockchain commit:** for latency-sensitive systems, treat blockchain as a control-plane audit/consensus layer: issue tokens/session keys locally (hub-side validation) and submit validator endorsement asynchronously; design mitigation for rare post-hoc rejection
- **Policy log replay overhead:** if policies are logged as transactions, maintain a shadow policy state (indices + latest policy snapshot) at hubs/validators to avoid reconstructing policies from the chain on every access validation
- **P2P “virtual LAN” overlays:** for NAT-isolated device services (KVM-over-IP, ROS, etc.), combine hole punching/relay fallback with TAP/TUN-based virtual IP + port forwarding; measure session setup separately from steady-state RTT since setup can dominate tail latency
- **Formal verification ≠ runtime performance:** Tamarin/ProVerif verification results (and solver runtime) validate symbolic security properties; they do not measure protocol latency/throughput
- **Transparency-log verification shortcut:** Formal analyses often model append-only logs/Merkle trees as simple lists or trusted DBs. For stronger assurance, specify an explicit log interface (presence/extension/transitivity/uniqueness) and prove the concrete proof predicates (e.g., Merkle presence/extension) satisfy it, then use the interface as axioms in protocol proofs.
- **Architecture latency claims:** survey/architecture papers may quote latency targets without end-to-end benchmarks; treat numbers as hypotheses unless measured
- **E2E vs S2S latency:** some papers report “end-to-end” latency using RTP timestamps/NTP that excludes camera capture + display time; screen-to-screen latency can be much higher and is the relevant metric for teleoperation/KVM feasibility
- **GPU frame handoff overhead:** remote-rendering stacks that read back rendered frames from GPU→CPU and then re-upload for encoding can add significant latency; engine-native streaming paths can be materially faster
- **QUIC/MoQ playback maturity:** “QUIC latency” results may be transport-only (e.g., RTP-over-QUIC) requiring a native player; application-layer QUIC streaming (MoQ/RoQ) may be immature (e.g., missing audio/browser support) and should be treated as experimental
- **Padding/dummy traffic overhead:** some low-latency video rate control systems inject padding/dummy packets to emulate a backlogged flow and keep CC feedback responsive; account for bandwidth overhead/cost and consider repurposing padding for FEC/keyframes/control-plane instead of wasted traffic
- **Profile-switch freezes:** changing discrete streaming profiles (resolution/bitrate) can itself cause short freezes in WebRTC/remote-rendering pipelines; measure switch cost, rate-limit oscillations, and prefer simulcast/SVC or smooth encoder reconfiguration where possible
- **WebRTC topology split (A/V vs control):** in multi-user telepresence/KVM-style systems, keep A/V on a cloud-star path but route delay-sensitive operator control on-demand via a direct P2P WebRTC data channel (SCTP); relaying control through the same star can add tail latency/jitter that breaks control loops
- **Edge runtime mediation:** treat “operator has no direct access to edge/ROS runtime” as an explicit policy-enforcement point; mediate capability invocations via an API so you can add DID/blockchain authorization without putting blockchain on the real-time data path
- **Controller-dominated latency:** for biped/humanoid teleoperation, perceived step latency can be dominated by locomotion controller phases (e.g., transfer state 0.15–1s) and actuator limits; network optimizations alone may not achieve human-synchronous stepping
- **Operator haptic load:** haptic teleop papers can imply high sustained operator forces/torques; treat this as an adoption constraint (fatigue/safety). Prefer adjustable feedback gains and/or shared-autonomy/setpoint compensation to reduce sustained loads
- **Block-commit burstiness:** permissioned blockchains (e.g., Fabric) deliver updates at block commits; expect non-deterministic latency and bursty message arrival that can break non-network-aware controllers; prefer event-driven chaincode events over polling when bridging ROS/control data
- **KVM query mismatch:** arXiv rarely uses "KVM over IP"/"keyboard-video-mouse"; use adjacent queries like "remote rendering", "remote driving", "cloud gaming", "QUIC vs WebRTC", and "teleoperating vehicles over 5G"
- **IEEE Explore blocks:** Direct fetches from `ieeexplore.ieee.org` may return "Request Rejected"; prefer arXiv/preprints or metadata via Google Scholar/Semantic Scholar
- **IEEE Xplore metadata via text proxy:** If IEEE Xplore blocks direct access, `https://r.jina.ai/https://ieeexplore.ieee.org/document/<id>/` can expose abstract/authors/keywords; PDF may still require subscription/sign-in (treat as metadata-only)
- **Semantic Scholar throttling:** Semantic Scholar Graph API can return HTTP 429 quickly; add backoff/delay and reduce bursty queries
- **OpenAlex metadata fallback:** Use `https://api.openalex.org/works?search=<title>` to retrieve DOI/date/OA status when publisher pages or Scholar are blocked; follow with `https://api.openalex.org/works/<openalex_id>` for more detail
- **arXiv Papers with Code integration:** `arxiv.paperswithcode.com` can fail TLS handshakes in some environments; fall back to GitHub API searches and in-paper links

## Source Fallback Strategy

When searching for papers and implementations, use this fallback hierarchy:

**Implementation checks:** GitHub API → arXiv → Semantic Scholar → WebSearch
**Paper discovery:** arXiv API → Google Scholar → web

**Rate limit handling:**
- 429/503 → wait 60s, retry (max 2 retries)
- 403 → skip to next source, log in progress.txt
- 3 consecutive blocks → add to `blocked_sources`

**GitHub API (preferred for implementation checks):**
```
https://api.github.com/search/repositories?q="{paper_title}"+language:python
```

**GitHub API Authentication (recommended):**
Set `GITHUB_TOKEN` environment variable for higher rate limits:
- Unauthenticated: 10 requests/minute
- Authenticated: 30 requests/minute

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

The agent will automatically use `Authorization: token $GITHUB_TOKEN` header when available.

**If all sources blocked:** Extract URLs from paper's Related Work section

## Rate Limiting Configuration

| Source | Delay | Retry on 429 | Retry on 403 |
|--------|-------|--------------|--------------|
| arXiv API | 3s | Yes (60s backoff) | No |
| Google Scholar | 5s | Yes | No (use fallback) |
| GitHub API | 1s | Yes | No |
| WebSearch | 2s | Yes | No |

If a source is blocked 3 consecutive iterations → move to `blocked_sources` and use fallback.

## Cross-Reference Patterns

When analyzing papers, actively identify cross-reference clusters:
- **Same benchmark:** e.g., LIBERO used by InternVLA-A1, Dream-VLA, π₀.₅
- **Same dataset:** e.g., Open-X Embodiment
- **Same authors/institutions:** Track prolific labs and researchers
- **Competing approaches:** e.g., MoT vs Diffusion vs Flow Matching for VLA backbone

Add `cross_cluster` field to insights when patterns emerge:
```json
{"cross_cluster": "VLA_ARCHITECTURES", "papers": ["arxiv_X", "arxiv_Y"]}
```

## Operational Rules

- ONE paper per ANALYSIS iteration (deep analysis takes full context)
- Read FULL papers, not just abstracts
- Always extract insights, even from rejected papers
- Track all URLs visited; add to `visited_urls`
- Update statistics after each operation
- When feasible, write small tests or prototype code to validate paper assumptions; record results in `progress.txt` and clean up temp files (or note where the code lives)
- Handle rate limits:
  - Wait 60 seconds before retrying
  - After 3 consecutive failures for a source, add it to `blocked_sources` and move on
  - Log rate limit errors in `progress.txt`
- Process fixes (self-repair):
  - If you notice workflow/instruction issues, log the proposed fix in `progress.txt` (file(s) + change + why)
  - If it's a small doc-only fix, you may edit `AGENTS.md` and `CLAUDE.md` (keep them in sync) and note the change in `progress.txt`
- Follow the Git Workflow (Checkpoints) section for commits

## Patterns

- Each iteration spawns a fresh agent instance with clean context
- Memory persists via `researches/{name}/rrd.json` and `researches/{name}/progress.txt`
- Each research topic has its own isolated folder
- Cross-reference papers to find connections
- Update this file with domain-specific learnings
