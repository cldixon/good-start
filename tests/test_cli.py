from datetime import datetime
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from good_start.cli import app
from good_start.result import AgentFindings, Result

runner = CliRunner()


def _make_result(passed: bool, details: str) -> Result:
    findings = AgentFindings(passed=passed, details=details)
    return Result(agent_messages=[], agent_result=findings)


class TestCheckCommand:
    @patch("good_start.cli.Agent")
    def test_passed_result(self, mock_agent_cls):
        result = _make_result(passed=True, details="All steps completed successfully.")
        instance = mock_agent_cls.return_value
        instance.run = AsyncMock(return_value=result)

        cli_result = runner.invoke(app, ["check", "."])

        assert cli_result.exit_code == 0
        assert "PASSED" in cli_result.output
        assert "All steps completed successfully." in cli_result.output

    @patch("good_start.cli.Agent")
    def test_failed_result(self, mock_agent_cls):
        result = _make_result(
            passed=False, details="pip install step failed due to missing dependency."
        )
        instance = mock_agent_cls.return_value
        instance.run = AsyncMock(return_value=result)

        cli_result = runner.invoke(app, ["check", "."])

        assert cli_result.exit_code == 1
        assert "FAILED" in cli_result.output
        assert "pip install step failed" in cli_result.output

    def test_nonexistent_path(self):
        cli_result = runner.invoke(app, ["check", "nonexistent-file.md"])

        assert cli_result.exit_code == 1
        assert "does not exist" in cli_result.output

    @patch("good_start.cli.Agent")
    def test_specific_file_target(self, mock_agent_cls):
        result = _make_result(passed=True, details="README checks passed.")
        instance = mock_agent_cls.return_value
        instance.run = AsyncMock(return_value=result)

        cli_result = runner.invoke(app, ["check", "README.md"])

        assert cli_result.exit_code == 0
        instance.run.assert_called_once()
        # verify the rendered prompt includes the specific file target
        rendered_prompt = instance.run.call_args[0][0]
        assert "README.md" in rendered_prompt

    @patch("good_start.cli.Agent")
    def test_default_target_is_dot(self, mock_agent_cls):
        result = _make_result(passed=True, details="Found and verified README.")
        instance = mock_agent_cls.return_value
        instance.run = AsyncMock(return_value=result)

        cli_result = runner.invoke(app, ["check"])

        assert cli_result.exit_code == 0
        rendered_prompt = instance.run.call_args[0][0]
        assert "getting-started documentation" in rendered_prompt

    @patch("good_start.cli.Agent")
    def test_output_includes_timestamp(self, mock_agent_cls):
        result = _make_result(passed=True, details="OK")
        instance = mock_agent_cls.return_value
        instance.run = AsyncMock(return_value=result)

        cli_result = runner.invoke(app, ["check", "."])

        assert cli_result.exit_code == 0
        # timestamp is in the panel subtitle as YYYY-MM-DD HH:MM:SS
        year = str(datetime.now().year)
        assert year in cli_result.output


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
