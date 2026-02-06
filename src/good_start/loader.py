from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import frontmatter
from jinja2 import BaseLoader, Environment

DEFAULT_PROMPT_PATH = Path(__file__).parent / "prompt.md"

_jinja_env = Environment(loader=BaseLoader(), keep_trailing_newline=True)


@dataclass
class Prompt:
    text: str
    metadata: dict[str, object] = field(default_factory=dict)

    def render(self, **kwargs: object) -> str:
        template = _jinja_env.from_string(self.text)
        return template.render(**kwargs)


def load_prompt(path: str | Path = DEFAULT_PROMPT_PATH) -> Prompt:
    post = frontmatter.load(str(path))
    return Prompt(text=post.content, metadata=dict(post.metadata))
