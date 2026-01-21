# Docs Update Plan: Python CLI Migration

## Current Doc Drift (from scan)
- README and most docs still refer to `ralph.sh` / `skill.sh`, but the current entrypoint is the Python CLI (`research-ralph` in `pyproject.toml`).
- Version badge in `README.md` is `3.0.0` while `pyproject.toml` is `4.0.0`.
- CLI reference, configuration reference, architecture diagram, and tutorials explain script-based usage and script-specific internals.
- AGENTS/CLAUDE instructions are script-first; they must stay in sync when updated.

## Update Plan
1. **Define the canonical CLI usage and install path**
   - Document the primary entrypoint: `research-ralph` (interactive by default).
   - Add install/run guidance aligned with `pyproject.toml` (e.g., `poetry install` + `poetry run research-ralph`, or editable install).
   - Update version references to `4.0.0`.

2. **Refresh top-level docs**
   - `README.md`: replace `./ralph.sh` / `./skill.sh` examples with `research-ralph` (flags + subcommands).
   - `docs/README.md`: update CLI reference label to the new CLI and adjust the “Reference” table text.

3. **Rewrite CLI reference**
   - `docs/reference/cli.md`: replace script sections with the `research-ralph` CLI surface:
     - flags: `--new`, `--run`, `--status`, `--list`, `--reset`, `--config`, `--papers`, `--iterations`, `--agent`, `--force`, `--version`
     - subcommands: `create`, `run`, `status`, `list`, `reset`, `config`, `init`
   - Add a small “legacy scripts” note if `ralph.sh`/`skill.sh` remain in repo (optional).

4. **Update configuration reference**
   - `docs/reference/configuration.md`: document `~/.research-ralph/config.yaml` and config keys (`research_dir`, `default_agent`, `default_papers`, `live_output`, `max_consecutive_failures`).
   - Replace “Script Options” and `ralph.sh`-specific references with CLI equivalents and `research-ralph config`.
   - Update agent invocation notes to reference the Python runner, not `ralph.sh` line numbers.

5. **Align tutorials and how-to guides**
   - `docs/tutorials/getting-started.md`, `docs/tutorials/customizing-research.md`: update example commands to `research-ralph`.
   - `docs/how-to/switch-agents.md`, `docs/how-to/multiple-projects.md`, `docs/how-to/resume-research.md`: swap script usage for CLI flags/subcommands.
   - Ensure examples use consistent folder naming and the new `--new` / `create` flow.

6. **Refresh architecture/explanations**
   - `docs/explanations/architecture.md`: rename loop from `ralph.sh` to `research-ralph` and update file tree.
   - Replace any script-specific operational details with Python CLI equivalents.

7. **Keep AGENTS/CLAUDE in sync**
   - Update command blocks and “Key Files” references to the Python CLI.
   - Apply identical changes in both `AGENTS.md` and `CLAUDE.md` per sync policy.

8. **Documentation plan hygiene**
   - Update `docs/DOCUMENTATION_PLAN.md` to reflect CLI-first flow and remove script-centric milestones.
   - Run a final `rg "ralph\\.sh|skill\\.sh"` sweep to confirm no stale references remain.
