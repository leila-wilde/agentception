"""Core tool implementations for the Agentception orchestrator.

This module provides asynchronous file operations and command execution,
all strictly confined to the /home/agentuser/workspace directory.
"""

import asyncio
from pathlib import Path
from typing import List


# Workspace jail directory
WORKSPACE_ROOT = Path("/home/agentuser/workspace")


def _validate_path(path: str | Path) -> Path:
    """Validate that a path stays within the workspace root.
    
    Args:
        path: The path to validate (can be relative or absolute).
        
    Returns:
        Resolved Path object within the workspace.
        
    Raises:
        ValueError: If path attempts to escape the workspace.
    """
    if isinstance(path, str):
        path = Path(path)
    
    # Resolve relative paths from workspace root
    if not path.is_absolute():
        resolved = (WORKSPACE_ROOT / path).resolve()
    else:
        resolved = path.resolve()
    
    # Ensure resolved path stays within workspace
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError:
        raise ValueError(
            f"Path '{path}' escapes workspace root at {WORKSPACE_ROOT}"
        )
    
    return resolved


async def read_file(path: str | Path) -> str:
    """Read and return the contents of a file.
    
    Args:
        path: Relative or absolute path to the file within workspace.
        
    Returns:
        File contents as a string.
        
    Raises:
        ValueError: If path escapes workspace.
        FileNotFoundError: If file does not exist.
        IOError: If file cannot be read.
    """
    try:
        file_path = _validate_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise IOError(f"Path is not a file: {file_path}")
        
        # Read file asynchronously
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, file_path.read_text)
        return content
        
    except (ValueError, FileNotFoundError, IOError) as e:
        raise e
    except Exception as e:
        raise IOError(f"Failed to read file: {str(e)}")


async def write_file(path: str | Path, content: str) -> str:
    """Write content to a file, creating directories and file as needed.
    
    Args:
        path: Relative or absolute path to the file within workspace.
        content: The content to write to the file.
        
    Returns:
        Confirmation message with file path.
        
    Raises:
        ValueError: If path escapes workspace.
        IOError: If file cannot be written.
    """
    try:
        file_path = _validate_path(path)
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file asynchronously
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, file_path.write_text, content)
        
        return f"File written successfully: {file_path}"
        
    except ValueError as e:
        raise e
    except Exception as e:
        raise IOError(f"Failed to write file: {str(e)}")


async def list_files(path: str | Path = ".") -> List[str]:
    """List files and directories in a given path.
    
    Args:
        path: Relative or absolute path within workspace. Defaults to workspace root.
        
    Returns:
        List of file/directory names (relative paths) in the directory.
        
    Raises:
        ValueError: If path escapes workspace.
        FileNotFoundError: If directory does not exist.
        IOError: If directory cannot be read.
    """
    try:
        dir_path = _validate_path(path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not dir_path.is_dir():
            raise IOError(f"Path is not a directory: {dir_path}")
        
        # List directory asynchronously
        loop = asyncio.get_event_loop()
        entries = await loop.run_in_executor(
            None,
            lambda: sorted([entry.name for entry in dir_path.iterdir()])
        )
        return entries
        
    except (ValueError, FileNotFoundError, IOError) as e:
        raise e
    except Exception as e:
        raise IOError(f"Failed to list directory: {str(e)}")


async def execute_command(cmd: str, timeout: int | None = 30) -> str:
    """Execute a shell command and return its output.
    
    Args:
        cmd: The shell command to execute.
        timeout: Maximum execution time in seconds. Defaults to 30.
        
    Returns:
        Combined stdout and stderr output from the command.
        
    Raises:
        TimeoutError: If command execution exceeds timeout.
        RuntimeError: If command fails or cannot be executed.
    """
    try:
        # Create subprocess shell task
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Wait for process completion with timeout
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds")
        
        # Decode output
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        
        # Combine output
        output = stdout
        if stderr:
            output += f"\n[stderr]\n{stderr}"
        
        # Check return code
        if process.returncode != 0:
            raise RuntimeError(
                f"Command failed with exit code {process.returncode}:\n{output}"
            )
        
        return output if output else "(no output)"
        
    except (TimeoutError, RuntimeError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {str(e)}")
