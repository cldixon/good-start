from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from good_start.cli import app
from good_start.result import AgentFindings, Result

runner = CliRunner()


def _make_result(passed: bool, details: str) -> Result:
    findings = AgentFindings(passed=passed, details=details)
    return Result(agent_messages=[], agent_result=findings)


def _mock_runtime(result: Result) -> MagicMock:
    runtime = MagicMock()
    runtime.run = AsyncMock(return_value=result)
    return runtime


class TestCheckCommand:
    @patch("good_start.cli.resolve_runtime")
    def test_passed_result(self, mock_resolve):
        result = _make_result(passed=True, details="All steps completed successfully.")
        mock_resolve.return_value = _mock_runtime(result)

        cli_result = runner.invoke(app, ["check", "."])

        assert cli_result.exit_code == 0
        assert "PASSED" in cli_result.output
        assert "All steps completed successfully." in cli_result.output

    @patch("good_start.cli.resolve_runtime")
    def test_failed_result(self, mock_resolve):
        result = _make_result(
            passed=False, details="pip install step failed due to missing dependency."
        )
        mock_resolve.return_value = _mock_runtime(result)

        cli_result = runner.invoke(app, ["check", "."])

        assert cli_result.exit_code == 1
        assert "FAILED" in cli_result.output
        assert "pip install step failed" in cli_result.output

    def test_nonexistent_path(self):
        cli_result = runner.invoke(app, ["check", "nonexistent-file.md"])

        assert cli_result.exit_code == 1
        assert "does not exist" in cli_result.output

    @patch("good_start.cli.resolve_runtime")
    def test_specific_file_target(self, mock_resolve):
        result = _make_result(passed=True, details="README checks passed.")
        mock_resolve.return_value = _mock_runtime(result)

        cli_result = runner.invoke(app, ["check", "README.md"])

        assert cli_result.exit_code == 0
        # verify the rendered prompt includes the specific file target
        rendered_prompt = mock_resolve.return_value.run.call_args[0][0]
        assert "README.md" in rendered_prompt

    @patch("good_start.cli.resolve_runtime")
    def test_default_target_is_dot(self, mock_resolve):
        result = _make_result(passed=True, details="Found and verified README.")
        mock_resolve.return_value = _mock_runtime(result)

        cli_result = runner.invoke(app, ["check"])

        assert cli_result.exit_code == 0
        rendered_prompt = mock_resolve.return_value.run.call_args[0][0]
        assert "getting-started documentation" in rendered_prompt

    @patch("good_start.cli.resolve_runtime")
    def test_output_includes_timestamp(self, mock_resolve):
        result = _make_result(passed=True, details="OK")
        mock_resolve.return_value = _mock_runtime(result)

        cli_result = runner.invoke(app, ["check", "."])

        assert cli_result.exit_code == 0
        year = str(datetime.now().year)
        assert year in cli_result.output

    @patch("good_start.cli.resolve_runtime")
    def test_shows_verification_command(self, mock_resolve):
        findings = AgentFindings(
            passed=True,
            details="All good.",
            verification_command='python -c "import good_start"',
        )
        result = Result(agent_messages=[], agent_result=findings)
        mock_resolve.return_value = _mock_runtime(result)

        cli_result = runner.invoke(app, ["check", "."])

        assert cli_result.exit_code == 0
        assert 'python -c "import good_start"' in cli_result.output

    @patch("good_start.cli.resolve_runtime")
    def test_no_verification_command(self, mock_resolve):
        result = _make_result(passed=True, details="OK")
        mock_resolve.return_value = _mock_runtime(result)

        cli_result = runner.invoke(app, ["check", "."])

        assert cli_result.exit_code == 0
        assert "Verification" not in cli_result.output


class TestNoContainerFlag:
    @patch("good_start.cli.resolve_runtime")
    def test_no_container_flag(self, mock_resolve):
        result = _make_result(passed=True, details="OK")
        mock_resolve.return_value = _mock_runtime(result)

        runner.invoke(app, ["check", ".", "--no-container"])

        mock_resolve.assert_called_once_with(no_container=True, verbose=False)

    @patch("good_start.cli.resolve_runtime")
    def test_default_uses_container(self, mock_resolve):
        result = _make_result(passed=True, details="OK")
        mock_resolve.return_value = _mock_runtime(result)

        runner.invoke(app, ["check", "."])

        mock_resolve.assert_called_once_with(no_container=False, verbose=False)


class TestHelpOutput:
    def test_app_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert (
            "good-start" in result.output.lower()
            or "documentation" in result.output.lower()
        )

    def test_check_help(self):
        result = runner.invoke(app, ["check", "--help"])
        assert result.exit_code == 0
        assert "target" in result.output.lower()
        # Rich/Typer inserts ANSI color codes that split option names;
        # check for the meaningful substring instead.
        assert "container" in result.output
