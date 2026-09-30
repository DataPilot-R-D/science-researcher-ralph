"""Main research loop logic."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ralph.config import Agent, load_config
from ralph.core.agent_runner import AgentRunner, AgentResult, ErrorType, get_retry_delay, _get_repo_root
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
    1. COMPLETE phase and required research artifacts are verified
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
        self.prompt_path = project_path.parent / "prompt.md"
        if not self.prompt_path.is_file():
            self.prompt_path = _get_repo_root() / "prompt.md"

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
        if not self.prompt_path.is_file():
            errors.append("prompt.md not found")

        return errors

    def _build_loop_result(
        self, completed: bool, iterations: int, error_message: Optional[str] = None
    ) -> LoopResult:
        """Build a LoopResult from current RRD state."""
        rrd = self.rrd_manager.load()
        return LoopResult(
            completed=completed,
            iterations_run=iterations,
            final_phase=rrd.phase,
            total_analyzed=rrd.statistics.total_analyzed,
            total_presented=rrd.statistics.total_presented,
            total_insights=rrd.statistics.total_insights_extracted,
            error_message=error_message,
        )

    def run(self) -> LoopResult:
        """
        Run the research loop.

        Returns:
            LoopResult with final state
        """
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

        self.rrd_manager.ensure_progress_file()
        runner = AgentRunner(self.agent, self.project_path.parent)

        for i in range(1, self.max_iterations + 1):
            self.current_iteration = i
            result = self._run_iteration(runner, i)

            if not result.should_continue:
                return self._build_loop_result(result.is_complete, i, result.error_message)

        return self._build_loop_result(
            False, self.max_iterations, f"Max iterations ({self.max_iterations}) reached"
        )

    def _ensure_valid_phase(self) -> Phase:
        """Ensure phase is valid, reverting to DISCOVERY if needed."""
        rrd = self.rrd_manager.load()
        phase = rrd.phase

        if phase == Phase.ANALYSIS and len(rrd.papers_pool) < rrd.requirements.target_papers:
            rrd.phase = Phase.DISCOVERY
            self.rrd_manager.save()
            return Phase.DISCOVERY
        return phase

    def _run_agent(self, runner: AgentRunner) -> AgentResult:
        """Run the agent, with streaming if enabled."""
        if self.live_output and self.on_output:
            gen = runner.run_streaming(self.project_path, prompt_path=self.prompt_path)
            result = None
            try:
                while True:
                    line = next(gen)
                    self.on_output(line)
            except KeyboardInterrupt:
                raise  # Let Ctrl+C propagate
            except StopIteration as e:
                result = e.value

            # Check if we got a valid result
            if isinstance(result, AgentResult):
                return result

            # Unexpected: streaming didn't return AgentResult, fall back
            import sys
            print("Warning: Streaming did not return AgentResult, falling back to non-streaming", file=sys.stderr)
            return runner.run(self.project_path, prompt_path=self.prompt_path)
        return runner.run(self.project_path, prompt_path=self.prompt_path)

    def _handle_failure(
        self, iteration: int, phase: Phase, agent_result: AgentResult
    ) -> IterationResult:
        """Handle agent failure and return appropriate result."""
        self.consecutive_failures += 1
        error_type = ErrorType(agent_result.error_type) if agent_result.error_type else ErrorType.UNKNOWN
        delay, should_retry = get_retry_delay(error_type)

        too_many_failures = self.consecutive_failures >= self.max_consecutive_failures
        should_continue = should_retry and not too_many_failures

        error_msg = f"{error_type.value}: {agent_result.output[:200]}"
        if too_many_failures:
            error_msg = f"Too many consecutive failures ({self.consecutive_failures})"

        result = IterationResult(
            iteration=iteration,
            success=False,
            agent_result=agent_result,
            phase=phase,
            should_continue=should_continue,
            error_message=error_msg,
        )

        if self.on_iteration_end:
            self.on_iteration_end(result)

        if should_retry and delay > 0:
            time.sleep(delay)

        return result

    def _run_iteration(self, runner: AgentRunner, iteration: int) -> IterationResult:
        """Run a single iteration of the loop."""
        analyzed_before = self.rrd_manager.load().statistics.total_analyzed
        phase = self._ensure_valid_phase()

        if self.on_iteration_start:
            self.on_iteration_start(iteration, phase)

        agent_result = self._run_agent(runner)

        if not agent_result.success:
            return self._handle_failure(iteration, phase, agent_result)

        self.consecutive_failures = 0

        rrd = self.rrd_manager.load()
        papers_delta = rrd.statistics.total_analyzed - analyzed_before
        # Verify the saved state and artifacts; a tag in output is not sufficient.
        completion_errors = (
            self.rrd_manager.completion_errors(rrd) if rrd.phase == Phase.COMPLETE else []
        )
        is_complete = rrd.phase == Phase.COMPLETE and not completion_errors
        error_message = None
        if completion_errors:
            error_message = "Completion validation failed: " + "; ".join(completion_errors)

        result = IterationResult(
            iteration=iteration,
            success=error_message is None,
            agent_result=agent_result,
            phase=rrd.phase,
            papers_delta=papers_delta,
            should_continue=not is_complete and error_message is None,
            is_complete=is_complete,
            error_message=error_message,
        )

        if self.on_iteration_end:
            self.on_iteration_end(result)

        if result.should_continue:
            time.sleep(2)

        return result
