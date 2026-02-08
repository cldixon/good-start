from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from good_start.display import print_tool_event
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
            f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY', '')}",
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

        # Stream stderr lines in real-time for tool events.
        # Use readline() instead of iterator to avoid read-ahead buffering.
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
                print_tool_event(event["tool"], event["input"], console)
            except (json.JSONDecodeError, KeyError):
                if self._verbose:
                    console.print(f"  [dim]{line}[/dim]")

        assert proc.stdout is not None
        stdout = proc.stdout.read()

        if proc.returncode != 0:
            error_details = stdout.strip() or "Container exited with non-zero status."
            if self._verbose:
                console.print(f"  [dim]{error_details}[/dim]")
            findings = AgentFindings(
                passed=False, details=f"Container error: {error_details}"
            )
            return Result(agent_messages=[], agent_result=findings)

        # The entrypoint prints AgentFindings JSON as the last line of stdout
        stdout_lines = stdout.strip().splitlines()
        json_line = stdout_lines[-1] if stdout_lines else "{}"
        findings = AgentFindings.model_validate_json(json_line)
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
