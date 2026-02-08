from __future__ import annotations

from rich.console import Console

from good_start.agent import Agent
from good_start.display import print_tool_event
from good_start.result import Result

console = Console(stderr=True)


class LocalRuntime:
    """Runs the agent directly on the host machine."""

    async def run(self, prompt: str, target: str) -> Result:
        agent = Agent()

        def _on_tool_use(name: str, tool_input: dict) -> None:
            print_tool_event(name, tool_input, console)

        return await agent.run(prompt, on_tool_use=_on_tool_use)
