from __future__ import annotations

from good_start.agent import Agent
from good_start.result import Result


class LocalRuntime:
    """Runs the agent directly on the host machine."""

    async def run(self, prompt: str, target: str) -> Result:
        agent = Agent()
        return await agent.run(prompt)
