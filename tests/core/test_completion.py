"""Completion requires persisted work and usable artifacts, not an output tag."""

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from ralph.cli import app
from ralph.commands.list_cmd import _get_project_info
from ralph.commands.run import run_research
from ralph.commands.status import show_status
from ralph.config import Agent, Config
from ralph.core.agent_runner import AgentResult, AgentRunner
from ralph.core.research_loop import ResearchLoop
from ralph.core.rrd_manager import RRDManager


def run_one_iteration(project, output="<promise>COMPLETE</promise>"):
    with (
        patch("ralph.core.research_loop.load_config", return_value=Config(live_output=False)),
        patch("ralph.core.research_loop.time.sleep"),
        patch.object(AgentRunner, "is_available", return_value=True),
        patch.object(AgentRunner, "run", return_value=AgentResult(output, 0, True)),
    ):
        return ResearchLoop(project, agent=Agent.CLAUDE, max_iterations=1).run()


def update_rrd(project, **changes):
    path = project / "rrd.json"
    data = json.loads(path.read_text())
    data.update(changes)
    path.write_text(json.dumps(data))


def test_completion_tag_does_not_skip_ideation(completed_project):
    update_rrd(completed_project, phase="IDEATION")
    assert not run_one_iteration(completed_project).completed


@pytest.mark.parametrize("defect", [
    "missing_report", "empty_report", "missing_ideas", "malformed_ideas",
    "empty_ideas", "invalid_idea", "unknown_paper", "unknown_insight",
    "duplicate_id", "wrong_project", "wrong_score", "stale_statistics", "empty_pool",
])
def test_invalid_completion_is_rejected(completed_project, defect):
    report = completed_project / "research-report.md"
    ideas_path = completed_project / "product-ideas.json"
    ideas = json.loads(ideas_path.read_text())
    if defect == "missing_report":
        report.unlink()
    elif defect == "empty_report":
        report.write_text(" \n")
    elif defect == "missing_ideas":
        ideas_path.unlink()
    elif defect == "malformed_ideas":
        ideas_path.write_text("{broken")
    elif defect == "stale_statistics":
        update_rrd(completed_project, statistics={"total_analyzed": 20})
    elif defect == "empty_pool":
        update_rrd(completed_project, papers_pool=[])
    else:
        if defect == "empty_ideas":
            ideas["ideas"] = []
        elif defect == "invalid_idea":
            ideas["ideas"][0] = {"id": "placeholder"}
        elif defect == "unknown_paper":
            ideas["ideas"][0]["evidence"]["paper_ids"] = ["missing-paper"]
        elif defect == "unknown_insight":
            ideas["ideas"][0]["evidence"]["insight_ids"] = ["missing-insight"]
        elif defect == "duplicate_id":
            ideas["ideas"][1]["id"] = ideas["ideas"][0]["id"]
        elif defect == "wrong_project":
            ideas["project"] = "Another research project"
        elif defect == "wrong_score":
            ideas["ideas"][0]["scores"]["combined_0_50"] = 49
        ideas_path.write_text(json.dumps(ideas))

    result = run_one_iteration(completed_project)
    assert not result.completed
    assert "Completion validation failed" in result.error_message


@pytest.mark.parametrize("output", ["<promise>COMPLETE</promise>", "Finished"])
def test_valid_completion_accepts_persisted_state(completed_project, output):
    assert run_one_iteration(completed_project, output).completed


def test_disabled_ideation_requires_only_report(completed_project):
    update_rrd(completed_project, handoff={"product_ideation": {"enabled": False}})
    (completed_project / "product-ideas.json").unlink()
    assert run_one_iteration(completed_project).completed


def test_custom_ideas_filename_is_validated(completed_project):
    update_rrd(completed_project, handoff={"product_ideation": {"output_filename": "opportunities.json"}})
    (completed_project / "product-ideas.json").rename(completed_project / "opportunities.json")
    assert run_one_iteration(completed_project).completed
    (completed_project / "opportunities.json").unlink()
    assert not run_one_iteration(completed_project).completed


def test_run_command_checks_artifacts_before_already_complete(completed_project):
    (completed_project / "product-ideas.json").unlink()
    with patch("ralph.commands.run.ResearchLoop") as loop:
        assert not run_research(str(completed_project), agent="claude")
    loop.assert_not_called()


def test_status_does_not_infer_completion_from_an_ideas_file(completed_project):
    update_rrd(completed_project, phase="IDEATION")
    assert RRDManager(completed_project).get_summary()["phase"] == "IDEATION"
    assert _get_project_info(completed_project)["phase"] == "IDEATION"


def test_status_reports_failed_completion_validation(completed_project, capsys):
    (completed_project / "product-ideas.json").unlink()
    assert show_status(str(completed_project))
    captured = capsys.readouterr()
    assert "Completion validation failed" in captured.out + captured.err
    assert "Research complete!" not in captured.out


@pytest.mark.parametrize("status", ["pending", "analyzing"])
def test_pending_papers_prevent_completion(completed_project, status):
    path = completed_project / "rrd.json"
    data = json.loads(path.read_text())
    data["papers_pool"][0]["status"] = status
    path.write_text(json.dumps(data))
    assert not run_one_iteration(completed_project).completed


@pytest.mark.parametrize("count", [2, 13])
def test_configured_idea_count_is_enforced(completed_project, count):
    path = completed_project / "product-ideas.json"
    data = json.loads(path.read_text())
    data["ideas"] = [{**data["ideas"][0], "id": f"idea_{i}"} for i in range(count)]
    path.write_text(json.dumps(data))
    assert not run_one_iteration(completed_project).completed


@pytest.mark.parametrize("command", ["--run", "run"])
@pytest.mark.parametrize("valid", [True, False])
def test_cli_exit_status_matches_validated_completion(completed_project, command, valid):
    if not valid:
        (completed_project / "product-ideas.json").unlink()
    result = CliRunner().invoke(app, [command, str(completed_project), "--agent", "claude"])
    assert result.exit_code == (0 if valid else 1)
    assert "Research failed: Exit" not in result.output
