"""Main research loop logic."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ralph.config import Agent, load_config
from ralph.core.agent_runner import AgentRunner, AgentResult, ErrorType, classify_error, get_retry_delay, _get_repo_root
from ralph.core.rrd_manager import RRDManager
from ralph.models.rrd import Phase


@dataclass
class IterationResult:
    """Result of a single research iteration."""

    iteration: int
    success: bool
    agent_result: AgentResult
    phase: Phase
    papers_delta: int = 0
    should_continue: bool = True
    is_complete: bool = False
    error_message: Optional[str] = None


@dataclass
class LoopResult:
    """Result of the complete research loop."""

    completed: bool
    iterations_run: int
    final_phase: Phase
    total_analyzed: int
    total_presented: int
    total_insights: int
    error_message: Optional[str] = None


class ResearchLoop:
    """
    Main research loop that runs the AI agent repeatedly.

    The loop continues until:
    1. Agent outputs <promise>COMPLETE</promise>
    2. Max iterations reached
    3. Too many consecutive failures
    """

    def __init__(
        self,
        project_path: Path,
        agent: Optional[Agent] = None,
        max_iterations: Optional[int] = None,
        on_iteration_start: Optional[Callable[[int, Phase], None]] = None,
        on_iteration_end: Optional[Callable[[IterationResult], None]] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the research loop.

        Args:
            project_path: Path to the research project
            agent: Agent to use (default: from config)
            max_iterations: Maximum iterations (default: target_papers + 6)
            on_iteration_start: Callback before each iteration
            on_iteration_end: Callback after each iteration
            on_output: Callback for streaming output
        """
        self.project_path = project_path
        self.rrd_manager = RRDManager(project_path)

        config = load_config()
        self.agent = agent or config.default_agent
        self.max_consecutive_failures = config.max_consecutive_failures
        self.live_output = config.live_output

        # Calculate max iterations if not provided
        if max_iterations is None:
            rrd = self.rrd_manager.load()
            max_iterations = rrd.requirements.target_papers + 6

        self.max_iterations = max_iterations

        # Callbacks
        self.on_iteration_start = on_iteration_start
        self.on_iteration_end = on_iteration_end
        self.on_output = on_output

        # State
        self.consecutive_failures = 0
        self.current_iteration = 0

    def validate(self) -> list[str]:
        """
        Validate that the loop can run.

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Check RRD exists and is valid
        rrd_errors = self.rrd_manager.validate()
        errors.extend(rrd_errors)

        # Check agent is available
        runner = AgentRunner(self.agent, self.project_path.parent)
        if not runner.is_available():
            errors.append(f"Agent '{self.agent.value}' not found. {runner.get_install_instructions()}")

        # Check prompt.md exists
        prompt_path = self.project_path.parent / "prompt.md"
        if not prompt_path.exists():
            # Try repo root
            prompt_path = _get_repo_root() / "prompt.md"
        if not prompt_path.exists():
            errors.append("prompt.md not found")

        return errors

    def run(self) -> LoopResult:
        """
        Run the research loop.

        Returns:
            LoopResult with final state
        """
        # Validate first
        errors = self.validate()
        if errors:
            return LoopResult(
                completed=False,
                iterations_run=0,
                final_phase=Phase.DISCOVERY,
                total_analyzed=0,
                total_presented=0,
                total_insights=0,
                error_message="; ".join(errors),
            )

        # Ensure progress file exists
        self.rrd_manager.ensure_progress_file()

        # Create agent runner
        runner = AgentRunner(self.agent, self.project_path.parent)

        # Main loop
        for i in range(1, self.max_iterations + 1):
            self.current_iteration = i
            result = self._run_iteration(runner, i)

            if not result.should_continue:
                rrd = self.rrd_manager.load()
                return LoopResult(
                    completed=result.is_complete,
                    iterations_run=i,
                    final_phase=rrd.phase,
                    total_analyzed=rrd.statistics.total_analyzed,
                    total_presented=rrd.statistics.total_presented,
                    total_insights=rrd.statistics.total_insights_extracted,
                    error_message=result.error_message,
                )

        # Max iterations reached
        rrd = self.rrd_manager.load()
        return LoopResult(
            completed=False,
            iterations_run=self.max_iterations,
            final_phase=rrd.phase,
            total_analyzed=rrd.statistics.total_analyzed,
            total_presented=rrd.statistics.total_presented,
            total_insights=rrd.statistics.total_insights_extracted,
            error_message=f"Max iterations ({self.max_iterations}) reached",
        )

    def _run_iteration(self, runner: AgentRunner, iteration: int) -> IterationResult:
        """Run a single iteration of the loop."""
        # Load current state
        rrd = self.rrd_manager.load()
        phase = rrd.phase
        analyzed_before = rrd.statistics.total_analyzed

        # Check for phase validation (ANALYSIS needs enough papers)
        if phase == Phase.ANALYSIS:
            pool_count = len(rrd.papers_pool)
            target_count = rrd.requirements.target_papers
            if pool_count < target_count:
                # Revert to DISCOVERY
                rrd.phase = Phase.DISCOVERY
                self.rrd_manager.save()
                phase = Phase.DISCOVERY

        # Callback
        if self.on_iteration_start:
            self.on_iteration_start(iteration, phase)

        # Run agent
        if self.live_output and self.on_output:
            # Streaming mode
            output_lines: list[str] = []
            gen = runner.run_streaming(self.project_path)
            try:
                for line in gen:
                    output_lines.append(line)
                    self.on_output(line)
                # Get final result from generator return
                agent_result = gen.send(None)  # type: ignore
            except StopIteration as e:
                agent_result = e.value
        else:
            # Non-streaming mode
            agent_result = runner.run(self.project_path)

        # Handle failure
        if not agent_result.success:
            self.consecutive_failures += 1
            error_type = ErrorType(agent_result.error_type) if agent_result.error_type else ErrorType.UNKNOWN

            delay, should_retry = get_retry_delay(error_type)

            result = IterationResult(
                iteration=iteration,
                success=False,
                agent_result=agent_result,
                phase=phase,
                should_continue=should_retry and self.consecutive_failures < self.max_consecutive_failures,
                error_message=f"{error_type.value}: {agent_result.output[:200]}",
            )

            if self.on_iteration_end:
                self.on_iteration_end(result)

            if should_retry and delay > 0:
                time.sleep(delay)

            if self.consecutive_failures >= self.max_consecutive_failures:
                result.should_continue = False
                result.error_message = f"Too many consecutive failures ({self.consecutive_failures})"

            return result

        # Success - reset failure counter
        self.consecutive_failures = 0

        # Reload RRD to get updated state
        rrd = self.rrd_manager.load()
        analyzed_after = rrd.statistics.total_analyzed
        papers_delta = analyzed_after - analyzed_before

        # Check for completion
        is_complete = False

        # Primary: explicit completion signal
        if agent_result.is_complete:
            pending_count = len(rrd.pending_papers) + len(rrd.analyzing_papers)
            if pending_count == 0 and analyzed_after > 0:
                is_complete = True

        # Fallback: phase is COMPLETE
        if rrd.phase == Phase.COMPLETE:
            pending_count = len(rrd.pending_papers) + len(rrd.analyzing_papers)
            if pending_count == 0 and analyzed_after > 0:
                is_complete = True

        result = IterationResult(
            iteration=iteration,
            success=True,
            agent_result=agent_result,
            phase=rrd.phase,
            papers_delta=papers_delta,
            should_continue=not is_complete,
            is_complete=is_complete,
        )

        if self.on_iteration_end:
            self.on_iteration_end(result)

        # Small delay between iterations
        if not is_complete:
            time.sleep(2)

        return result
