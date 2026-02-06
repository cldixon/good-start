from datetime import datetime

from claude_agent_sdk import Message
from pydantic import BaseModel, Field


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


class Result:
    def __init__(self, agent_messages: list[Message], agent_result: AgentFindings):
        self.passed = agent_result.passed
        self.details = agent_result.details
        self.messages = agent_messages
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"{self.__class__.__name__}(passed={self.passed}, details='{self.details}', timestamp={self.timestamp})"
