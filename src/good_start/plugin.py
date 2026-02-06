"""Pytest plugin for good-start documentation testing."""

from __future__ import annotations

import asyncio

import pytest

from good_start.loader import load_prompt
from good_start.result import Result
from good_start.runtime import resolve_runtime

_result_key = pytest.StashKey[Result]()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("good-start", "Good Start documentation testing")
    group.addoption(
        "--good-start-target",
        action="store",
        default=None,
        help="Default target path for good-start tests (default: '.').",
    )
    group.addoption(
        "--good-start-prompt",
        action="store",
        default=None,
        help="Path to a custom prompt template file.",
    )
    group.addoption(
        "--good-start-no-container",
        action="store_true",
        default=False,
        help="Run the good-start agent locally instead of in a container.",
    )
    parser.addini(
        "good_start_target",
        help="Default target path for good-start tests.",
        default=".",
    )
    parser.addini(
        "good_start_prompt",
        help="Path to a custom prompt template file.",
        default=None,
    )
    parser.addini(
        "good_start_no_container",
        help="Run the good-start agent locally instead of in a container.",
        type="bool",
        default=False,
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "good_start(target, prompt): configure good-start agent for this test. "
        "'target' sets the documentation path; 'prompt' sets a custom prompt file.",
    )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "good_start" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.good_start)


@pytest.fixture()
def good_start(request: pytest.FixtureRequest):
    """Factory fixture that runs the good-start agent and returns a Result.

    Usage:
        def test_docs(good_start):
            result = good_start()           # agent finds docs automatically
            result = good_start("README.md") # or check a specific file
            assert result.passed, result.details
    """
    config = request.config

    def _run(target: str | None = None, prompt_path: str | None = None) -> Result:
        # -- resolve target via precedence chain
        if target is None:
            marker = request.node.get_closest_marker("good_start")
            if marker and marker.kwargs.get("target"):
                target = marker.kwargs["target"]
            elif config.getoption("good_start_target"):
                target = config.getoption("good_start_target")
            else:
                target = config.getini("good_start_target") or "."

        # -- resolve prompt path via precedence chain
        if prompt_path is None:
            marker = request.node.get_closest_marker("good_start")
            if marker and marker.kwargs.get("prompt"):
                prompt_path = marker.kwargs["prompt"]
            elif config.getoption("good_start_prompt"):
                prompt_path = config.getoption("good_start_prompt")
            else:
                ini_val = config.getini("good_start_prompt")
                if ini_val:
                    prompt_path = ini_val

        # -- load and render prompt
        if prompt_path:
            prompt = load_prompt(prompt_path)
        else:
            prompt = load_prompt()

        rendered = prompt.render(target=target)

        # -- resolve runtime mode
        no_container = config.getoption("good_start_no_container") or config.getini(
            "good_start_no_container"
        )
        runtime = resolve_runtime(no_container=no_container)

        # -- run agent
        result = asyncio.run(runtime.run(rendered, target))

        # -- stash result for report hook
        request.node.stash[_result_key] = result
        return result

    return _run


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        result = item.stash.get(_result_key, None)
        if result is not None:
            extra = f"\n\n--- good-start agent details ---\n{result.details}\n"
            if report.longrepr:
                report.longrepr = str(report.longrepr) + extra
