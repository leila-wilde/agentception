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
        assert len(agent.tools) == 7
        assert "read_file" in agent.tools
        assert "write_file" in agent.tools
        assert "list_files" in agent.tools
        assert "execute_command" in agent.tools
        assert "get_system_info" in agent.tools
        assert "manage_notes" in agent.tools
        assert "web_search" in agent.tools

    def test_agent_custom_initialization(self):
        """Test Agent with custom parameters."""
        agent = Agent(model="llama2", ollama_host="http://192.168.1.1:11434")
        assert agent.model == "llama2"
        assert agent.ollama_host == "http://192.168.1.1:11434"

    def test_get_tool_schema_structure(self, agent):
        """Test tool schema generation."""
        schemas = agent.get_tools_schema()
        
        assert len(schemas) == 7
        
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

    def test_loads_system_context_on_init(self, tmp_path):
        """Test Agent loads system_context.txt as first system message."""
        context = "You are a helpful assistant named Aria."
        (tmp_path / "system_context.txt").write_text(context)

        agent = Agent(workspace_path=tmp_path)

        assert len(agent.message_history) == 1
        assert agent.message_history[0]["role"] == "system"
        assert agent.message_history[0]["content"] == context

    def test_ignores_missing_system_context(self, tmp_path):
        """Test Agent starts with empty history when no context file exists."""
        agent = Agent(workspace_path=tmp_path)
        assert agent.message_history == []

    def test_ignores_empty_system_context(self, tmp_path):
        """Test Agent ignores a blank system_context.txt."""
        (tmp_path / "system_context.txt").write_text("   \n  ")
        agent = Agent(workspace_path=tmp_path)
        assert agent.message_history == []

    def test_new_tools_in_schema(self, tmp_path):
        """Test all 7 tools appear in the generated Ollama tool schema."""
        agent = Agent(workspace_path=tmp_path)
        schema = agent.get_tools_schema()
        names = {entry["function"]["name"] for entry in schema}
        assert names == {
            "read_file", "write_file", "list_files", "execute_command",
            "get_system_info", "manage_notes", "web_search",
        }

    @pytest.mark.asyncio
    async def test_approval_callback_called_for_execute_command(self, tmp_path):
        """Test approval_callback is invoked when LLM requests execute_command."""
        responses = [
            {"message": {"content": '[TOOL_CALL]execute_command({"cmd": "echo hi"})[/TOOL_CALL]'}},
            {"message": {"content": "Done."}},
        ]
        idx = 0

        async def mock_chat(**kwargs):
            nonlocal idx
            r = responses[idx]; idx += 1; return r

        approval_calls: list[str] = []

        async def mock_approval(cmd: str) -> bool:
            approval_calls.append(cmd)
            return True

        with patch("ollama.AsyncClient.chat", side_effect=mock_chat):
            agent = Agent(workspace_path=tmp_path)
            result = await agent.think_act_observe("run echo", approval_callback=mock_approval)

        assert approval_calls == ["echo hi"]
        assert "Done" in result

    @pytest.mark.asyncio
    async def test_denied_command_injected_into_history(self, tmp_path):
        """Test that a denied execute_command is noted in history and loop continues."""
        responses = [
            {"message": {"content": '[TOOL_CALL]execute_command({"cmd": "rm -rf /"})[/TOOL_CALL]'}},
            {"message": {"content": "I understand, the command was not allowed."}},
        ]
        idx = 0

        async def mock_chat(**kwargs):
            nonlocal idx
            r = responses[idx]; idx += 1; return r

        async def deny_all(cmd: str) -> bool:
            return False

        with patch("ollama.AsyncClient.chat", side_effect=mock_chat):
            agent = Agent(workspace_path=tmp_path)
            await agent.think_act_observe("delete everything", approval_callback=deny_all)

        denied_in_history = any(
            "denied" in msg.get("content", "").lower()
            for msg in agent.message_history
        )
        assert denied_in_history

    @pytest.mark.asyncio
    async def test_event_callback_fires_for_tool_call_and_output(self, tmp_path):
        """Test event_callback receives tool_call and tool_output events."""
        responses = [
            {"message": {"content": '[TOOL_CALL]get_system_info({})[/TOOL_CALL]'}},
            {"message": {"content": "Stats retrieved."}},
        ]
        idx = 0

        async def mock_chat(**kwargs):
            nonlocal idx
            r = responses[idx]; idx += 1; return r

        events: list[dict] = []

        async def capture(event: dict) -> None:
            events.append(event)

        with patch("ollama.AsyncClient.chat", side_effect=mock_chat):
            agent = Agent(workspace_path=tmp_path)
            await agent.think_act_observe("get stats", event_callback=capture)

        types = [e["type"] for e in events]
        assert "tool_call" in types
        assert "tool_output" in types
        tool_call_event = next(e for e in events if e["type"] == "tool_call")
        assert tool_call_event["tool"] == "get_system_info"
