"""Create command - create a new research project."""

from pathlib import Path
from typing import Optional

from ralph.config import Agent, load_config
from ralph.core.skill_runner import SkillRunner
from ralph.ui.console import console, print_error, print_success, print_info, SimpsonsColors
from ralph.ui.progress import create_spinner


def create_project(
    topic: str,
    papers: Optional[int] = None,
    agent: Optional[str] = None,
) -> Optional[Path]:
    """
    Create a new research project.

    Uses the RRD skill to generate the research requirements document.

    Args:
        topic: Research topic description
        papers: Target papers count (default: from config)
        agent: Agent to use (default: from config)

    Returns:
        Path to created project, or None on failure
    """
    config = load_config()

    # Resolve parameters
    target_papers = papers or config.default_papers

    if agent:
        try:
            agent_enum = Agent(agent)
        except ValueError:
            print_error(f"Invalid agent: {agent}. Must be claude, amp, or codex")
            return None
    else:
        agent_enum = config.default_agent

    # Print header
    console.print()
    console.print(f"[bold {SimpsonsColors.BLUE}]Research-Ralph[/] - Create New Research")
    console.print()
    console.print(f"  Topic: [{SimpsonsColors.BLUE}]{topic}[/]")
    console.print(f"  Target papers: {target_papers}")
    console.print(f"  Agent: {agent_enum.value}")
    console.print()

    # Run skill
    runner = SkillRunner()

    # Check if RRD skill exists
    skills = runner.list_skills()
    rrd_skill = next((s for s in skills if s["name"] == "rrd"), None)

    if rrd_skill is None:
        print_error("RRD skill not found in skills/ directory")
        return None

    # Create project with spinner
    console.print("[dim]Creating research project...[/dim]")
    console.print()

    project_path, output = runner.run_rrd_skill(
        topic=topic,
        agent=agent_enum,
        target_papers=target_papers,
    )

    if project_path is None:
        print_error("Failed to create research project")
        console.print()
        console.print("[dim]Agent output:[/dim]")
        console.print(output[:2000] if len(output) > 2000 else output)
        return None

    # Success
    print_success(f"Research project created: {project_path}")
    console.print()
    console.print("Next step:")
    console.print(f"  [bold]research-ralph --run {project_path.name}[/bold]")
    console.print()

    return project_path


def create_project_interactive() -> Optional[Path]:
    """
    Create a new research project interactively.

    Prompts for topic, papers count, and agent.

    Returns:
        Path to created project, or None on failure/cancel
    """
    import questionary
    from questionary import Style

    # Custom style using Simpsons colors
    custom_style = Style(
        [
            ("question", "bold"),
            ("answer", f"fg:{SimpsonsColors.BLUE} bold"),
        ]
    )

    console.print()
    console.print(f"[bold {SimpsonsColors.BLUE}]Research-Ralph[/] - Create New Research")
    console.print()

    # Get topic
    topic = questionary.text(
        "What is your research topic?",
        validate=lambda x: len(x.strip()) > 10 or "Please provide a more detailed topic description",
        style=custom_style,
    ).ask()

    if topic is None:
        print_info("Cancelled")
        return None

    # Get target papers
    config = load_config()

    papers_str = questionary.text(
        "Target number of papers?",
        default=str(config.default_papers),
        validate=lambda x: x.isdigit() and int(x) > 0 or "Please enter a positive number",
        style=custom_style,
    ).ask()

    if papers_str is None:
        print_info("Cancelled")
        return None

    papers = int(papers_str)

    # Get agent
    agent_choices = [
        questionary.Choice(f"Claude (default)" if config.default_agent == Agent.CLAUDE else "Claude", value="claude"),
        questionary.Choice(f"Amp (default)" if config.default_agent == Agent.AMP else "Amp", value="amp"),
        questionary.Choice(f"Codex (default)" if config.default_agent == Agent.CODEX else "Codex", value="codex"),
    ]

    agent = questionary.select(
        "Which agent to use?",
        choices=agent_choices,
        default="claude" if config.default_agent == Agent.CLAUDE else config.default_agent.value,
        style=custom_style,
    ).ask()

    if agent is None:
        print_info("Cancelled")
        return None

    # Create project
    return create_project(topic, papers, agent)
