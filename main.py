import asyncio

from good_start.agent import Agent


async def main():
    agent = Agent()
    await agent.run()
    return agent.messages


if __name__ == "__main__":
    final_result = asyncio.run(main())
    print(final_result)
