"""Unit tests for the orchestrator Agent class."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestrator import Agent


class TestAgent:
    """Test the Agent orchestrator class."""

    @pytest.fixture
    def agent(self):
        """Create an Agent instance for testing."""
        return Agent(model="llama3.2", ollama_host="http://localhost:11434")

    def test_agent_initialization(self, agent):
        """Test Agent initializes with correct defaults."""
        assert agent.model == "llama3.2"
        assert agent.ollama_host == "http://localhost:11434"
        assert len(agent.tools) == 4
        assert "read_file" in agent.tools
        assert "write_file" in agent.tools
        assert "list_files" in agent.tools
        assert "execute_command" in agent.tools
        assert agent.message_history == []

    def test_agent_custom_initialization(self):
        """Test Agent with custom parameters."""
        agent = Agent(model="llama2", ollama_host="http://192.168.1.1:11434")
        assert agent.model == "llama2"
        assert agent.ollama_host == "http://192.168.1.1:11434"

    def test_get_tool_schema_structure(self, agent):
        """Test tool schema generation."""
        schemas = agent.get_tools_schema()
        
        assert len(schemas) == 4
        
        # Check schema structure
        for schema in schemas:
            assert "type" in schema
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]
            
            params = schema["function"]["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params

    def test_read_file_schema(self, agent):
        """Test read_file tool schema."""
        schemas = agent.get_tools_schema()
        read_file_schema = next(s for s in schemas if s["function"]["name"] == "read_file")
        
        assert "path" in read_file_schema["function"]["parameters"]["properties"]
        assert "path" in read_file_schema["function"]["parameters"]["required"]

    def test_write_file_schema(self, agent):
        """Test write_file tool schema."""
        schemas = agent.get_tools_schema()
        write_file_schema = next(s for s in schemas if s["function"]["name"] == "write_file")
        
        props = write_file_schema["function"]["parameters"]["properties"]
        assert "path" in props
        assert "content" in props
        
        required = write_file_schema["function"]["parameters"]["required"]
        assert "path" in required
        assert "content" in required

    def test_parse_tool_call_with_brackets(self, agent):
        """Test parsing tool call with [TOOL_CALL] markers."""
        response = 'Some text [TOOL_CALL]read_file({"path": "test.txt"}) [/TOOL_CALL] more text'
        
        result = agent._parse_tool_call(response)
        assert result is not None
        tool_name, args = result
        assert tool_name == "read_file"
        assert args == {"path": "test.txt"}

    def test_parse_tool_call_no_call(self, agent):
        """Test parsing response without tool call."""
        response = "This is just a plain response with no tool calls."
        
        result = agent._parse_tool_call(response)
        assert result is None

    def test_parse_tool_call_empty(self, agent):
        """Test parsing empty response."""
        result = agent._parse_tool_call("")
        assert result is None

    def test_parse_tool_call_with_complex_args(self, agent):
        """Test parsing tool call with complex arguments."""
        response = '[TOOL_CALL]write_file({"path": "file.txt", "content": "Hello\\nWorld"}) [/TOOL_CALL]'
        
        result = agent._parse_tool_call(response)
        assert result is not None
        tool_name, args = result
        assert tool_name == "write_file"
        assert args["path"] == "file.txt"
        assert "Hello" in args["content"]

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, agent):
        """Test successful tool execution."""
        # Mock the read_file tool
        agent.tools["read_file"] = AsyncMock(return_value="file content")
        
        result = await agent.execute_tool("read_file", {"path": "test.txt"})
        assert result == "file content"
        agent.tools["read_file"].assert_called_once_with(path="test.txt")

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self, agent):
        """Test execution of unknown tool."""
        result = await agent.execute_tool("nonexistent_tool", {})
        assert "Unknown tool" in result

    @pytest.mark.asyncio
    async def test_execute_tool_invalid_args(self, agent):
        """Test tool execution with invalid arguments."""
        # Create an async mock that raises TypeError on wrong args
        async def mock_read(*args, **kwargs):
            raise TypeError("read_file() got an unexpected keyword argument 'wrong_arg'")
        
        agent.tools["read_file"] = AsyncMock(side_effect=mock_read)
        
        result = await agent.execute_tool("read_file", {"wrong_arg": "value"})
        assert "Invalid arguments" in result

    @pytest.mark.asyncio
    async def test_execute_tool_exception(self, agent):
        """Test tool execution that raises an exception."""
        agent.tools["read_file"] = AsyncMock(side_effect=IOError("File not found"))
        
        result = await agent.execute_tool("read_file", {"path": "test.txt"})
        assert "Error executing" in result
        assert "File not found" in result

    @pytest.mark.asyncio
    async def test_think_act_observe_no_tools(self, agent):
        """Test Think-Act-Observe loop with no tool calls."""
        agent.client.chat = AsyncMock(
            return_value={
                "message": {"content": "Hello, I can help you with that."}
            }
        )
        
        result = await agent.think_act_observe("Hello!")
        assert result == "Hello, I can help you with that."
        assert len(agent.message_history) == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_think_act_observe_with_tool_call(self, agent):
        """Test Think-Act-Observe loop with tool execution."""
        # Mock LLM responses
        responses = [
            {"message": {"content": '[TOOL_CALL]read_file({"path": "test.txt"}) [/TOOL_CALL]'}},
            {"message": {"content": "I read the file successfully."}},
        ]
        agent.client.chat = AsyncMock(side_effect=responses)
        
        # Mock the tool
        agent.tools["read_file"] = AsyncMock(return_value="file content")
        
        result = await agent.think_act_observe("Read test.txt")
        assert result == "I read the file successfully."
        
        # Verify tool was called
        agent.tools["read_file"].assert_called_once_with(path="test.txt")
        
        # Verify history includes tool result
        assert any("file content" in str(msg) for msg in agent.message_history)

    @pytest.mark.asyncio
    async def test_think_act_observe_ollama_error(self, agent):
        """Test Think-Act-Observe loop with Ollama connection error."""
        agent.client.chat = AsyncMock(side_effect=ConnectionError("Cannot connect to Ollama"))
        
        result = await agent.think_act_observe("Hello")
        assert "Error communicating with Ollama" in result

    def test_reset_clears_history(self, agent):
        """Test reset clears message history."""
        agent.message_history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"},
        ]
        
        agent.reset()
        assert agent.message_history == []
