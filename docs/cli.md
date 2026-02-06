# CLI

The `good-start` command-line interface is the quickest way to test your project's documentation.

## Usage

Run `good-start check` from your project root:

```sh
# Let the agent find the getting-started docs automatically
good-start check .

# Point it at a specific file
good-start check README.md
good-start check docs/GETTING_STARTED.md
```

The output is a color-coded pass/fail panel with the agent's findings.

## Exit codes

The CLI returns structured exit codes for use in scripts and CI:

- `0` — the agent completed the instructions successfully
- `1` — the agent encountered issues following the instructions

## Saving output

Write the results to a file:

```sh
good-start check . > report.txt
```

## Help

```sh
good-start --help
good-start check --help
```
