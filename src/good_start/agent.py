from claude_agent_sdk import ClaudeAgentOptions, query

from good_start.loader import Prompt, load_prompt
from good_start.result import Result


class Agent:
    def __init__(self, prompt: Prompt | None = None) -> None:
        self.prompt = prompt or load_prompt()
        self.messages = []

    async def run(self, prompt: str | Prompt | None = None) -> str:
        ## -- if note, set to internal agent's prompt
        if prompt is None:
            prompt = self.prompt

        ## -- if prompt is a Prompt object, render it
        if isinstance(prompt, Prompt):
            prompt = prompt.render()

        async def main():
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    allowed_tools=["Bash", "Glob", "Grep", "Read"],
                    output_format={
                        "type": "json_schema",
                        "schema": Result.model_json_schema(),
                    },
                ),
            ):
                self.messages.append(message)

        await main()
        return "complete"
