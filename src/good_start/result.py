from pydantic import BaseModel, Field


class Result(BaseModel):
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
