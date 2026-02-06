# Examples

A few common ways to use Good Start.

## Quick check during development

Run a one-off check while writing your docs:

```sh
good-start check README.md
```

Review the output, fix any issues, and run it again.

## Add to CI with the CLI

Add a step to your GitHub Actions workflow:

```yaml
- name: Check getting-started docs
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: good-start check .
```

The process exits with code 1 on failure, so your pipeline will catch regressions in your setup instructions.

## Add to your test suite

Use the pytest plugin to make documentation checks part of your regular test runs:

```python
# tests/test_docs.py

def test_readme(good_start):
    result = good_start("README.md")
    assert result.passed, result.details


def test_quickstart_guide(good_start):
    result = good_start("docs/QUICKSTART.md")
    assert result.passed, result.details
```

Run them:

```sh
pytest -m good_start -v
```

Or skip them when you want a fast feedback loop:

```sh
pytest -m "not good_start"
```

## Check multiple docs with markers

Use markers to configure each test independently:

```python
import pytest


@pytest.mark.good_start(target="INSTALL.md")
def test_install_docs(good_start):
    result = good_start()
    assert result.passed, result.details


@pytest.mark.good_start(target="CONTRIBUTING.md")
def test_contributing_docs(good_start):
    result = good_start()
    assert result.passed, result.details
```

## Custom prompt for stricter checks

Write a custom prompt template and pass it in:

```python
def test_strict_check(good_start):
    result = good_start(
        "README.md",
        prompt_path="tests/prompts/strict.md",
    )
    assert result.passed, result.details
```

This lets you tailor the agent's behavior -- for example, requiring that every command exits cleanly, or that specific tools are installed as part of setup.
