from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from good_start.result import AgentFindings, Result


def _make_result(passed: bool, details: str) -> Result:
    findings = AgentFindings(passed=passed, details=details)
    return Result(agent_messages=[], agent_result=findings)


def _mock_runtime(result: Result) -> MagicMock:
    runtime = MagicMock()
    runtime.run = AsyncMock(return_value=result)
    return runtime


# ---------------------------------------------------------------------------
# Unit tests — mock resolve_runtime, use the fixture via normal pytest injection
# ---------------------------------------------------------------------------


class TestFixtureCallable:
    @patch("good_start.plugin.resolve_runtime")
    def test_default_target(self, mock_resolve, good_start):
        """With no args, the prompt renders the '.' (auto-discover) branch."""
        result = _make_result(passed=True, details="OK")
        mock_resolve.return_value = _mock_runtime(result)

        ret = good_start()

        runtime = mock_resolve.return_value
        runtime.run.assert_called_once()
        rendered_prompt = runtime.run.call_args[0][0]
        assert "getting-started documentation" in rendered_prompt
        assert ret.passed is True

    @patch("good_start.plugin.resolve_runtime")
    def test_explicit_target(self, mock_resolve, good_start):
        """Passing a target directly renders that file in the prompt."""
        result = _make_result(passed=True, details="OK")
        mock_resolve.return_value = _mock_runtime(result)

        ret = good_start("README.md")

        rendered_prompt = mock_resolve.return_value.run.call_args[0][0]
        assert "README.md" in rendered_prompt
        assert ret.passed is True

    @patch("good_start.plugin.resolve_runtime")
    def test_returns_result_object(self, mock_resolve, good_start):
        """The factory returns a Result with passed and details."""
        result = _make_result(passed=False, details="Step 3 failed.")
        mock_resolve.return_value = _mock_runtime(result)

        ret = good_start()

        assert isinstance(ret, Result)
        assert ret.passed is False
        assert ret.details == "Step 3 failed."

    @patch("good_start.plugin.resolve_runtime")
    def test_custom_prompt_path(self, mock_resolve, good_start, tmp_path):
        """A custom prompt file is loaded when prompt_path is given."""
        prompt_file = tmp_path / "custom.md"
        prompt_file.write_text("Custom instructions for {{ target }}.")

        result = _make_result(passed=True, details="OK")
        mock_resolve.return_value = _mock_runtime(result)

        good_start(".", prompt_path=str(prompt_file))

        rendered_prompt = mock_resolve.return_value.run.call_args[0][0]
        assert "Custom instructions for ." in rendered_prompt


# ---------------------------------------------------------------------------
# Integration tests — pytester runs real pytest in a subprocess
# ---------------------------------------------------------------------------


class TestPluginRegistration:
    def test_marker_is_registered(self, pytester: pytest.Pytester):
        result = pytester.runpytest("--markers")
        result.stdout.fnmatch_lines(["*good_start*"])

    def test_cli_options_registered(self, pytester: pytest.Pytester):
        result = pytester.runpytest("--help")
        result.stdout.fnmatch_lines(["*--good-start-target*"])
        result.stdout.fnmatch_lines(["*--good-start-prompt*"])
        result.stdout.fnmatch_lines(["*--good-start-no-container*"])

    def test_fixture_is_available(self, pytester: pytest.Pytester):
        """A test requesting the fixture can be collected."""
        pytester.makepyfile(
            """
            def test_example(good_start):
                pass
            """
        )
        result = pytester.runpytest("--collect-only")
        result.stdout.fnmatch_lines(["*test_example*"])

    def test_auto_marker_deselection(self, pytester: pytest.Pytester):
        """Tests using the fixture are auto-marked and can be deselected."""
        pytester.makepyfile(
            """
            def test_with_fixture(good_start):
                pass

            def test_without_fixture():
                pass
            """
        )
        result = pytester.runpytest("-m", "not good_start", "-v")
        result.stdout.fnmatch_lines(["*test_without_fixture*"])
        assert "test_with_fixture" not in result.stdout.str()


class TestPluginExecution:
    def test_fixture_runs_with_mock(self, pytester: pytest.Pytester):
        """Full integration: fixture runs agent (mocked) and assertion works."""
        pytester.makeconftest(
            """
            from unittest.mock import AsyncMock, MagicMock, patch
            from good_start.result import AgentFindings, Result

            _patcher = None

            def pytest_configure(config):
                global _patcher
                _patcher = patch("good_start.plugin.resolve_runtime")
                mock_resolve = _patcher.start()
                findings = AgentFindings(passed=True, details="All good!")
                result = Result(agent_messages=[], agent_result=findings)
                runtime = MagicMock()
                runtime.run = AsyncMock(return_value=result)
                mock_resolve.return_value = runtime

            def pytest_unconfigure(config):
                if _patcher:
                    _patcher.stop()
            """
        )
        pytester.makepyfile(
            """
            def test_docs(good_start):
                result = good_start()
                assert result.passed, result.details
            """
        )
        result = pytester.runpytest("-v")
        result.stdout.fnmatch_lines(["*test_docs*PASSED*"])

    def test_failure_includes_details(self, pytester: pytest.Pytester):
        """On failure, agent details appear in the report output."""
        pytester.makeconftest(
            """
            from unittest.mock import AsyncMock, MagicMock, patch
            from good_start.result import AgentFindings, Result

            _patcher = None

            def pytest_configure(config):
                global _patcher
                _patcher = patch("good_start.plugin.resolve_runtime")
                mock_resolve = _patcher.start()
                findings = AgentFindings(passed=False, details="pip install broke on step 3")
                result = Result(agent_messages=[], agent_result=findings)
                runtime = MagicMock()
                runtime.run = AsyncMock(return_value=result)
                mock_resolve.return_value = runtime

            def pytest_unconfigure(config):
                if _patcher:
                    _patcher.stop()
            """
        )
        pytester.makepyfile(
            """
            def test_docs(good_start):
                result = good_start()
                assert result.passed, result.details
            """
        )
        result = pytester.runpytest("-v")
        result.stdout.fnmatch_lines(["*test_docs*FAILED*"])
        result.stdout.fnmatch_lines(["*good-start agent details*"])
        result.stdout.fnmatch_lines(["*pip install broke on step 3*"])
