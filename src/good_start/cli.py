import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from good_start.agent import Agent
from good_start.loader import load_prompt

app = typer.Typer(
    name="good-start",
    no_args_is_help=True,
)

console = Console()


@app.callback()
def main():
    """Test whether a codebase's getting-started documentation is accurate and easy to follow."""


@app.command()
def check(
    target: str = typer.Argument(
        default=".",
        help="Path to the getting-started documentation file, or '.' to let the agent find it.",
    ),
) -> None:
    """Run the good-start agent against a project's documentation."""
    target_path = Path(target)
    if not target_path.exists():
        console.print(f"[red]Error:[/red] path '{target}' does not exist.")
        raise typer.Exit(code=1)

    prompt = load_prompt()
    rendered = prompt.render(target=target)

    agent = Agent()
    result = asyncio.run(agent.run(rendered))

    # -- build output
    if result.passed:
        status = Text("PASSED", style="bold green")
    else:
        status = Text("FAILED", style="bold red")

    body = Text()
    body.append("Status: ")
    body.append(status)
    body.append(f"\n\n{result.details}")

    panel = Panel(
        body,
        title="good-start",
        subtitle=result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        border_style="green" if result.passed else "red",
    )

    console.print(panel)

    if not result.passed:
        raise typer.Exit(code=1)
