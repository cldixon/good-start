from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from good_start.result import AgentFindings, Result

IMAGE_NAME = "good-start-agent"
IMAGE_TAG = "latest"
FULL_IMAGE = f"{IMAGE_NAME}:{IMAGE_TAG}"

_CONTAINERFILE = Path(__file__).parent.parent.parent.parent / "Containerfile"

console = Console(stderr=True)


class ContainerRuntime:
    """Runs the agent inside a container (Podman or Docker)."""

    def __init__(self) -> None:
        self._engine = _detect_engine()

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

        console.print(f"[dim]Container starting ({self._engine})...[/dim]")
        console.print("[dim]Agent is working...[/dim]")

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        console.print("[dim]Agent finished. Stopping container...[/dim]")

        if proc.returncode != 0:
            error_details = (
                proc.stderr.strip() or "Container exited with non-zero status."
            )
            findings = AgentFindings(
                passed=False, details=f"Container error: {error_details}"
            )
            return Result(agent_messages=[], agent_result=findings)

        # The entrypoint prints AgentFindings JSON as the last line of stdout
        stdout_lines = proc.stdout.strip().splitlines()
        json_line = stdout_lines[-1] if stdout_lines else "{}"
        findings = AgentFindings.model_validate_json(json_line)

        console.print("[dim]Container stopped.[/dim]")
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

        console.print("[dim]Building agent image (first run)...[/dim]")
        subprocess.run(
            [
                self._engine,
                "build",
                "-t",
                FULL_IMAGE,
                "-f",
                str(_CONTAINERFILE),
                str(_CONTAINERFILE.parent),
            ],
            check=True,
        )
        console.print("[dim]Image built.[/dim]")


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
