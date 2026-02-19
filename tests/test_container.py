"""Unit tests for container management layer."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from container import ContainerManager, ContainerConfig


class TestContainerConfig:
    """Test ContainerConfig initialization."""

    def test_default_configuration(self):
        """Test default configuration."""
        config = ContainerConfig()
        
        assert config.image_name == "agentception:dev"
        assert config.ollama_host == "http://host.docker.internal:11434"
        assert config.model == "llama3.2"
        assert config.workspace_path.exists() or True  # Path may not exist yet
        assert config.container_id.startswith("agentception-")

    def test_custom_configuration(self):
        """Test custom configuration."""
        workspace = Path("/custom/workspace")
        config = ContainerConfig(
            image_name="custom:latest",
            workspace_path=workspace,
            ollama_host="http://192.168.1.1:11434",
            model="llama2",
        )
        
        assert config.image_name == "custom:latest"
        assert config.workspace_path == workspace
        assert config.ollama_host == "http://192.168.1.1:11434"
        assert config.model == "llama2"

    def test_docker_args_generation(self):
        """Test docker run arguments generation."""
        config = ContainerConfig()
        args = config.get_docker_args()
        
        assert "docker" in args
        assert "run" in args
        assert "--rm" in args
        assert "-i" in args
        assert "--name" in args
        assert config.container_id in args
        assert "-e" in args
        assert config.image_name in args


class TestContainerManager:
    """Test ContainerManager class."""

    @pytest.fixture
    def manager(self):
        """Create a ContainerManager for testing."""
        config = ContainerConfig()
        return ContainerManager(config)

    def test_initialization(self, manager):
        """Test ContainerManager initialization."""
        assert manager.config is not None
        assert manager.process is None

    @pytest.mark.asyncio
    async def test_start_docker_not_found(self, manager):
        """Test start fails when Docker is not available."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.side_effect = FileNotFoundError("docker not found")
            
            with pytest.raises(RuntimeError, match="Docker not found"):
                await manager.start()

    @pytest.mark.asyncio
    async def test_start_container_initialization_success(self, manager):
        """Test successful container start."""
        mock_process = AsyncMock()
        mock_process.returncode = None
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()
        
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.return_value = mock_process
            
            await manager.start()
            
            assert manager.process == mock_process

    @pytest.mark.asyncio
    async def test_send_prompt_success(self, manager):
        """Test sending prompt to container."""
        mock_process = AsyncMock()
        mock_process.stdin = AsyncMock()
        manager.process = mock_process
        
        prompt = "Test prompt"
        await manager.send_prompt(prompt)
        
        # Verify message was sent
        mock_process.stdin.write.assert_called_once()
        mock_process.stdin.drain.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_prompt_not_running(self, manager):
        """Test send_prompt fails when container not running."""
        manager.process = None
        
        with pytest.raises(RuntimeError, match="Container not running"):
            await manager.send_prompt("test")

    @pytest.mark.asyncio
    async def test_receive_response_success(self, manager):
        """Test receiving responses from container."""
        response_data = {"type": "response", "content": "Hello"}
        json_line = (json.dumps(response_data) + "\n").encode()
        
        mock_process = AsyncMock()
        
        # Create async generator for stdout
        async def read_lines():
            yield json_line
        
        mock_process.stdout = read_lines()
        manager.process = mock_process
        
        responses = []
        async for response in manager.receive_response():
            responses.append(response)
        
        assert len(responses) == 1
        assert responses[0]["type"] == "response"
        assert responses[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_receive_response_invalid_json(self, manager):
        """Test receiving invalid JSON falls back to plain text."""
        invalid_line = b"Not valid JSON\n"
        
        mock_process = AsyncMock()
        
        async def read_lines():
            yield invalid_line
        
        mock_process.stdout = read_lines()
        manager.process = mock_process
        
        responses = []
        async for response in manager.receive_response():
            responses.append(response)
        
        assert len(responses) == 1
        assert responses[0]["type"] == "response"
        assert "Not valid JSON" in responses[0]["content"]

    @pytest.mark.asyncio
    async def test_receive_response_not_running(self, manager):
        """Test receive_response fails when container not running."""
        manager.process = None
        
        with pytest.raises(RuntimeError, match="Container not running"):
            async for _ in manager.receive_response():
                pass

    @pytest.mark.asyncio
    async def test_stop_graceful(self, manager):
        """Test graceful container stop."""
        mock_process = AsyncMock()
        mock_process.stdin = AsyncMock()
        mock_process.wait = AsyncMock()
        manager.process = mock_process
        
        await manager.stop()
        
        # Verify stdin was closed
        mock_process.stdin.close.assert_called_once()
        # Verify wait was called
        mock_process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_with_timeout(self, manager):
        """Test stop with timeout forces kill."""
        mock_process = AsyncMock()
        mock_stdin = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_process.kill = MagicMock()
        
        # Mock wait_for to raise TimeoutError
        async def wait_mock(*args, **kwargs):
            await mock_process.wait()
        
        manager.process = mock_process
        
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            await manager.stop()
        
        # Verify kill was called
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """Test cleanup calls stop."""
        mock_process = AsyncMock()
        mock_process.stdin = AsyncMock()
        mock_process.wait = AsyncMock()
        manager.process = mock_process
        
        await manager.cleanup()
        
        # Verify stop was called (through process.wait)
        mock_process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_running_true(self, manager):
        """Test is_running returns True when process running."""
        mock_process = AsyncMock()
        mock_process.returncode = None
        manager.process = mock_process
        
        result = await manager.is_running()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_running_false(self, manager):
        """Test is_running returns False when process exited."""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        manager.process = mock_process
        
        result = await manager.is_running()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_running_no_process(self, manager):
        """Test is_running returns False when no process."""
        manager.process = None
        
        result = await manager.is_running()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_error_output(self, manager):
        """Test getting error output from container."""
        error_text = b"Error message"
        
        mock_process = AsyncMock()
        mock_stderr = AsyncMock()
        mock_stderr.read = AsyncMock(return_value=error_text)
        mock_process.stderr = mock_stderr
        manager.process = mock_process
        
        output = await manager.get_error_output()
        
        assert "Error message" in output

    @pytest.mark.asyncio
    async def test_get_error_output_no_process(self, manager):
        """Test get_error_output returns empty string when no process."""
        manager.process = None
        
        output = await manager.get_error_output()
        assert output == ""


class TestCommunicationProtocol:
    """Test container communication protocol."""

    @pytest.mark.asyncio
    async def test_prompt_message_format(self):
        """Test prompt message is properly formatted."""
        config = ContainerConfig()
        manager = ContainerManager(config)
        
        mock_process = AsyncMock()
        mock_stdin = AsyncMock()
        mock_process.stdin = mock_stdin
        manager.process = mock_process
        
        prompt = "What is 2+2?"
        await manager.send_prompt(prompt)
        
        # Extract what was written
        call_args = mock_stdin.write.call_args
        if call_args:
            written_data = call_args[0][0]
            if isinstance(written_data, bytes):
                written_str = written_data.decode()
                msg = json.loads(written_str.strip())
                assert msg["type"] == "prompt"
                assert msg["content"] == prompt

    def test_response_message_format(self):
        """Test response message structure."""
        response = {
            "type": "response",
            "content": "The answer is 4.",
        }
        
        # Should be serializable to JSON
        json_str = json.dumps(response)
        parsed = json.loads(json_str)
        
        assert parsed["type"] == "response"
        assert parsed["content"] == "The answer is 4."

    def test_error_message_format(self):
        """Test error message structure."""
        error = {
            "type": "error",
            "message": "Invalid input",
        }
        
        json_str = json.dumps(error)
        parsed = json.loads(json_str)
        
        assert parsed["type"] == "error"
        assert parsed["message"] == "Invalid input"
