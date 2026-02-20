"""Core tool implementations for the Agentception orchestrator.

This module provides asynchronous file operations, command execution,
system info reporting, note management, and web search — all confined
to the /home/agentuser/workspace directory where applicable.
"""

import asyncio
import json
import platform
import shutil
from datetime import datetime, timezone
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


async def get_system_info() -> str:
    """Report container stats: disk usage, memory, and OS version.

    Returns:
        Formatted string with system information.
    """
    try:
        # Disk usage
        disk_root = WORKSPACE_ROOT if WORKSPACE_ROOT.exists() else Path("/")
        disk = shutil.disk_usage(disk_root)
        disk_total_gb = disk.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_free_gb = disk.free / (1024 ** 3)
        disk_percent = (disk.used / disk.total) * 100

        # Memory from /proc/meminfo (Linux container)
        mem_total_kb = 0
        mem_available_kb = 0
        proc_meminfo = Path("/proc/meminfo")
        if proc_meminfo.exists():
            for line in proc_meminfo.read_text().splitlines():
                if line.startswith("MemTotal:"):
                    mem_total_kb = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available_kb = int(line.split()[1])

        mem_used_kb = mem_total_kb - mem_available_kb
        mem_total_gb = mem_total_kb / (1024 ** 2)
        mem_used_gb = mem_used_kb / (1024 ** 2)
        mem_percent = (mem_used_kb / mem_total_kb * 100) if mem_total_kb > 0 else 0.0

        uname = platform.uname()
        return (
            f"System Information:\n"
            f"  OS: {uname.system} {uname.release}\n"
            f"  Machine: {uname.machine}\n"
            f"  Python: {platform.python_version()}\n"
            f"  Disk ({disk_root}): {disk_used_gb:.1f}GB / {disk_total_gb:.1f}GB "
            f"({disk_percent:.1f}% used, {disk_free_gb:.1f}GB free)\n"
            f"  Memory: {mem_used_gb:.1f}GB / {mem_total_gb:.1f}GB ({mem_percent:.1f}% used)\n"
        )
    except Exception as e:
        return f"Error getting system info: {str(e)}"


async def manage_notes(action: str, content: str = "") -> str:
    """Read, append, or clear persistent notes stored in the workspace.

    Notes are stored as JSON in notes.json inside the workspace root,
    providing simple long-term memory for the agent across resets.

    Args:
        action: Operation to perform — 'read', 'append', or 'clear'.
        content: Note text to save (required when action is 'append').

    Returns:
        Note listing (on 'read'), confirmation (on 'append'/'clear'), or error.
    """
    notes_path = WORKSPACE_ROOT / "notes.json"
    loop = asyncio.get_event_loop()

    try:
        notes: list[dict[str, str]] = []
        if notes_path.exists():
            raw = await loop.run_in_executor(None, notes_path.read_text)
            notes = json.loads(raw).get("notes", [])

        if action == "read":
            if not notes:
                return "No notes found."
            lines = "\n".join(
                f"[{n.get('timestamp', '?')}] {n.get('content', '')}" for n in notes
            )
            return f"Notes ({len(notes)}):\n{lines}"

        elif action == "append":
            if not content:
                return "Error: 'content' is required for action='append'."
            notes.append(
                {"timestamp": datetime.now(timezone.utc).isoformat(), "content": content}
            )
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            await loop.run_in_executor(
                None, notes_path.write_text, json.dumps({"notes": notes}, indent=2)
            )
            return f"Note saved. Total notes: {len(notes)}"

        elif action == "clear":
            await loop.run_in_executor(
                None, notes_path.write_text, json.dumps({"notes": []}, indent=2)
            )
            return "All notes cleared."

        else:
            return f"Error: Unknown action '{action}'. Valid actions: 'read', 'append', 'clear'."

    except json.JSONDecodeError:
        return "Error: notes.json is corrupted. Use action='clear' to reset."
    except Exception as e:
        return f"Error managing notes: {str(e)}"


async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for information about a topic or question.

    Stub implementation — structured for future integration with SearxNG.
    To enable real search, set the SEARXNG_URL environment variable and
    replace the stub body with an aiohttp request to the SearxNG JSON API.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return. Defaults to 5.

    Returns:
        JSON-formatted search results string.
    """
    # Future integration point:
    # import os, aiohttp
    # searxng_url = os.getenv("SEARXNG_URL")
    # if searxng_url:
    #     async with aiohttp.ClientSession() as session:
    #         params = {"q": query, "format": "json", "num_results": max_results}
    #         async with session.get(f"{searxng_url}/search", params=params) as resp:
    #             data = await resp.json()
    #             return json.dumps(data.get("results", [])[:max_results], indent=2)

    stub_results = [
        {
            "title": f"[Stub] Result for: {query}",
            "url": f"https://example.com/?q={query.replace(' ', '+')}",
            "snippet": (
                "Web search is currently stubbed. "
                "Set SEARXNG_URL to enable real results via SearxNG."
            ),
            "source": "stub",
        }
    ]
    return json.dumps(
        {
            "query": query,
            "results": stub_results[:max_results],
            "note": "[STUB] Real web search requires SearxNG integration.",
        },
        indent=2,
    )


async def execute_command(cmd: str, timeout: int | str | None = 30) -> str:
    """Execute a shell command and return its output.
    
    Args:
        cmd: The shell command to execute.
        timeout: Maximum execution time in seconds. Can be int, string "XXs", or None.
                 Defaults to 30.
        
    Returns:
        Combined stdout and stderr output from the command.
        
    Raises:
        TimeoutError: If command execution exceeds timeout.
        RuntimeError: If command fails or cannot be executed.
    """
    try:
        # Parse timeout if it's a string (e.g., "10s")
        timeout_seconds = 30
        if timeout is not None:
            if isinstance(timeout, str):
                timeout_str = timeout.strip().lower()
                if timeout_str.endswith('s'):
                    timeout_seconds = int(timeout_str[:-1])
                else:
                    timeout_seconds = int(timeout_str)
            else:
                timeout_seconds = int(timeout)
        
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
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout_seconds} seconds")
        
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
