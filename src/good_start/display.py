"""Shared formatting for real-time tool event display."""

from __future__ import annotations

from rich.console import Console

_TOOL_PREFIXES = {
    "Bash": "$",
    "Read": ">",
    "Grep": "?",
    "Glob": "*",
}

# Internal SDK events that shouldn't be displayed as tool actions.
_HIDDEN_TOOLS = {"StructuredOutput"}


def format_tool_event(tool_name: str, tool_input: dict) -> str:
    """Return a short, human-readable string for a tool invocation."""
    prefix = _TOOL_PREFIXES.get(tool_name, "#")

    if tool_name == "Bash":
        return f"{prefix} {tool_input.get('command', '')}"
    elif tool_name == "Read":
        return f"{prefix} {tool_input.get('file_path', '')}"
    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", ".")
        return f"{prefix} grep {pattern!r} {path}"
    elif tool_name == "Glob":
        return f"{prefix} {tool_input.get('pattern', '')}"
    else:
        return f"{prefix} {tool_name} {tool_input}"


def print_tool_event(tool_name: str, tool_input: dict, console: Console) -> None:
    """Print a formatted tool event to the console."""
    if tool_name in _HIDDEN_TOOLS:
        return
    line = format_tool_event(tool_name, tool_input)
    console.print(f"  [dim]{line}[/dim]")
