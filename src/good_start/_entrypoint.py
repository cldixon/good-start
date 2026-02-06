"""Entrypoint for running the good-start agent inside a container.

Invoked as ``python -m good_start._entrypoint`` by the container's
ENTRYPOINT.  Runs the agent and prints AgentFindings JSON to stdout,
which the host ContainerRuntime captures.
"""

from __future__ import annotations

import argparse
import asyncio

from good_start.agent import Agent
from good_start.result import AgentFindings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Rendered prompt string")
    parser.add_argument("--target", default=".", help="Target path")
    args = parser.parse_args()

    agent = Agent()
    result = asyncio.run(agent.run(args.prompt))

    findings = AgentFindings(passed=result.passed, details=result.details)
    print(findings.model_dump_json())


if __name__ == "__main__":
    main()
