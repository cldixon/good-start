import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query

PROMPT = """
"Follow the project's README instructions on how to get started.
Return 'Good start!' if you are able to successfully follow the instructions.
Otherwise, return 'Bad start!'"
"""


async def main():
    async for message in query(
        prompt=PROMPT,
        options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"]),
    ):
        if hasattr(message, "result"):
            print(message.result)


if __name__ == "__main__":
    asyncio.run(main())
