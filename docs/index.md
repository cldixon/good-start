# good-start

Test whether a project's getting-started documentation is accurate and easy to follow, using an AI agent.

Good Start reads your project's setup instructions, attempts to follow them step by step, and reports back with a pass/fail result and actionable feedback.

## Installation

Requires Python 3.12+.

```sh
pip install good-start
```

Or with uv:

```sh
uv add good-start
```

## Prerequisites

Good Start uses the Anthropic API under the hood. Set your API key before running:

```sh
export ANTHROPIC_API_KEY=your-key-here
```

## Quick start

Check a project's documentation from the project root:

```sh
good-start check .
```

Or point it at a specific file:

```sh
good-start check README.md
```

See the [CLI guide](cli.md) for more details, or the [pytest plugin](pytest-plugin.md) to integrate into your test suite.
