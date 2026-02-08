"""Entrypoint for running the good-start agent inside a container.

Invoked as ``python -m good_start._entrypoint`` by the container's
ENTRYPOINT.  Runs the agent and prints AgentFindings JSON to stdout,
which the host ContainerRuntime captures.

Tool-use events are emitted as JSON lines to stderr so the host
runtime can display them in real-time.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from good_start.agent import Agent
from good_start.result import AgentFindings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Rendered prompt string")
    parser.add_argument("--target", default=".", help="Target path")
    args = parser.parse_args()

    def _on_tool_use(name: str, tool_input: dict) -> None:
        event = json.dumps({"tool": name, "input": tool_input})
        print(event, file=sys.stderr, flush=True)

    agent = Agent(permission_mode="bypassPermissions")
    try:
        result = asyncio.run(agent.run(args.prompt, on_tool_use=_on_tool_use))
        findings = AgentFindings(
            passed=result.passed,
            details=result.details,
            steps=result.steps,
            verification_command=result.verification_command,
        )
    except Exception as exc:
        findings = AgentFindings(
            passed=False,
            details=f"Agent encountered an error: {exc}",
        )
    print(findings.model_dump_json())


if __name__ == "__main__":
    main()
