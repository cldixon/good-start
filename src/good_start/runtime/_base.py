from __future__ import annotations

from typing import Protocol

from good_start.result import Result


class Runtime(Protocol):
    """Contract for executing the good-start agent."""

    async def run(self, prompt: str, target: str) -> Result: ...
