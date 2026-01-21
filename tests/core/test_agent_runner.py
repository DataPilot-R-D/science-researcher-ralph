"""Tests for AgentRunner class and related functions."""

import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ralph.config import Agent
from ralph.core.agent_runner import (
    AgentRunner,
    AgentResult,
    ErrorType,
    classify_error,
    get_retry_delay,
)


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_basic_creation(self):
        """Test basic AgentResult creation."""
        result = AgentResult(
            output="Some output",
            exit_code=0,
            success=True,
        )
        assert result.output == "Some output"
        assert result.exit_code == 0
        assert result.success is True
        assert result.error_type is None

    def test_with_error_type(self):
        """Test AgentResult with error type."""
        result = AgentResult(
            output="Error",
            exit_code=1,
            success=False,
            error_type="rate_limit",
        )
        assert result.error_type == "rate_limit"

    def test_is_complete_true(self):
        """Test is_complete when completion signal present."""
        result = AgentResult(
            output="Research done! <promise>COMPLETE</promise>",
            exit_code=0,
            success=True,
        )
        assert result.is_complete is True

    def test_is_complete_false(self):
        """Test is_complete when signal absent."""
        result = AgentResult(
            output="Still working on research...",
            exit_code=0,
            success=True,
        )
        assert result.is_complete is False

    def test_is_complete_partial_signal(self):
        """Test is_complete with incomplete signal."""
        result = AgentResult(
            output="<promise>NOT COMPLETE</promise>",
            exit_code=0,
            success=True,
        )
        assert result.is_complete is False

    def test_claims_complete_positive_research_complete(self):
        """Test claims_complete with 'research complete' phrase."""
        result = AgentResult(
            output="The research is complete.",
            exit_code=0,
            success=True,
        )
        assert result.claims_complete is True

    def test_claims_complete_positive_papers_analyzed(self):
        """Test claims_complete with 'all papers analyzed' phrase."""
        result = AgentResult(
            output="All papers have been analyzed successfully.",
            exit_code=0,
            success=True,
        )
        assert result.claims_complete is True

    def test_claims_complete_with_not_negation(self):
        """Test claims_complete with 'not complete' negation."""
        result = AgentResult(
            output="Research is not complete yet",
            exit_code=0,
            success=True,
        )
        assert result.claims_complete is False

    def test_claims_complete_with_isnt_negation(self):
        """Test claims_complete with 'isn't' negation."""
        result = AgentResult(
            output="The research isn't complete",
            exit_code=0,
            success=True,
        )
        assert result.claims_complete is False

    def test_claims_complete_with_arent_negation(self):
        """Test claims_complete with 'aren't analyzed' negation."""
        result = AgentResult(
            output="Papers aren't all analyzed yet",
            exit_code=0,
            success=True,
        )
        assert result.claims_complete is False

    def test_claims_complete_neutral_text(self):
        """Test claims_complete with neutral text."""
        result = AgentResult(
            output="Analyzing paper 5 of 20...",
            exit_code=0,
            success=True,
        )
        assert result.claims_complete is False


class TestErrorType:
    """Tests for ErrorType enum."""

    def test_all_error_types(self):
        """Verify all expected error types."""
        assert ErrorType.RATE_LIMIT.value == "rate_limit"
        assert ErrorType.FORBIDDEN.value == "forbidden"
        assert ErrorType.BOT_CHALLENGE.value == "bot_challenge"
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.NETWORK.value == "network"
        assert ErrorType.UNKNOWN.value == "unknown"

    def test_error_type_count(self):
        """Verify we have all expected error types."""
        assert len(ErrorType) == 6


class TestClassifyError:
    """Tests for classify_error function."""

    @pytest.mark.parametrize(
        "output,expected",
        [
            ("Error 403 Forbidden", ErrorType.FORBIDDEN),
            ("403: Access denied", ErrorType.FORBIDDEN),
            ("forbidden access to resource", ErrorType.FORBIDDEN),
            ("HTTP 429 Too Many Requests", ErrorType.RATE_LIMIT),
            ("rate limit exceeded", ErrorType.RATE_LIMIT),
            ("Rate Limit reached", ErrorType.RATE_LIMIT),
            ("Bot challenge detected", ErrorType.BOT_CHALLENGE),
            ("captcha required", ErrorType.BOT_CHALLENGE),
            ("blocked by server", ErrorType.BOT_CHALLENGE),
            ("Request timed out", ErrorType.TIMEOUT),
            ("connection timeout", ErrorType.TIMEOUT),
            ("timed out waiting for response", ErrorType.TIMEOUT),
            ("Network error occurred", ErrorType.NETWORK),
            ("DNS lookup failed", ErrorType.NETWORK),
            ("connection refused", ErrorType.NETWORK),
            ("some random error message", ErrorType.UNKNOWN),
            ("syntax error in code", ErrorType.UNKNOWN),
        ],
    )
    def test_classify_error(self, output, expected):
        """Test error classification for various outputs."""
        assert classify_error(output) == expected

    def test_classify_error_case_insensitive(self):
        """Test error classification is case insensitive."""
        assert classify_error("FORBIDDEN") == ErrorType.FORBIDDEN
        assert classify_error("Timeout") == ErrorType.TIMEOUT
        assert classify_error("BLOCKED") == ErrorType.BOT_CHALLENGE

    def test_classify_error_empty_string(self):
        """Test error classification with empty string."""
        assert classify_error("") == ErrorType.UNKNOWN


class TestGetRetryDelay:
    """Tests for get_retry_delay function."""

    def test_forbidden_no_retry(self):
        """Test forbidden errors don't retry."""
        delay, should_retry = get_retry_delay(ErrorType.FORBIDDEN)
        assert delay == 0
        assert should_retry is False

    def test_bot_challenge_no_retry(self):
        """Test bot challenge errors don't retry."""
        delay, should_retry = get_retry_delay(ErrorType.BOT_CHALLENGE)
        assert delay == 0
        assert should_retry is False

    def test_rate_limit_retry_with_delay(self):
        """Test rate limit errors retry with delay."""
        delay, should_retry = get_retry_delay(ErrorType.RATE_LIMIT)
        assert delay == 30
        assert should_retry is True

    def test_timeout_retry_short_delay(self):
        """Test timeout errors retry with short delay."""
        delay, should_retry = get_retry_delay(ErrorType.TIMEOUT)
        assert delay == 2
        assert should_retry is True

    def test_network_retry_short_delay(self):
        """Test network errors retry with short delay."""
        delay, should_retry = get_retry_delay(ErrorType.NETWORK)
        assert delay == 2
        assert should_retry is True

    def test_unknown_retry_default(self):
        """Test unknown errors retry with default delay."""
        delay, should_retry = get_retry_delay(ErrorType.UNKNOWN)
        assert delay == 5
        assert should_retry is True


class TestAgentRunnerInit:
    """Tests for AgentRunner initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default script_dir."""
        runner = AgentRunner(Agent.CLAUDE)
        assert runner.agent == Agent.CLAUDE
        assert runner.script_dir is not None

    def test_init_with_custom_script_dir(self, tmp_path):
        """Test initialization with custom script_dir."""
        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)
        assert runner.script_dir == tmp_path

    def test_init_all_agents(self, tmp_path):
        """Test initialization with all agent types."""
        for agent in Agent:
            runner = AgentRunner(agent, script_dir=tmp_path)
            assert runner.agent == agent


class TestAgentRunnerIsAvailable:
    """Tests for AgentRunner.is_available method."""

    def test_is_available_true(self):
        """Test is_available when agent CLI exists."""
        with patch("shutil.which", return_value="/usr/local/bin/claude"):
            runner = AgentRunner(Agent.CLAUDE)
            assert runner.is_available() is True

    def test_is_available_false(self):
        """Test is_available when agent CLI missing."""
        with patch("shutil.which", return_value=None):
            runner = AgentRunner(Agent.CLAUDE)
            assert runner.is_available() is False

    def test_is_available_checks_agent_name(self):
        """Test that is_available checks the correct agent name."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None

            runner = AgentRunner(Agent.AMP)
            runner.is_available()

            mock_which.assert_called_once_with("amp")


class TestAgentRunnerGetInstallInstructions:
    """Tests for AgentRunner.get_install_instructions method."""

    @pytest.mark.parametrize(
        "agent,expected_url",
        [
            (Agent.CLAUDE, "claude.ai/code"),
            (Agent.AMP, "ampcode.com"),
            (Agent.CODEX, "openai.com/codex"),
        ],
    )
    def test_get_install_instructions(self, agent, expected_url):
        """Test install instructions for each agent."""
        runner = AgentRunner(agent)
        instructions = runner.get_install_instructions()
        assert expected_url in instructions


class TestAgentRunnerRun:
    """Tests for AgentRunner.run method."""

    def test_run_missing_prompt(self, tmp_path):
        """Test run when prompt.md missing."""
        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)

        result = runner.run(tmp_path)

        assert result.success is False
        assert "not found" in result.output
        assert result.error_type == "missing_prompt"

    @patch("subprocess.run")
    def test_run_claude_success(self, mock_run, tmp_path):
        """Test successful Claude run."""
        # Setup prompt file
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt {{RESEARCH_DIR}}")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success output",
            stderr="",
        )

        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)
        result = runner.run(tmp_path)

        assert result.success is True
        assert result.exit_code == 0
        assert "Success output" in result.output
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_claude_with_path_injection(self, mock_run, tmp_path):
        """Test that research dir is injected into prompt."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Research at {{RESEARCH_DIR}}")

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)
        runner.run(tmp_path / "my-research")

        # Verify the prompt was modified
        call_args = mock_run.call_args
        prompt_in_call = call_args[0][0][2]  # Third arg is the prompt
        assert "my-research" in prompt_in_call

    @patch("subprocess.run")
    def test_run_amp_success(self, mock_run, tmp_path):
        """Test successful Amp run (input via stdin)."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt")

        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        runner = AgentRunner(Agent.AMP, script_dir=tmp_path)
        result = runner.run(tmp_path)

        assert result.success is True
        # Verify amp command structure
        call_args = mock_run.call_args
        assert "amp" in call_args[0][0]
        assert "--dangerously-allow-all" in call_args[0][0]
        # Verify input was provided
        assert call_args[1].get("input") is not None

    @patch("subprocess.run")
    def test_run_codex_success(self, mock_run, tmp_path):
        """Test successful Codex run."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt")

        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        runner = AgentRunner(Agent.CODEX, script_dir=tmp_path)

        with patch("builtins.open", MagicMock()):
            with patch("os.unlink"):
                result = runner.run(tmp_path)

        assert result.success is True

    @patch("subprocess.run")
    def test_run_timeout(self, mock_run, tmp_path):
        """Test handling subprocess timeout."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt")

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 600)

        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)
        result = runner.run(tmp_path)

        assert result.success is False
        assert result.exit_code == 124
        assert result.error_type == ErrorType.TIMEOUT.value

    @patch("subprocess.run")
    def test_run_failure_classifies_error(self, mock_run, tmp_path):
        """Test run failure classifies error type."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt")

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error 429 rate limit exceeded",
        )

        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)
        result = runner.run(tmp_path)

        assert result.success is False
        assert result.error_type == ErrorType.RATE_LIMIT.value

    @patch("subprocess.run")
    def test_run_generic_exception(self, mock_run, tmp_path):
        """Test run handles generic exceptions."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt")

        mock_run.side_effect = Exception("Something went wrong")

        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)
        result = runner.run(tmp_path)

        assert result.success is False
        assert result.error_type == ErrorType.UNKNOWN.value
        assert "Something went wrong" in result.output

    @patch("subprocess.run")
    def test_run_custom_timeout(self, mock_run, tmp_path):
        """Test run with custom timeout."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt")

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)
        runner.run(tmp_path, timeout=1200)

        # Verify timeout was passed
        call_args = mock_run.call_args
        assert call_args[1]["timeout"] == 1200


class TestAgentRunnerRunStreaming:
    """Tests for AgentRunner.run_streaming method."""

    def test_run_streaming_missing_prompt(self, tmp_path):
        """Test streaming run when prompt missing."""
        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)

        gen = runner.run_streaming(tmp_path)

        # Exhaust the generator to get the result
        result = None
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

        assert isinstance(result, AgentResult)
        assert result.success is False
        assert result.error_type == "missing_prompt"

    @patch("subprocess.Popen")
    def test_run_streaming_collects_lines(self, mock_popen, tmp_path):
        """Test streaming run yields output lines."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt")

        mock_process = MagicMock()
        mock_process.stdout = iter(["Line 1\n", "Line 2\n", "Done\n"])
        mock_process.stdin = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        runner = AgentRunner(Agent.CLAUDE, script_dir=tmp_path)
        gen = runner.run_streaming(tmp_path)

        lines = []
        result = None
        try:
            while True:
                line = next(gen)
                lines.append(line)
        except StopIteration as e:
            result = e.value

        assert len(lines) == 3
        assert result.success is True

    @patch("subprocess.Popen")
    def test_run_streaming_amp_uses_stdin(self, mock_popen, tmp_path):
        """Test streaming run with Amp uses stdin."""
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text("Test prompt")

        mock_process = MagicMock()
        mock_process.stdout = iter([])
        mock_process.stdin = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        runner = AgentRunner(Agent.AMP, script_dir=tmp_path)

        # Exhaust the generator
        gen = runner.run_streaming(tmp_path)
        try:
            while True:
                next(gen)
        except StopIteration:
            pass

        # Verify stdin was used
        mock_process.stdin.write.assert_called()
        mock_process.stdin.close.assert_called()
