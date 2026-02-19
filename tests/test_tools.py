"""Unit tests for core tool implementations."""

import asyncio
from pathlib import Path
import pytest
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools import read_file, write_file, list_files, execute_command, _validate_path


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
