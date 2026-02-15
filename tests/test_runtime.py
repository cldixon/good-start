import asyncio
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from good_start.result import AgentFindings, Result
from good_start.runtime import resolve_runtime
from good_start.runtime._container import ContainerRuntime, _detect_engine
from good_start.runtime._local import LocalRuntime


def _make_result(passed: bool, details: str) -> Result:
    findings = AgentFindings(passed=passed, details=details)
    return Result(agent_messages=[], agent_result=findings)


class TestResolveRuntime:
    def test_no_container_returns_local(self):
        rt = resolve_runtime(no_container=True)
        assert isinstance(rt, LocalRuntime)

    @patch("good_start.runtime._container.shutil.which", return_value="/usr/bin/podman")
    def test_default_returns_container(self, _mock_which):
        rt = resolve_runtime(no_container=False)
        assert isinstance(rt, ContainerRuntime)

    @patch("good_start.runtime._container.shutil.which", return_value=None)
    def test_no_engine_raises(self, _mock_which):
        with pytest.raises(RuntimeError, match="No container engine"):
            resolve_runtime(no_container=False)


class TestLocalRuntime:
    @patch("good_start.runtime._local.Agent")
    def test_run_delegates_to_agent(self, mock_agent_cls):
        result = _make_result(passed=True, details="OK")
        mock_agent_cls.return_value.run = AsyncMock(return_value=result)

        rt = LocalRuntime()
        ret = asyncio.run(rt.run("prompt text", "."))

        assert ret.passed is True
        call_args = mock_agent_cls.return_value.run.call_args
        assert call_args[0][0] == "prompt text"
        assert call_args[1]["on_tool_use"] is not None


class TestDetectEngine:
    @patch("good_start.runtime._container.shutil.which")
    def test_prefers_podman(self, mock_which):
        mock_which.side_effect = lambda cmd: (
            "/usr/bin/podman" if cmd == "podman" else None
        )
        assert _detect_engine() == "podman"

    @patch("good_start.runtime._container.shutil.which")
    def test_falls_back_to_docker(self, mock_which):
        mock_which.side_effect = lambda cmd: (
            "/usr/bin/docker" if cmd == "docker" else None
        )
        assert _detect_engine() == "docker"

    @patch("good_start.runtime._container.shutil.which", return_value=None)
    def test_raises_when_none_found(self, _mock_which):
        with pytest.raises(RuntimeError, match="No container engine"):
            _detect_engine()


def _mock_popen(stdout: str, stderr: str = "", returncode: int = 0):
    """Create a mock Popen object with given stdout/stderr/returncode."""
    stderr_lines = stderr.splitlines(keepends=True) if stderr else []
    stderr_index = {"i": 0}

    def _readline():
        if stderr_index["i"] < len(stderr_lines):
            line = stderr_lines[stderr_index["i"]]
            stderr_index["i"] += 1
            return line
        return ""

    proc = MagicMock()
    proc.stdout.read.return_value = stdout
    proc.stderr.readline = _readline
    proc.poll.return_value = returncode
    proc.returncode = returncode
    return proc


@patch("good_start.runtime._container._resolve_api_key", return_value="sk-test-key")
class TestContainerRuntime:
    @patch("good_start.runtime._container.subprocess.Popen")
    @patch("good_start.runtime._container.subprocess.run")
    @patch("good_start.runtime._container.shutil.which", return_value="/usr/bin/podman")
    def test_successful_run(self, _mock_which, mock_run, mock_popen, _mock_key):
        findings_json = '{"passed": true, "details": "All good"}'
        # subprocess.run is used for image inspect
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        # subprocess.Popen is used for the container run
        mock_popen.return_value = _mock_popen(stdout=findings_json)

        rt = ContainerRuntime()
        result = asyncio.run(rt.run("prompt", "."))

        assert result.passed is True
        assert result.details == "All good"

    @patch("good_start.runtime._container.subprocess.Popen")
    @patch("good_start.runtime._container.subprocess.run")
    @patch("good_start.runtime._container.shutil.which", return_value="/usr/bin/podman")
    def test_container_failure(self, _mock_which, mock_run, mock_popen, _mock_key):
        # subprocess.run is used for image inspect
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        # subprocess.Popen is used for the container run (fails)
        mock_popen.return_value = _mock_popen(stdout="", returncode=1)

        rt = ContainerRuntime()
        result = asyncio.run(rt.run("prompt", "."))

        assert result.passed is False
        assert "Container exited with code 1" in result.details

    @patch("good_start.runtime._container.subprocess.Popen")
    @patch("good_start.runtime._container.subprocess.run")
    @patch("good_start.runtime._container.shutil.which", return_value="/usr/bin/podman")
    def test_builds_image_when_missing(
        self, _mock_which, mock_run, mock_popen, _mock_key
    ):
        findings_json = '{"passed": true, "details": "OK"}'
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 1),  # image inspect — not found
            subprocess.CompletedProcess([], 0),  # build
        ]
        mock_popen.return_value = _mock_popen(stdout=findings_json)

        rt = ContainerRuntime()
        result = asyncio.run(rt.run("prompt", "."))

        assert result.passed is True
        # Second subprocess.run call should be the build command
        build_call = mock_run.call_args_list[1]
        assert "build" in build_call[0][0]

    @patch("good_start.runtime._container.subprocess.run")
    @patch("good_start.runtime._container.shutil.which", return_value="/usr/bin/podman")
    def test_missing_api_key_raises(
        self, _mock_which, mock_run, _mock_key, tmp_path, monkeypatch
    ):
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        _mock_key.return_value = None  # override class-level mock
        rt = ContainerRuntime()
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY is not set"):
            asyncio.run(rt.run("prompt", "."))

    @patch("good_start.runtime._container.subprocess.Popen")
    @patch("good_start.runtime._container.subprocess.run")
    @patch("good_start.runtime._container.shutil.which", return_value="/usr/bin/podman")
    def test_streams_tool_events_from_stderr(
        self, _mock_which, mock_run, mock_popen, _mock_key
    ):
        findings_json = '{"passed": true, "details": "OK"}'
        stderr_lines = '{"tool": "Bash", "input": {"command": "pip install foo"}}\n'
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        mock_popen.return_value = _mock_popen(stdout=findings_json, stderr=stderr_lines)

        rt = ContainerRuntime()
        result = asyncio.run(rt.run("prompt", "."))

        assert result.passed is True
