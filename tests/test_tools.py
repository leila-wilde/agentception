"""Unit tests for core tool implementations."""

import asyncio
from pathlib import Path
import pytest
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools import (
    read_file,
    write_file,
    list_files,
    execute_command,
    get_system_info,
    manage_notes,
    web_search,
    _validate_path,
)


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing."""
    return tmp_path


class TestPathValidation:
    """Test path validation and jailing."""
    
    def test_validates_path_escape_attempt(self, tmp_path):
        """Ensure paths escaping workspace are rejected."""
        import tools
        original_workspace = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        
        try:
            with pytest.raises(ValueError, match="escapes workspace root"):
                _validate_path("/../../../etc/passwd")
        finally:
            tools.WORKSPACE_ROOT = original_workspace
    
    def test_validates_absolute_path_escape(self, tmp_path):
        """Ensure absolute paths outside workspace are rejected."""
        import tools
        original_workspace = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        
        try:
            with pytest.raises(ValueError, match="escapes workspace root"):
                _validate_path("/etc/passwd")
        finally:
            tools.WORKSPACE_ROOT = original_workspace


class TestReadFile:
    """Test file reading."""
    
    @pytest.mark.asyncio
    async def test_read_file_success(self, tmp_path):
        """Test successful file reading."""
        import tools
        original_workspace = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        
        try:
            test_file = tmp_path / "test.txt"
            test_content = "Hello, World!"
            test_file.write_text(test_content)
            
            result = await read_file("test.txt")
            assert result == test_content
        finally:
            tools.WORKSPACE_ROOT = original_workspace
    
    @pytest.mark.asyncio
    async def test_read_file_not_found(self, tmp_path):
        """Test reading non-existent file."""
        import tools
        original_workspace = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        
        try:
            with pytest.raises(FileNotFoundError):
                await read_file("nonexistent.txt")
        finally:
            tools.WORKSPACE_ROOT = original_workspace


class TestWriteFile:
    """Test file writing."""
    
    @pytest.mark.asyncio
    async def test_write_file_success(self, tmp_path):
        """Test successful file writing."""
        import tools
        original_workspace = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        
        try:
            test_file = "new_file.txt"
            test_content = "New content"
            
            result = await write_file(test_file, test_content)
            
            assert "File written successfully" in result
            assert (tmp_path / test_file).read_text() == test_content
        finally:
            tools.WORKSPACE_ROOT = original_workspace
    
    @pytest.mark.asyncio
    async def test_write_file_creates_dirs(self, tmp_path):
        """Test file writing creates parent directories."""
        import tools
        original_workspace = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        
        try:
            test_file = "subdir/nested/file.txt"
            test_content = "Nested content"
            
            result = await write_file(test_file, test_content)
            
            assert "File written successfully" in result
            assert (tmp_path / test_file).read_text() == test_content
        finally:
            tools.WORKSPACE_ROOT = original_workspace


class TestListFiles:
    """Test directory listing."""
    
    @pytest.mark.asyncio
    async def test_list_files_success(self, tmp_path):
        """Test successful directory listing."""
        import tools
        original_workspace = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        
        try:
            # Create test files
            (tmp_path / "file1.txt").write_text("content1")
            (tmp_path / "file2.txt").write_text("content2")
            (tmp_path / "subdir").mkdir()
            
            result = await list_files(".")
            
            assert "file1.txt" in result
            assert "file2.txt" in result
            assert "subdir" in result
            assert sorted(result) == result
        finally:
            tools.WORKSPACE_ROOT = original_workspace
    
    @pytest.mark.asyncio
    async def test_list_files_not_found(self, tmp_path):
        """Test listing non-existent directory."""
        import tools
        original_workspace = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        
        try:
            with pytest.raises(FileNotFoundError):
                await list_files("nonexistent")
        finally:
            tools.WORKSPACE_ROOT = original_workspace


class TestExecuteCommand:
    """Test command execution."""
    
    @pytest.mark.asyncio
    async def test_execute_command_success(self):
        """Test successful command execution."""
        result = await execute_command("echo 'test output'")
        assert "test output" in result
    
    @pytest.mark.asyncio
    async def test_execute_command_failure(self):
        """Test failed command execution."""
        with pytest.raises(RuntimeError, match="exit code"):
            await execute_command("false")
    
    @pytest.mark.asyncio
    async def test_execute_command_timeout(self):
        """Test command timeout."""
        with pytest.raises(TimeoutError, match="timed out"):
            await execute_command("sleep 10", timeout=1)


class TestGetSystemInfo:
    """Test system information reporting."""

    @pytest.mark.asyncio
    async def test_returns_string(self):
        """Test get_system_info returns a non-empty string."""
        result = await get_system_info()
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_contains_expected_sections(self):
        """Test get_system_info output includes key system sections."""
        result = await get_system_info()
        assert "OS:" in result
        assert "Python:" in result
        assert "Disk" in result
        assert "Memory:" in result


class TestManageNotes:
    """Test persistent note management."""

    @pytest.mark.asyncio
    async def test_read_empty_notes(self, tmp_path):
        """Test reading when no notes exist returns helpful message."""
        import tools
        original = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        try:
            result = await manage_notes("read")
            assert "No notes found" in result
        finally:
            tools.WORKSPACE_ROOT = original

    @pytest.mark.asyncio
    async def test_append_note(self, tmp_path):
        """Test appending a note creates notes.json and returns count."""
        import tools
        original = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        try:
            result = await manage_notes("append", "Remember to water the plants.")
            assert "Note saved" in result
            assert "1" in result
            assert (tmp_path / "notes.json").exists()
        finally:
            tools.WORKSPACE_ROOT = original

    @pytest.mark.asyncio
    async def test_read_after_append(self, tmp_path):
        """Test reading notes returns previously saved content."""
        import tools
        original = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        try:
            await manage_notes("append", "First note")
            await manage_notes("append", "Second note")
            result = await manage_notes("read")
            assert "First note" in result
            assert "Second note" in result
            assert "Notes (2)" in result
        finally:
            tools.WORKSPACE_ROOT = original

    @pytest.mark.asyncio
    async def test_clear_notes(self, tmp_path):
        """Test clearing notes empties the store."""
        import tools
        original = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        try:
            await manage_notes("append", "To be cleared")
            await manage_notes("clear")
            result = await manage_notes("read")
            assert "No notes found" in result
        finally:
            tools.WORKSPACE_ROOT = original

    @pytest.mark.asyncio
    async def test_append_without_content(self, tmp_path):
        """Test appending with empty content returns error."""
        import tools
        original = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        try:
            result = await manage_notes("append", "")
            assert "Error" in result
        finally:
            tools.WORKSPACE_ROOT = original

    @pytest.mark.asyncio
    async def test_unknown_action(self, tmp_path):
        """Test unknown action returns error message."""
        import tools
        original = tools.WORKSPACE_ROOT
        tools.WORKSPACE_ROOT = tmp_path
        try:
            result = await manage_notes("delete")
            assert "Error" in result
            assert "Unknown action" in result
        finally:
            tools.WORKSPACE_ROOT = original


class TestWebSearch:
    """Test web search stub."""

    @pytest.mark.asyncio
    async def test_returns_valid_json(self):
        """Test web_search returns valid JSON string."""
        import json
        result = await web_search("Python asyncio tutorial")
        data = json.loads(result)
        assert "query" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_query_reflected_in_output(self):
        """Test the query is reflected in the response."""
        import json
        query = "best coffee shops in Paris"
        result = await web_search(query)
        data = json.loads(result)
        assert data["query"] == query

    @pytest.mark.asyncio
    async def test_max_results_respected(self):
        """Test max_results limits the result count."""
        import json
        result = await web_search("test query", max_results=1)
        data = json.loads(result)
        assert len(data["results"]) <= 1

    @pytest.mark.asyncio
    async def test_stub_note_present(self):
        """Test stub response includes integration note."""
        import json
        result = await web_search("anything")
        data = json.loads(result)
        assert "note" in data
        assert "STUB" in data["note"].upper() or "stub" in data["note"].lower()
