from __future__ import annotations

from datetime import datetime
from typing import Any

from claude_agent_sdk import Message
from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    tool: str = Field(description="The tool used (e.g., Bash, Read, Grep, Glob).")
    input: str = Field(description="The command or argument passed to the tool.")
    output: str = Field(
        description="The tool's output or result, truncated if very long."
    )
    is_error: bool = Field(
        default=False, description="Whether the tool call resulted in an error."
    )


class AgentFindings(BaseModel):
    passed: bool = Field(
        description="Boolean indicating whether the agent was able to follow the instructions end to end."
    )
    details: str = Field(
        description="""
        Summary details of how the attempt to follow the instructions went.
        If the test did not pass, provide direct constructive feedback to
        help the maintainer understand where to make corrections.
        """,
        examples=[
            "The test passed with flying colors. No notes!",
            "The test failed because the instructions around pip installation were not accurate.",
            "The URL for downloading is no longer reachable.",
        ],
    )
    steps: list[AgentStep] = Field(
        default_factory=list,
        description="An ordered log of every tool action taken during the check. "
        "Include each Bash command, file read, grep, etc.",
    )
    verification_command: str | None = Field(
        default=None,
        description="The specific command used to verify that the software was "
        "successfully installed (e.g., 'python -c \"import good_start\"'). "
        "None if verification was not performed.",
    )


def _dereference_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline all $ref references so the schema has no $defs block.

    The claude CLI's structured-output validation does not handle
    Pydantic's $defs/$ref pattern, so we flatten before passing it.
    """
    defs = schema.pop("$defs", {})

    def _resolve(obj: Any) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_name = obj["$ref"].split("/")[-1]
                return _resolve(defs[ref_name])
            return {k: _resolve(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_resolve(item) for item in obj]
        return obj

    return _resolve(schema)


def agent_findings_schema() -> dict[str, Any]:
    """Return the AgentFindings JSON schema with $refs inlined."""
    return _dereference_schema(AgentFindings.model_json_schema())


class Result:
    def __init__(self, agent_messages: list[Message], agent_result: AgentFindings):
        self.passed = agent_result.passed
        self.details = agent_result.details
        self.steps = agent_result.steps
        self.verification_command = agent_result.verification_command
        self.messages = agent_messages
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"{self.__class__.__name__}(passed={self.passed}, details='{self.details}', timestamp={self.timestamp})"
