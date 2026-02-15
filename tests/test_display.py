from good_start.display import format_tool_event


class TestFormatToolEvent:
    def test_bash_command(self):
        result = format_tool_event("Bash", {"command": "pip install good-start"})
        assert result == "$ pip install good-start"

    def test_read_file(self):
        result = format_tool_event("Read", {"file_path": "README.md"})
        assert result == "> README.md"

    def test_grep_pattern(self):
        result = format_tool_event("Grep", {"pattern": "install", "path": "."})
        assert result == "? grep 'install' ."

    def test_glob_pattern(self):
        result = format_tool_event("Glob", {"pattern": "*.md"})
        assert result == "* *.md"

    def test_unknown_tool(self):
        result = format_tool_event("CustomTool", {"arg": "value"})
        assert result.startswith("# CustomTool")
