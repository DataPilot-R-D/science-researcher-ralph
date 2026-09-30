"""Exercise the loop with real state files and harmless agent subprocesses."""

import json
import sys
from unittest.mock import patch

import pytest

from ralph.config import Agent, Config
from ralph.core.agent_runner import AgentRunner
from ralph.core.research_loop import ResearchLoop
from ralph.core.rrd_manager import RRDManager


@pytest.mark.parametrize("live_output", [False, True])
@pytest.mark.parametrize("local_prompt", [False, True])
def test_nested_project_uses_the_validated_prompt(tmp_path, live_output, local_prompt):
    project = tmp_path / "researches" / "topic"
    project.mkdir(parents=True)
    (project / "rrd.json").write_text(json.dumps({
        "project": "Prompt regression",
        "requirements": {"focus_area": "Testing", "target_papers": 1},
    }))
    (tmp_path / "prompt.md").write_text("Repository prompt: {{RESEARCH_DIR}}")
    if local_prompt:
        (project.parent / "prompt.md").write_text("Local prompt: {{RESEARCH_DIR}}")

    def echo_prompt(prompt):
        return [sys.executable, "-c", "import sys; print(sys.argv[1])", prompt], None

    iterations = []
    with (
        patch("ralph.core.research_loop._get_repo_root", return_value=tmp_path),
        patch("ralph.core.research_loop.load_config", return_value=Config(live_output=live_output)),
        patch("ralph.core.research_loop.time.sleep"),
        patch.object(AgentRunner, "is_available", return_value=True),
        patch.object(AgentRunner, "_get_command_and_input", side_effect=echo_prompt),
    ):
        loop = ResearchLoop(
            project, agent=Agent.CLAUDE, max_iterations=1,
            on_output=lambda line: None, on_iteration_end=iterations.append,
        )
        assert loop.validate() == []
        loop.run()

    expected = "Local" if local_prompt else "Repository"
    assert iterations[0].success
    assert iterations[0].agent_result.output.strip() == f"{expected} prompt: {project}"


@pytest.mark.parametrize("live_output", [False, True])
def test_all_phases_run_before_completion(tmp_path, completed_project, live_output):
    project = tmp_path / "new-researches" / "topic"
    project.mkdir(parents=True)
    data = json.loads((completed_project / "rrd.json").read_text())
    data.update(phase="DISCOVERY", papers_pool=[], insights=[], statistics={})
    (project / "rrd.json").write_text(json.dumps(data))
    script = tmp_path / "fixture_agent.py"
    script.write_text('''
import json
import sys
from pathlib import Path

project, fixture = map(Path, sys.argv[1:])
path = project / "rrd.json"
data = json.loads(path.read_text())
if data["phase"] == "DISCOVERY":
    data["papers_pool"] = json.loads((fixture / "rrd.json").read_text())["papers_pool"]
    data["papers_pool"][0]["status"] = "pending"
    data["phase"] = "ANALYSIS"
elif data["phase"] == "ANALYSIS":
    data = json.loads((fixture / "rrd.json").read_text())
    data["phase"] = "IDEATION"
    (project / "research-report.md").write_text((fixture / "research-report.md").read_text())
elif data["phase"] == "IDEATION":
    (project / "product-ideas.json").write_text((fixture / "product-ideas.json").read_text())
    data["phase"] = "COMPLETE"
path.write_text(json.dumps(data))
# Even a tag echoed before IDEATION must not terminate the loop early.
print("<promise>COMPLETE</promise>")
''')
    phases = []
    with (
        patch("ralph.core.research_loop.load_config", return_value=Config(live_output=live_output)),
        patch("ralph.core.research_loop.time.sleep"),
        patch.object(AgentRunner, "is_available", return_value=True),
        patch.object(AgentRunner, "_get_command_and_input", return_value=(
            [sys.executable, str(script), str(project), str(completed_project)], None,
        )),
    ):
        result = ResearchLoop(
            project, agent=Agent.CLAUDE, max_iterations=3,
            on_output=lambda line: None,
            on_iteration_start=lambda iteration, phase: phases.append(phase),
        ).run()

    assert result.completed
    assert result.iterations_run == 3
    assert phases == ["DISCOVERY", "ANALYSIS", "IDEATION"]
    assert RRDManager(project).completion_errors() == []
