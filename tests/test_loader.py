from pathlib import Path

import pytest

from good_start.loader import BAD_START, GOOD_START, Prompt, load_prompt


@pytest.fixture()
def prompt_file(tmp_path: Path) -> Path:
    content = """\
---
version: 1.0.0
author: test
---

# Hello

Return {{ good_start }} or {{ bad_start }}.
"""
    p = tmp_path / "prompt.md"
    p.write_text(content)
    return p


@pytest.fixture()
def no_frontmatter_file(tmp_path: Path) -> Path:
    content = "Just a plain prompt with {{ name }}."
    p = tmp_path / "plain.md"
    p.write_text(content)
    return p


class TestLoadPrompt:
    def test_parses_metadata(self, prompt_file: Path):
        prompt = load_prompt(prompt_file)
        assert prompt.metadata["version"] == "1.0.0"
        assert prompt.metadata["author"] == "test"

    def test_parses_text(self, prompt_file: Path):
        prompt = load_prompt(prompt_file)
        assert "# Hello" in prompt.text
        assert "{{ good_start }}" in prompt.text

    def test_text_excludes_frontmatter(self, prompt_file: Path):
        prompt = load_prompt(prompt_file)
        assert "---" not in prompt.text
        assert "version:" not in prompt.text

    def test_no_frontmatter(self, no_frontmatter_file: Path):
        prompt = load_prompt(no_frontmatter_file)
        assert prompt.metadata == {}
        assert "{{ name }}" in prompt.text

    def test_accepts_string_path(self, prompt_file: Path):
        prompt = load_prompt(str(prompt_file))
        assert prompt.metadata["version"] == "1.0.0"


class TestLoadPromptFromProject:
    def test_loads_project_prompt(self):
        path = (
            Path(__file__).resolve().parent.parent / "src" / "good_start" / "prompt.md"
        )
        prompt = load_prompt(path)
        assert prompt.metadata["version"] == "1.0.0"
        assert "{{good_start}}" in prompt.text

    def test_loads_default_prompt(self):
        prompt = load_prompt()
        assert prompt.metadata["version"] == "1.0.0"
        assert "{{good_start}}" in prompt.text


class TestPromptRender:
    def test_renders_variables(self, prompt_file: Path):
        prompt = load_prompt(prompt_file)
        result = prompt.render(good_start=GOOD_START, bad_start=BAD_START)
        assert GOOD_START in result
        assert BAD_START in result
        assert "{{ good_start }}" not in result

    def test_render_leaves_missing_vars_empty(self):
        prompt = Prompt(text="Hello {{ name }}!")
        result = prompt.render()
        assert result == "Hello !"

    def test_render_with_no_placeholders(self):
        prompt = Prompt(text="No placeholders here.")
        result = prompt.render(extra="ignored")
        assert result == "No placeholders here."

    def test_render_jinja_filter(self):
        prompt = Prompt(text="Hello {{ name | upper }}!")
        result = prompt.render(name="world")
        assert result == "Hello WORLD!"

    def test_render_jinja_conditional(self):
        prompt = Prompt(text="{% if verbose %}Details{% else %}Summary{% endif %}")
        assert prompt.render(verbose=True) == "Details"
        assert prompt.render(verbose=False) == "Summary"
