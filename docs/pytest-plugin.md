# Pytest Plugin

Good Start ships as a pytest plugin that is automatically available once installed. No configuration or conftest imports needed.

## Basic usage

```python
def test_getting_started(good_start):
    result = good_start()
    assert result.passed, result.details
```

The `good_start` fixture is a callable that runs the agent and returns a `Result` object with:

- `result.passed` -- boolean indicating whether the agent completed the instructions successfully
- `result.details` -- summary of findings, with constructive feedback on failure

## Checking a specific file

```python
def test_quickstart(good_start):
    result = good_start("docs/QUICKSTART.md")
    assert result.passed, result.details
```

## Configuration

Configuration resolves in this order (highest priority first):

1. Direct call arguments: `good_start("SETUP.md")`
2. Marker keyword arguments: `@pytest.mark.good_start(target="SETUP.md")`
3. CLI options: `pytest --good-start-target=SETUP.md`
4. ini options in `pyproject.toml`
5. Default: `"."`

### Marker-based configuration

```python
import pytest

@pytest.mark.good_start(target="INSTALL.md")
def test_install_docs(good_start):
    result = good_start()
    assert result.passed, result.details
```

### Project-wide defaults in pyproject.toml

```toml
[tool.pytest.ini_options]
good_start_target = "docs/GETTING_STARTED.md"
good_start_prompt = "tests/prompts/custom.md"
```

### Custom prompt templates

Supply your own prompt file to tailor the agent's behavior:

```python
def test_with_custom_prompt(good_start):
    result = good_start(prompt_path="tests/prompts/strict.md")
    assert result.passed, result.details
```

## Skipping agent tests

Tests using the `good_start` fixture are automatically marked with `@pytest.mark.good_start`. Skip them during fast iteration:

```sh
pytest -m "not good_start"
```

Or run only the documentation tests:

```sh
pytest -m good_start -v
```

## Failure output

When a test fails, the agent's detailed findings are appended to the pytest failure report, so you get actionable feedback directly in your CI output.
