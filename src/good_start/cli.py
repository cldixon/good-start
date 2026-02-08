import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from good_start.loader import load_prompt
from good_start.runtime import resolve_runtime

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
    no_container: bool = typer.Option(
        False,
        "--no-container",
        help="Run the agent directly on the host instead of in a container.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed container build and run output.",
    ),
) -> None:
    """Run the good-start agent against a project's documentation."""
    target_path = Path(target)
    if not target_path.exists():
        console.print(f"[red]Error:[/red] path '{target}' does not exist.")
        raise typer.Exit(code=1)

    prompt = load_prompt()
    rendered = prompt.render(target=target)

    runtime = resolve_runtime(no_container=no_container, verbose=verbose)
    result = asyncio.run(runtime.run(rendered, target))

    # -- build output
    if result.passed:
        status = Text("PASSED", style="bold green")
    else:
        status = Text("FAILED", style="bold red")

    body = Text()
    body.append("Status: ")
    body.append(status)
    body.append(f"\n\n{result.details}")

    if result.verification_command:
        body.append("\n\nVerification: ")
        body.append(Text(result.verification_command, style="dim"))

    panel = Panel(
        body,
        title="good-start",
        subtitle=result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        border_style="green" if result.passed else "red",
    )

    console.print(panel)

    if not result.passed:
        raise typer.Exit(code=1)
