"""Skill runner for executing Research-Ralph skills."""

import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Optional

from ralph.config import Agent, load_config
from ralph.core.agent_runner import AgentRunner, _get_repo_root


def _to_slug(text: str, max_length: int = 50) -> str:
    """Convert text to a URL-friendly slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return re.sub(r"^-|-$", "", slug)[:max_length]


class SkillRunner:
    """Runs Research-Ralph skills (like RRD creation)."""

    def __init__(self, script_dir: Optional[Path] = None):
        """
        Initialize skill runner.

        Args:
            script_dir: Directory containing skills/ folder (repo root)
        """
        self.script_dir = script_dir or _get_repo_root()
        self.skills_dir = self.script_dir / "skills"

    def list_skills(self) -> list[dict]:
        """
        List all available skills.

        Returns:
            List of skill info dicts with name and description
        """
        skills: list[dict] = []

        if not self.skills_dir.exists():
            return skills

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    # Extract description from frontmatter
                    with open(skill_file) as f:
                        content = f.read()

                    desc = ""
                    # Look for description in YAML frontmatter
                    match = re.search(r'description:\s*"?([^"\n]+)"?', content)
                    if match:
                        desc = match.group(1).strip()[:60]

                    skills.append(
                        {
                            "name": skill_dir.name,
                            "description": desc,
                            "path": skill_file,
                        }
                    )

        return sorted(skills, key=lambda x: x["name"])

    def get_skill_content(self, skill_name: str) -> Optional[str]:
        """
        Get the content of a skill (without YAML frontmatter).

        Args:
            skill_name: Name of the skill

        Returns:
            Skill content or None if not found
        """
        skill_file = self.skills_dir / skill_name / "SKILL.md"
        if not skill_file.exists():
            return None

        with open(skill_file) as f:
            content = f.read()

        # Strip YAML frontmatter
        lines = content.split("\n")
        if lines and lines[0].strip() == "---":
            # Find closing ---
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    return "\n".join(lines[i + 1 :]).strip()

        return content

    def _run_agent_with_prompt(self, agent: Agent, prompt: str) -> tuple[str, Optional[str]]:
        """Run agent with prompt, returning (output, error_message)."""
        try:
            cmd, stdin_input = self._get_agent_command(agent, prompt)
            result = subprocess.run(
                cmd, input=stdin_input, capture_output=True, text=True, timeout=300
            )
            return result.stdout + result.stderr, None
        except subprocess.TimeoutExpired:
            return "", "Agent timed out"
        except FileNotFoundError as e:
            return "", f"Agent not found: {e}"
        except PermissionError as e:
            return "", f"Permission denied: {e}"
        except Exception as e:
            return "", f"{type(e).__name__}: {e}"

    def _get_agent_command(self, agent: Agent, prompt: str) -> tuple[list[str], Optional[str]]:
        """Get command and optional stdin for agent."""
        if agent == Agent.AMP:
            return ["amp", "--dangerously-allow-all"], prompt
        elif agent == Agent.CODEX:
            return ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "-"], prompt
        else:  # CLAUDE
            return [
                "claude", "-p", prompt,
                "--dangerously-skip-permissions",
                "--allowedTools", "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch",
            ], None

    def _finalize_project(
        self, temp_path: Path, topic: str, output: str
    ) -> tuple[Optional[Path], str]:
        """Rename temp directory to final name and update rrd.json."""
        rrd_path = temp_path / "rrd.json"
        if not rrd_path.exists():
            try:
                temp_path.rmdir()
            except Exception:
                pass
            return None, f"RRD file was not created. Agent output:\n{output}"

        try:
            with open(rrd_path) as f:
                rrd_data = json.load(f)

            project_name = rrd_data.get("project", "").replace("Research: ", "")
            slug = _to_slug(project_name, 50) if project_name else _to_slug(topic, 40)

            today = date.today().isoformat()
            final_name = f"{slug}-{today}"
            research_dir = temp_path.parent
            final_path = research_dir / final_name

            # Handle name collision
            if final_path.exists():
                counter = 1
                while (research_dir / f"{final_name}-{counter}").exists():
                    counter += 1
                final_path = research_dir / f"{final_name}-{counter}"

            temp_path.rename(final_path)

            rrd_data["branchName"] = f"research/{slug}"
            with open(final_path / "rrd.json", "w") as f:
                json.dump(rrd_data, f, indent=2)

            return final_path, output
        except Exception as e:
            return temp_path, f"Created research but failed to rename ({type(e).__name__}): {e}\n{output}"

    def run_rrd_skill(
        self,
        topic: str,
        agent: Optional[Agent] = None,
        target_papers: int = 20,
    ) -> tuple[Optional[Path], str]:
        """
        Run the RRD creation skill to create a new research project.

        Args:
            topic: Research topic description
            agent: Agent to use (default: from config)
            target_papers: Target number of papers

        Returns:
            Tuple of (project_path, output) - path is None on failure
        """
        config = load_config()
        agent = agent or config.default_agent

        skill_content = self.get_skill_content("rrd")
        if skill_content is None:
            return None, "RRD skill not found"

        today = date.today().isoformat()
        temp_path = Path.cwd() / f"rrd-temp-{today}"
        temp_path.mkdir(parents=True, exist_ok=True)

        prompt = f"""{skill_content}

---

## Task

{topic}

---

## Output Location

Save all files to the research folder: {temp_path}/
- Save rrd.json to: {temp_path}/rrd.json
- progress.txt will be created automatically by ralph.sh

**Note:** The `project` field in rrd.json will be used for the directory name, so make it concise and descriptive (3-6 words).

**Target Papers:** {target_papers}
"""

        runner = AgentRunner(agent, self.script_dir)
        if not runner.is_available():
            temp_path.rmdir()
            return None, f"Agent '{agent.value}' not available. {runner.get_install_instructions()}"

        output, error = self._run_agent_with_prompt(agent, prompt)
        if error:
            return None, error

        return self._finalize_project(temp_path, topic, output)
