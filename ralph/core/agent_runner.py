"""Agent invocation for running AI agents (Claude, Amp, Codex)."""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Generator, Optional

from ralph.config import Agent


@dataclass
class AgentResult:
    """Result from running an agent."""

    output: str
    exit_code: int
    success: bool
    error_type: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        """Check if agent signaled completion."""
        return "<promise>COMPLETE</promise>" in self.output

    @property
    def claims_complete(self) -> bool:
        """Check if agent claims completion in plain English."""
        output_lower = self.output.lower()
        completion_phrases = [
            "research.*complete",
            "all.*papers.*analyzed",
            "research is complete",
        ]
        negation_phrases = [
            "not.*complete",
            "isn't complete",
            "is not complete",
            "aren't.*analyzed",
            "not.*analyzed",
        ]

        import re

        has_completion = any(re.search(phrase, output_lower) for phrase in completion_phrases)
        has_negation = any(re.search(phrase, output_lower) for phrase in negation_phrases)

        return has_completion and not has_negation


class ErrorType(str, Enum):
    """Types of agent errors."""

    RATE_LIMIT = "rate_limit"
    FORBIDDEN = "forbidden"
    BOT_CHALLENGE = "bot_challenge"
    TIMEOUT = "timeout"
    NETWORK = "network"
    UNKNOWN = "unknown"


def classify_error(output: str) -> ErrorType:
    """Classify the type of error from agent output."""
    output_lower = output.lower()

    if "403" in output or "forbidden" in output_lower:
        return ErrorType.FORBIDDEN
    if "429" in output or "too many requests" in output_lower or "rate" in output_lower and "limit" in output_lower:
        return ErrorType.RATE_LIMIT
    if any(word in output_lower for word in ["bot", "challenge", "captcha", "blocked"]):
        return ErrorType.BOT_CHALLENGE
    if "timeout" in output_lower or "timed out" in output_lower:
        return ErrorType.TIMEOUT
    if any(word in output_lower for word in ["network", "connection", "dns"]):
        return ErrorType.NETWORK

    return ErrorType.UNKNOWN


def get_retry_delay(error_type: ErrorType) -> tuple[int, bool]:
    """
    Get retry delay and whether to retry for an error type.

    Returns:
        Tuple of (delay_seconds, should_retry)
    """
    if error_type == ErrorType.FORBIDDEN:
        return 0, False
    if error_type == ErrorType.BOT_CHALLENGE:
        return 0, False
    if error_type == ErrorType.RATE_LIMIT:
        return 30, True
    if error_type in (ErrorType.TIMEOUT, ErrorType.NETWORK):
        return 2, True

    return 5, True


def _get_repo_root() -> Path:
    """Get the repository root directory."""
    # Try to find repo root by looking for known markers
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Max 5 levels up
        if (current / "pyproject.toml").exists() or (current / "prompt.md").exists():
            return current
        current = current.parent
    # Fallback to package parent
    return Path(__file__).parent.parent


class AgentRunner:
    """Runs AI agents (Claude, Amp, Codex) with research prompts."""

    def __init__(self, agent: Agent, script_dir: Optional[Path] = None):
        """
        Initialize agent runner.

        Args:
            agent: The agent type to use
            script_dir: Directory containing prompt.md (repo root)
        """
        self.agent = agent
        self.script_dir = script_dir or _get_repo_root()

    def is_available(self) -> bool:
        """Check if the agent CLI is available."""
        return shutil.which(self.agent.value) is not None

    def get_install_instructions(self) -> str:
        """Get installation instructions for the agent."""
        instructions = {
            Agent.CLAUDE: "Install from: https://claude.ai/code",
            Agent.AMP: "Install from: https://ampcode.com",
            Agent.CODEX: "Install from: https://openai.com/codex",
        }
        return instructions.get(self.agent, f"Unknown agent: {self.agent}")

    def run(
        self,
        research_dir: Path,
        prompt_path: Optional[Path] = None,
        timeout: int = 600,
    ) -> AgentResult:
        """
        Run the agent with the research prompt.

        Args:
            research_dir: Path to the research folder
            prompt_path: Path to prompt.md (default: script_dir/prompt.md)
            timeout: Timeout in seconds

        Returns:
            AgentResult with output and status
        """
        if prompt_path is None:
            prompt_path = self.script_dir / "prompt.md"

        if not prompt_path.exists():
            return AgentResult(
                output=f"Prompt file not found: {prompt_path}",
                exit_code=1,
                success=False,
                error_type="missing_prompt",
            )

        # Read and prepare prompt
        with open(prompt_path) as f:
            prompt_content = f.read()

        # Inject research directory path
        prompt_content = prompt_content.replace("{{RESEARCH_DIR}}", str(research_dir))

        try:
            if self.agent == Agent.AMP:
                result = self._run_amp(prompt_content, timeout)
            elif self.agent == Agent.CODEX:
                result = self._run_codex(prompt_content, timeout)
            else:  # CLAUDE
                result = self._run_claude(prompt_content, timeout)

            return result

        except subprocess.TimeoutExpired:
            return AgentResult(
                output="Agent timed out",
                exit_code=124,
                success=False,
                error_type=ErrorType.TIMEOUT.value,
            )
        except Exception as e:
            return AgentResult(
                output=str(e),
                exit_code=1,
                success=False,
                error_type=ErrorType.UNKNOWN.value,
            )

    def _run_claude(self, prompt: str, timeout: int) -> AgentResult:
        """Run Claude Code CLI."""
        cmd = [
            "claude",
            "-p",
            prompt,
            "--dangerously-skip-permissions",
            "--allowedTools",
            "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = result.stdout + result.stderr
        exit_code = result.returncode
        success = exit_code == 0

        error_type = None
        if not success:
            error_type = classify_error(output).value

        return AgentResult(
            output=output,
            exit_code=exit_code,
            success=success,
            error_type=error_type,
        )

    def _run_amp(self, prompt: str, timeout: int) -> AgentResult:
        """Run Amp CLI."""
        result = subprocess.run(
            ["amp", "--dangerously-allow-all"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = result.stdout + result.stderr
        exit_code = result.returncode
        success = exit_code == 0

        error_type = None
        if not success:
            error_type = classify_error(output).value

        return AgentResult(
            output=output,
            exit_code=exit_code,
            success=success,
            error_type=error_type,
        )

    def _run_codex(self, prompt: str, timeout: int) -> AgentResult:
        """Run Codex CLI."""
        # Codex requires a temp file for last message output
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            last_message_file = f.name

        try:
            result = subprocess.run(
                [
                    "codex",
                    "exec",
                    "--dangerously-bypass-approvals-and-sandbox",
                    "--output-last-message",
                    last_message_file,
                    "-",
                ],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Read last message from file
            try:
                with open(last_message_file) as f:
                    last_message = f.read()
            except Exception:
                last_message = ""

            output = result.stdout + result.stderr + last_message
            exit_code = result.returncode
            success = exit_code == 0

            error_type = None
            if not success:
                error_type = classify_error(output).value

            return AgentResult(
                output=output,
                exit_code=exit_code,
                success=success,
                error_type=error_type,
            )
        finally:
            # Clean up temp file
            try:
                os.unlink(last_message_file)
            except Exception:
                pass

    def run_streaming(
        self,
        research_dir: Path,
        prompt_path: Optional[Path] = None,
    ) -> Generator[str, None, AgentResult]:
        """
        Run the agent with streaming output.

        Yields lines as they come, returns final result.

        Args:
            research_dir: Path to the research folder
            prompt_path: Path to prompt.md

        Yields:
            Output lines as they're produced

        Returns:
            Final AgentResult
        """
        if prompt_path is None:
            prompt_path = self.script_dir / "prompt.md"

        if not prompt_path.exists():
            return AgentResult(
                output=f"Prompt file not found: {prompt_path}",
                exit_code=1,
                success=False,
                error_type="missing_prompt",
            )

        # Read and prepare prompt
        with open(prompt_path) as f:
            prompt_content = f.read()

        prompt_content = prompt_content.replace("{{RESEARCH_DIR}}", str(research_dir))

        # Build command based on agent
        if self.agent == Agent.AMP:
            cmd = ["amp", "--dangerously-allow-all"]
            use_stdin = True
        elif self.agent == Agent.CODEX:
            cmd = ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "-"]
            use_stdin = True
        else:  # CLAUDE
            cmd = [
                "claude",
                "-p",
                prompt_content,
                "--dangerously-skip-permissions",
                "--allowedTools",
                "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch",
            ]
            use_stdin = False

        # Run with streaming
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if use_stdin else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if use_stdin and process.stdin:
            process.stdin.write(prompt_content)
            process.stdin.close()

        output_lines: list[str] = []
        if process.stdout:
            for line in process.stdout:
                output_lines.append(line)
                yield line

        process.wait()
        output = "".join(output_lines)
        exit_code = process.returncode
        success = exit_code == 0

        error_type = None
        if not success:
            error_type = classify_error(output).value

        return AgentResult(
            output=output,
            exit_code=exit_code,
            success=success,
            error_type=error_type,
        )
