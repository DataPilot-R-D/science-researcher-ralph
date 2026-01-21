"""Run command - execute the research loop."""

from pathlib import Path
from typing import Optional

from ralph.config import Agent, resolve_research_path, load_config
from ralph.core.rrd_manager import RRDManager
from ralph.core.research_loop import ResearchLoop, IterationResult, LoopResult
from ralph.models.rrd import Phase
from ralph.ui.console import console, print_error, print_success, print_warning, get_phase_style, SimpsonsColors
from ralph.ui.live import LiveResearchDisplay, SimpleProgressDisplay
from ralph.ui.tables import create_completion_summary


def run_research(
    project: str,
    papers: Optional[int] = None,
    iterations: Optional[int] = None,
    agent: Optional[str] = None,
    force: bool = False,
) -> bool:
    """
    Run the research loop on a project.

    Args:
        project: Project name or path
        papers: Target papers count (optional, overrides RRD)
        iterations: Max iterations (optional, defaults to papers + 6)
        agent: Agent to use (optional, defaults to config)
        force: Force override of target_papers even if in progress

    Returns:
        True if research completed, False otherwise
    """
    # Resolve project path
    project_path = resolve_research_path(project)

    if project_path is None:
        print_error(f"Research project not found: {project}")
        console.print()
        console.print("Use [bold]research-ralph --list[/bold] to see available projects")
        return False

    # Load RRD
    manager = RRDManager(project_path)

    errors = manager.validate()
    if errors:
        print_error("Invalid RRD file:")
        for error in errors:
            console.print(f"  - {error}")
        return False

    # Update target papers if specified
    if papers is not None:
        if not manager.update_target_papers(papers, force=force):
            rrd = manager.load()
            print_error("Cannot change target_papers - research already in progress")
            console.print(f"  Phase: {rrd.phase}, Analyzed: {rrd.statistics.total_analyzed}")
            console.print(f"  Current target: {rrd.requirements.target_papers}")
            console.print()
            console.print("Options:")
            console.print("  1. Run without --papers to continue with existing target")
            console.print("  2. Use --force --papers N to override (creates backup)")
            console.print("  3. Use --reset to start fresh")
            return False

    # Resolve agent
    config = load_config()
    if agent:
        try:
            agent_enum = Agent(agent)
        except ValueError:
            print_error(f"Invalid agent: {agent}. Must be claude, amp, or codex")
            return False
    else:
        agent_enum = config.default_agent

    # Calculate max iterations
    rrd = manager.load()
    target_papers = rrd.requirements.target_papers

    if iterations is None:
        max_iterations = target_papers + 6
    else:
        max_iterations = iterations

    # Print header
    console.print()
    console.print(f"[bold {SimpsonsColors.BLUE}]Research-Ralph[/] - Starting Research Loop")
    console.print()
    console.print(f"  Project: [{SimpsonsColors.BLUE}]{rrd.project}[/]")
    console.print(f"  Path: {project_path}")
    console.print(f"  Agent: {agent_enum.value}")
    console.print(f"  Phase: [{get_phase_style(rrd.phase)}]{rrd.phase}[/{get_phase_style(rrd.phase)}]")
    console.print(f"  Papers: {rrd.statistics.total_analyzed}/{target_papers} analyzed")
    console.print(f"  Max iterations: {max_iterations}")
    console.print()

    # Check if already complete
    if rrd.phase == Phase.COMPLETE:
        print_success("Research already complete!")
        console.print(f"  View report: cat {project_path}/research-report.md")
        return True

    # Create display
    if config.live_output:
        display = LiveResearchDisplay(max_iterations, target_papers)
    else:
        display = SimpleProgressDisplay()

    # Callbacks for the loop
    def on_iteration_start(iteration: int, phase: Phase) -> None:
        if config.live_output:
            display.update_iteration(iteration, phase.value if isinstance(phase, Phase) else phase)
        else:
            display.start_iteration(iteration, max_iterations, phase.value if isinstance(phase, Phase) else phase)

    def on_iteration_end(result: IterationResult) -> None:
        if config.live_output:
            # Reload to get updated count
            try:
                updated_rrd = manager.load()
                display.update_papers(updated_rrd.statistics.total_analyzed)
            except Exception:
                pass
        else:
            if result.papers_delta > 0:
                display.end_iteration(result.papers_delta)

    def on_output(line: str) -> None:
        if config.live_output:
            display.add_output(line)

    # Create and run loop
    loop = ResearchLoop(
        project_path=project_path,
        agent=agent_enum,
        max_iterations=max_iterations,
        on_iteration_start=on_iteration_start,
        on_iteration_end=on_iteration_end,
        on_output=on_output,
    )

    # Run with live display if enabled
    if config.live_output:
        with display.start() as live:
            # Patch the iteration callbacks to update live display
            original_on_end = on_iteration_end

            def live_on_end(result: IterationResult) -> None:
                original_on_end(result)
                live.update(display.get_layout())

            def live_on_output(line: str) -> None:
                on_output(line)
                live.update(display.get_layout())

            loop.on_iteration_end = live_on_end
            loop.on_output = live_on_output

            loop_result = loop.run()
    else:
        loop_result = loop.run()

    console.print()

    # Show result
    if loop_result.completed:
        # Show completion summary
        summary = manager.get_summary()
        panel = create_completion_summary(summary)
        console.print(panel)
        console.print()
        console.print(f"Results in: [bold]{project_path}/[/bold]")
        console.print("  - progress.txt for detailed findings")
        console.print("  - rrd.json for full data")
        if (project_path / "research-report.md").exists():
            console.print("  - research-report.md for summary report")
        if (project_path / "product-ideas.json").exists():
            console.print("  - product-ideas.json for product opportunities")
        console.print()
        return True
    else:
        print_warning(f"Research did not complete: {loop_result.error_message}")
        console.print(f"  Iterations run: {loop_result.iterations_run}")
        console.print(f"  Final phase: {loop_result.final_phase}")
        console.print(f"  Papers analyzed: {loop_result.total_analyzed}")
        console.print()
        console.print(f"Continue with: [bold]research-ralph --run {project_path.name}[/bold]")
        console.print()
        return False
