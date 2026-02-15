from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from rich.console import Console

from good_start.display import format_tool_event
from good_start.result import AgentFindings, Result

IMAGE_NAME = "good-start-agent"
IMAGE_TAG = "latest"
FULL_IMAGE = f"{IMAGE_NAME}:{IMAGE_TAG}"

_CONTAINERFILE = Path(__file__).parent.parent.parent.parent / "Containerfile"

console = Console(stderr=True)


class ContainerRuntime:
    """Runs the agent inside a container (Podman or Docker)."""

    def __init__(self, verbose: bool = False) -> None:
        self._engine = _detect_engine()
        self._verbose = verbose

    async def run(self, prompt: str, target: str) -> Result:
        self._ensure_image()

        api_key = _resolve_api_key()
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. "
                "Export it in your shell or add it to a .env file."
            )

        # Resolve the project directory to mount
        target_path = Path(target).resolve()
        if target_path.is_file():
            mount_dir = target_path.parent
        else:
            mount_dir = target_path

        cmd = [
            self._engine,
            "run",
            "--rm",
            "-v",
            f"{mount_dir}:/workspace:ro",
            "-w",
            "/workspace",
            "-e",
            f"ANTHROPIC_API_KEY={api_key}",
            FULL_IMAGE,
            "--prompt",
            prompt,
            "--target",
            target,
        ]

        console.print(
            f"  [dim]Container started ({self._engine}). Agent is working...[/dim]"
        )

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Drain stdout in a background thread to prevent pipe deadlock.
        # If the container fills the stdout pipe buffer while we're
        # blocking on stderr.readline(), both sides stall.
        stdout_chunks: list[str] = []

        def _drain_stdout() -> None:
            assert proc.stdout is not None
            stdout_chunks.append(proc.stdout.read())

        reader = threading.Thread(target=_drain_stdout, daemon=True)
        reader.start()

        # Stream stderr lines in real-time for tool events.
        assert proc.stderr is not None
        while True:
            line = proc.stderr.readline()
            if not line and proc.poll() is not None:
                break
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                tool_name = event["tool"]
                if tool_name == "StructuredOutput":
                    continue
                text = format_tool_event(tool_name, event["input"])
                sys.stderr.write(f"  {text}\n")
                sys.stderr.flush()
            except (json.JSONDecodeError, KeyError):
                if self._verbose:
                    sys.stderr.write(f"  {line}\n")
                    sys.stderr.flush()

        reader.join()
        stdout = stdout_chunks[0] if stdout_chunks else ""

        # The entrypoint prints AgentFindings JSON as the last line of stdout.
        # Try to parse it regardless of exit code — the entrypoint catches
        # SDK errors and still writes valid JSON before exiting.
        stdout_lines = stdout.strip().splitlines()
        json_line = stdout_lines[-1] if stdout_lines else ""

        if json_line:
            try:
                findings = AgentFindings.model_validate_json(json_line)
                return Result(agent_messages=[], agent_result=findings)
            except Exception:
                pass

        # Fallback: no parseable JSON on stdout
        if proc.returncode == -9:
            detail = "Container was killed (OOM). Try increasing container memory."
        elif proc.returncode != 0:
            detail = f"Container exited with code {proc.returncode}."
        else:
            detail = "Agent did not produce output."

        if self._verbose and stdout.strip():
            console.print(f"  [dim]{stdout.strip()}[/dim]")

        findings = AgentFindings(passed=False, details=detail)
        return Result(agent_messages=[], agent_result=findings)

    def _ensure_image(self) -> None:
        """Build the image if it does not exist locally."""
        result = subprocess.run(
            [self._engine, "image", "inspect", FULL_IMAGE],
            capture_output=True,
        )
        if result.returncode == 0:
            return

        if not _CONTAINERFILE.exists():
            raise FileNotFoundError(
                f"Containerfile not found at {_CONTAINERFILE}. "
                "Cannot build the agent image."
            )

        with console.status(
            "[dim]Building agent image (first run)...[/dim]", spinner="dots"
        ):
            build_result = subprocess.run(
                [
                    self._engine,
                    "build",
                    "-t",
                    FULL_IMAGE,
                    "-f",
                    str(_CONTAINERFILE),
                    str(_CONTAINERFILE.parent),
                ],
                capture_output=True,
                text=True,
            )
            if build_result.returncode != 0:
                raise RuntimeError(f"Image build failed:\n{build_result.stderr}")
            if self._verbose:
                console.print(f"[dim]{build_result.stdout}[/dim]")


def _resolve_api_key() -> str | None:
    """Return the Anthropic API key from the environment or a .env file."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key

    # Fall back to reading a .env file in the current directory.
    env_path = Path.cwd() / ".env"
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()

    return None


def _detect_engine() -> str:
    """Find a container engine, preferring Podman."""
    for candidate in ("podman", "docker"):
        path = shutil.which(candidate)
        if path:
            return candidate
    raise RuntimeError(
        "No container engine found. Install podman or docker, "
        "or use --no-container to run without a container."
    )
