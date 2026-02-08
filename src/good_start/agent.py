from collections.abc import Callable

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    ToolUseBlock,
    query,
)

from good_start.loader import Prompt, load_prompt
from good_start.result import AgentFindings, Result


class Agent:
    def __init__(
        self,
        prompt: Prompt | None = None,
        permission_mode: str | None = None,
    ) -> None:
        self.prompt = prompt or load_prompt()
        self.permission_mode = permission_mode
        self.messages = []

    async def run(
        self,
        prompt: str | Prompt | None = None,
        on_tool_use: Callable[[str, dict], None] | None = None,
    ) -> Result:
        ## -- if not set, use internal agent's prompt
        if prompt is None:
            prompt = self.prompt

        ## -- if prompt is a Prompt object, render it
        if isinstance(prompt, Prompt):
            prompt = prompt.render()

        query_error = None
        try:
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    allowed_tools=["Bash", "Glob", "Grep", "Read"],
                    permission_mode=self.permission_mode,  # ty: ignore[invalid-argument-type]
                    output_format={
                        "type": "json_schema",
                        "schema": AgentFindings.model_json_schema(),
                    },
                ),
            ):
                self.messages.append(message)
                if on_tool_use and isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            on_tool_use(block.name, block.input)
        except Exception as exc:
            query_error = exc

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
            error_detail = (
                f"Agent error: {query_error}"
                if query_error
                else "Agent did not produce structured output. "
                "It may have encountered an error or hit a limit."
            )
            agent_result = AgentFindings(
                passed=False,
                details=error_detail,
            )

        ## -- create final test result object
        test_result = Result(agent_messages=self.messages, agent_result=agent_result)

        return test_result
