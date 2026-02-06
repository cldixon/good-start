from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from good_start.loader import Prompt, load_prompt
from good_start.result import AgentFindings, Result


class Agent:
    def __init__(self, prompt: Prompt | None = None) -> None:
        self.prompt = prompt or load_prompt()
        self.messages = []

    async def run(self, prompt: str | Prompt | None = None) -> Result:
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
                        "schema": AgentFindings.model_json_schema(),
                    },
                ),
            ):
                self.messages.append(message)

        await main()

        ## - get result message
        result_message = self.messages[-1] if self.messages else None

        ## -- take structured output result
        if (
            isinstance(result_message, ResultMessage)
            and result_message.structured_output is not None
        ):
            agent_result = AgentFindings.model_validate(
                result_message.structured_output
            )
        else:
            agent_result = AgentFindings(
                passed=False,
                details="Agent did not produce structured output. "
                "It may have encountered an error or hit a limit.",
            )

        ## -- create final test result object
        test_result = Result(agent_messages=self.messages, agent_result=agent_result)

        return test_result
