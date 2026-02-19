"""Container management and execution for the Agentception Agent.

Handles Docker container lifecycle, communication protocol, and
host ↔ container message passing for the orchestrated Agent.
"""

import asyncio
import json
import subprocess
import uuid
from typing import AsyncIterator, Optional
from pathlib import Path


class ContainerConfig:
    """Configuration for container execution."""

    def __init__(
        self,
        image_name: str = "agentception:dev",
        workspace_path: Optional[Path] = None,
        ollama_host: str = "http://host.docker.internal:11434",
        model: str = "llama3.2",
    ) -> None:
        """Initialize container configuration.

        Args:
            image_name: Docker image to run (must be built first)
            workspace_path: Host path to mount as workspace (optional)
            ollama_host: Ollama server URL accessible from container
            model: LLM model to use inside container
        """
        self.image_name = image_name
        self.workspace_path = workspace_path or Path.home() / "agentception_workspace"
        self.ollama_host = ollama_host
        self.model = model
        self.container_id = f"agentception-{uuid.uuid4().hex[:8]}"

    def get_docker_args(self) -> list[str]:
        """Get docker run arguments for this configuration.

        Returns:
            List of arguments for docker run command.
        """
        args = [
            "docker",
            "run",
            "--rm",  # Clean up after exit
            "--name",
            self.container_id,
            # Environment
            "-e",
            f"OLLAMA_HOST={self.ollama_host}",
            "-e",
            "PYTHONUNBUFFERED=1",
            "-e",
            f"AGENTCEPTION_MODEL={self.model}",
            # Workspace mount
            "-v",
            f"{self.workspace_path}:/home/agentuser/workspace",
            # Entrypoint
            "-i",  # Interactive stdin
            self.image_name,
        ]
        return args


class ContainerManager:
    """Manages Agent execution inside Docker containers."""

    def __init__(self, config: Optional[ContainerConfig] = None) -> None:
        """Initialize ContainerManager.

        Args:
            config: Container configuration (uses defaults if None)
        """
        self.config = config or ContainerConfig()
        self.process: Optional[subprocess.Popen] = None

    async def start(self) -> None:
        """Start the container and initialize communication.

        Raises:
            RuntimeError: If Docker is not available or container fails to start.
        """
        try:
            args = self.config.get_docker_args()
            
            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Give container time to initialize
            await asyncio.sleep(0.5)
            
            if self.process.returncode is not None:
                raise RuntimeError(
                    f"Container failed to start (exit code: {self.process.returncode})"
                )
        except FileNotFoundError:
            raise RuntimeError("Docker not found. Please install Docker to run the Agent.")
        except Exception as e:
            raise RuntimeError(f"Failed to start container: {str(e)}")

    async def send_prompt(self, prompt: str) -> None:
        """Send a prompt to the container's stdin.

        Args:
            prompt: User input prompt.

        Raises:
            RuntimeError: If container is not running or send fails.
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("Container not running")

        try:
            message = {
                "type": "prompt",
                "content": prompt,
            }
            json_line = json.dumps(message) + "\n"
            self.process.stdin.write(json_line.encode())
            await self.process.stdin.drain()
        except Exception as e:
            raise RuntimeError(f"Failed to send prompt to container: {str(e)}")

    async def receive_response(self) -> AsyncIterator[dict]:
        """Receive responses from container's stdout.

        Yields:
            Response dictionaries from container (streamed line-by-line).

        Raises:
            RuntimeError: If container is not running or receive fails.
        """
        if not self.process or not self.process.stdout:
            raise RuntimeError("Container not running")

        try:
            async for line in self.process.stdout:
                if not line:
                    break
                
                try:
                    data = json.loads(line.decode().strip())
                    yield data
                except json.JSONDecodeError:
                    # Fallback: treat as plain text response
                    yield {
                        "type": "response",
                        "content": line.decode().strip(),
                    }
        except Exception as e:
            raise RuntimeError(f"Failed to receive from container: {str(e)}")

    async def stop(self) -> None:
        """Stop the container gracefully.

        Raises:
            RuntimeError: If stop fails.
        """
        if not self.process:
            return

        try:
            # Close stdin to signal end of input
            if self.process.stdin:
                self.process.stdin.close()
            
            # Wait for process to exit (with timeout)
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # Force kill if graceful shutdown times out
            self.process.kill()
            await self.process.wait()
        except Exception as e:
            raise RuntimeError(f"Failed to stop container: {str(e)}")

    async def cleanup(self) -> None:
        """Clean up container resources.

        Raises:
            RuntimeError: If cleanup fails.
        """
        try:
            await self.stop()
        except Exception as e:
            raise RuntimeError(f"Cleanup failed: {str(e)}")

    async def is_running(self) -> bool:
        """Check if container is still running.

        Returns:
            True if running, False otherwise.
        """
        if not self.process:
            return False
        return self.process.returncode is None

    async def get_error_output(self) -> str:
        """Get stderr output from container.

        Returns:
            Container stderr output if available.
        """
        if not self.process or not self.process.stderr:
            return ""

        try:
            stderr = await self.process.stderr.read()
            return stderr.decode(errors="replace")
        except Exception:
            return ""
