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
    if "429" in output or "too many requests" in output_lower or ("rate" in output_lower and "limit" in output_lower):
        return ErrorType.RATE_LIMIT
    if any(word in output_lower for word in ["bot", "challenge", "captcha", "blocked"]):
        return ErrorType.BOT_CHALLENGE
    if "timeout" in output_lower or "timed out" in output_lower:
        return ErrorType.TIMEOUT
    if any(word in output_lower for word in ["network", "connection", "dns"]):
        return ErrorType.NETWORK

    return ErrorType.UNKNOWN


RETRY_CONFIG: dict[ErrorType, tuple[int, bool]] = {
    ErrorType.FORBIDDEN: (0, False),
    ErrorType.BOT_CHALLENGE: (0, False),
    ErrorType.RATE_LIMIT: (30, True),
    ErrorType.TIMEOUT: (2, True),
    ErrorType.NETWORK: (2, True),
    ErrorType.UNKNOWN: (5, True),
}


def get_retry_delay(error_type: ErrorType) -> tuple[int, bool]:
    """
    Get retry delay and whether to retry for an error type.

    Returns:
        Tuple of (delay_seconds, should_retry)
    """
    return RETRY_CONFIG.get(error_type, (5, True))


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
        prompt_content, error = self._prepare_prompt(research_dir, prompt_path)
        if error:
            return error

        try:
            return self._run_agent(prompt_content, timeout)  # type: ignore
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

    def _get_command_and_input(self, prompt: str) -> tuple[list[str], Optional[str]]:
        """Get the command and optional stdin input for the agent."""
        if self.agent == Agent.CLAUDE:
            cmd = [
                "claude", "-p", prompt,
                "--dangerously-skip-permissions",
                "--allowedTools", "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch",
            ]
            return cmd, None
        elif self.agent == Agent.AMP:
            return ["amp", "--dangerously-allow-all"], prompt
        else:  # CODEX
            return ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "-"], prompt

    def _build_result(self, output: str, exit_code: int) -> AgentResult:
        """Build an AgentResult from output and exit code."""
        success = exit_code == 0
        error_type = None if success else classify_error(output).value
        return AgentResult(output=output, exit_code=exit_code, success=success, error_type=error_type)

    def _run_agent(self, prompt: str, timeout: int) -> AgentResult:
        """Run the agent and return the result."""
        cmd, stdin_input = self._get_command_and_input(prompt)

        # Codex requires special handling for last message output
        if self.agent == Agent.CODEX:
            return self._run_codex_with_output_file(cmd, stdin_input, timeout)

        result = subprocess.run(
            cmd, input=stdin_input, capture_output=True, text=True, timeout=timeout
        )
        return self._build_result(result.stdout + result.stderr, result.returncode)

    def _run_codex_with_output_file(
        self, base_cmd: list[str], stdin_input: Optional[str], timeout: int
    ) -> AgentResult:
        """Run Codex with temp file for last message output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            last_message_file = f.name

        try:
            cmd = base_cmd[:-1] + ["--output-last-message", last_message_file, "-"]
            result = subprocess.run(
                cmd, input=stdin_input, capture_output=True, text=True, timeout=timeout
            )

            last_message = ""
            try:
                with open(last_message_file) as f:
                    last_message = f.read()
            except (FileNotFoundError, PermissionError, IOError, UnicodeDecodeError):
                pass  # Codex output file is supplementary; continue without it

            return self._build_result(
                result.stdout + result.stderr + last_message, result.returncode
            )
        finally:
            try:
                os.unlink(last_message_file)
            except (FileNotFoundError, PermissionError, OSError):
                pass  # Temp file cleanup is best-effort

    def _prepare_prompt(
        self, research_dir: Path, prompt_path: Optional[Path]
    ) -> tuple[Optional[str], Optional[AgentResult]]:
        """Prepare prompt content, returning error result if prompt not found."""
        if prompt_path is None:
            prompt_path = self.script_dir / "prompt.md"

        if not prompt_path.exists():
            error = AgentResult(
                output=f"Prompt file not found: {prompt_path}",
                exit_code=1,
                success=False,
                error_type="missing_prompt",
            )
            return None, error

        with open(prompt_path) as f:
            content = f.read()
        return content.replace("{{RESEARCH_DIR}}", str(research_dir)), None

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
        prompt_content, error = self._prepare_prompt(research_dir, prompt_path)
        if error:
            return error

        cmd, stdin_input = self._get_command_and_input(prompt_content)  # type: ignore
        use_stdin = stdin_input is not None

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if use_stdin else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if use_stdin and process.stdin:
            process.stdin.write(stdin_input)  # type: ignore
            process.stdin.close()

        output_lines: list[str] = []
        if process.stdout:
            for line in process.stdout:
                output_lines.append(line)
                yield line

        process.wait()
        return self._build_result("".join(output_lines), process.returncode or 0)
