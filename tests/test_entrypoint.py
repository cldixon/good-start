import json
import sys
from unittest.mock import AsyncMock, patch

from good_start._entrypoint import main
from good_start.result import AgentFindings, Result


def _make_result(passed: bool, details: str) -> Result:
    findings = AgentFindings(passed=passed, details=details)
    return Result(agent_messages=[], agent_result=findings)


class TestEntrypoint:
    @patch("good_start._entrypoint.Agent")
    def test_outputs_json(self, mock_agent_cls, capsys, monkeypatch):
        result = _make_result(passed=True, details="All good")
        mock_agent_cls.return_value.run = AsyncMock(return_value=result)

        monkeypatch.setattr(
            sys, "argv", ["_entrypoint", "--prompt", "test prompt", "--target", "."]
        )
        main()

        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert data["passed"] is True
        assert data["details"] == "All good"

    @patch("good_start._entrypoint.Agent")
    def test_failed_result(self, mock_agent_cls, capsys, monkeypatch):
        result = _make_result(passed=False, details="Step 2 failed")
        mock_agent_cls.return_value.run = AsyncMock(return_value=result)

        monkeypatch.setattr(
            sys, "argv", ["_entrypoint", "--prompt", "test prompt", "--target", "."]
        )
        main()

        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert data["passed"] is False
        assert data["details"] == "Step 2 failed"
