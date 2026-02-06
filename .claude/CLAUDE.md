# Welcome to Good Start 

A package for testing whether a codebase's documentation on getting started is accurate and easy to follow.

## Planned Interfaces

Currently, we envision the following interfaces and outputs for this tool:

- **CLI**: A command-line interface for running tests and generating reports.
- **pytest plugin**: A clean, canonical function to run as part of a project's `pytest` suite. 
- **Agent Assessment Report**: A comprehensive report describing the agent's experience and assessment of attempting to work through the project's documentation; can be exported to HTML or PDF formats.

### CLI

The initial workflow for the `good-start` tool. Perhaps can be run like this:

```sh
$ good-start check . # if leaving it open for agent to find the getting started documentation
```

or,

```sh
$ good-start check README.md # if the getting started documentation is in a specific file   
```

In the above scenarios, we want the CLI to print out a succinct technical result following the tool's prescribed output. See `/good_start/result`. This output should be informative and actionable, with a nice layout which makes sense in the user's terminal.

This also allows for the user to save the output to a text file:

```sh
$ good-start check . > report.md
```

If the user wants the report returned in an output document:

```sh
$ good-start check . --output report.html # or report.pdf
```

### Pytest Functionality

While the CLI is a great introduction to the tool, and can be helpful during the development of a project's setup instructions, the longer term use of the `good-start` tool is to integrate it into a project's testing suite. This allows for the documentation to be tested automatically as part of the project's continuous integration pipeline.

If during the course of development there is a regression in the getting started steps (e.g., an argument or command has changed, a URL has been updated, etc.), the `good-start` tool can be used to automatically detect and report these changes. This ensures that the documentation remains accurate and up-to-date, and helps to prevent regressions from occurring.

\*\*Note: We will need to design the right interface for the pytest functionality. 


### Agent Assessment Report

**Agent Assessment Report**: A comprehensive report describing the agent's experience and assessment of attempting to work through the project's documentation; can be exported to HTML or PDF formats.

In the above CLI section, we provided some examples of how to generate these reports. But, we will need to develop what these reports provide in addition to the CLI's default terminal output. Additionally, how will these outputs look and for what additional use can they be put to?


## Agent Runtime 

Currently, our agent runs locally on the user's machine. For the initial PoC, this is acceptable. However, in reality this is both complicated and slightly dangerous. The nature of a projec'ts start up documentation usually includes installing and configuring software, either within a project (e.g., via `pip`, `uv`, `npm`, etc.) or on the system itself (e.g., `apt-get`, `brew`, etc.). Additionally, a project might prescribe different instructions for different operating systems or environments. To address these challenges, we will need to develop a more robust agent runtime that can handle these complexities and provide a more seamless experience for users.

We should explore using a sandboxed, containerized environment to run the agent while it is testing and assessing the project's documentation. This will allow us to isolate the agent's environment from the user's machine, preventing any potential conflicts or security issues. Additionally, this approach will enable us to run the agent in a consistent and reproducible environment, regardless of the user's machine configuration.


## Agent Configuration

We will also want to allow for the user to configure the agent. For starters, this can include specifying the model version; though for now we will only support Anthropic models due to API and SDK specific features such as the agent SDK, structured outputs feature, etc.. 

We may also consider allowing the user to configure the tools available to the agent, such as extending to use `WebSearch`, etc.

## Project Guidelines

A few simple guidelines to follow when developing this project:

- we prefer simplicity/minimalism wherever possible
- use `uv` for all tools, python commands, etc. 
- create clear boundaries between project modules
