"""Skill runner for executing Research-Ralph skills."""

import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Optional

from ralph.config import Agent, load_config
from ralph.core.agent_runner import AgentRunner


def _get_repo_root() -> Path:
    """Get the repository root directory."""
    # Try to find repo root by looking for known markers
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Max 5 levels up
        if (current / "pyproject.toml").exists() or (current / "skills").exists():
            return current
        current = current.parent
    # Fallback to package parent
    return Path(__file__).parent.parent


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

        # Get skill content
        skill_content = self.get_skill_content("rrd")
        if skill_content is None:
            return None, "RRD skill not found"

        # Create temporary directory for the research in current directory
        research_dir = Path.cwd()
        today = date.today().isoformat()
        temp_name = f"rrd-temp-{today}"
        temp_path = research_dir / temp_name

        # Create temp directory
        temp_path.mkdir(parents=True, exist_ok=True)

        # Build full prompt
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

        # Run agent
        runner = AgentRunner(agent, self.script_dir)
        if not runner.is_available():
            temp_path.rmdir()
            return None, f"Agent '{agent.value}' not available. {runner.get_install_instructions()}"

        # Run the agent
        try:
            if agent == Agent.AMP:
                result = subprocess.run(
                    ["amp", "--dangerously-allow-all"],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
            elif agent == Agent.CODEX:
                result = subprocess.run(
                    ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "-"],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
            else:  # CLAUDE
                result = subprocess.run(
                    [
                        "claude",
                        "-p",
                        prompt,
                        "--dangerously-skip-permissions",
                        "--allowedTools",
                        "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return None, "Agent timed out"
        except Exception as e:
            return None, str(e)

        # Check if rrd.json was created
        rrd_path = temp_path / "rrd.json"
        if not rrd_path.exists():
            # Clean up
            try:
                temp_path.rmdir()
            except Exception:
                pass
            return None, f"RRD file was not created. Agent output:\n{output}"

        # Rename to final name based on project name
        import json

        try:
            with open(rrd_path) as f:
                rrd_data = json.load(f)

            project_name = rrd_data.get("project", "").replace("Research: ", "")
            if project_name:
                # Convert to slug
                slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower())
                slug = re.sub(r"^-|-$", "", slug)[:50]
            else:
                # Use topic
                slug = re.sub(r"[^a-z0-9]+", "-", topic.lower())
                slug = re.sub(r"^-|-$", "", slug)[:40]

            final_name = f"{slug}-{today}"
            final_path = research_dir / final_name

            # Handle collision
            if final_path.exists():
                i = 1
                while (research_dir / f"{final_name}-{i}").exists():
                    i += 1
                final_path = research_dir / f"{final_name}-{i}"

            # Rename
            temp_path.rename(final_path)

            # Update branchName in rrd.json
            rrd_data["branchName"] = f"research/{slug}"
            with open(final_path / "rrd.json", "w") as f:
                json.dump(rrd_data, f, indent=2)

            return final_path, output

        except Exception as e:
            return temp_path, f"Created research but failed to rename: {e}\n{output}"
