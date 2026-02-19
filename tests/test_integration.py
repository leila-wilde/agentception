"""Integration tests for the full Agentception tool-chain loop.

These tests exercise the Agent orchestrator with real tool execution
(no Docker, mocked Ollama) to verify multi-step tool chaining works end-to-end.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tools as tools_module
from orchestrator import Agent


def _tool_call(name: str, args: dict) -> dict:
    """Build a mock Ollama response that requests a tool call."""
    args_json = json.dumps(args)
    return {"message": {"content": f"[TOOL_CALL]{name}({args_json})[/TOOL_CALL]"}}


def _final(text: str) -> dict:
    """Build a mock Ollama response with a plain text final answer."""
    return {"message": {"content": text}}


class TestFullToolChain:
    """Integration test: Agent chains multiple tools in a single prompt."""

    @pytest.mark.asyncio
    async def test_system_stats_note_and_summary_file(self, tmp_path):
        """Agent checks system stats, saves them as a note, writes a summary file."""
        responses = [
            _tool_call("get_system_info", {}),
            _tool_call("manage_notes", {"action": "append", "content": "container stats noted"}),
            _tool_call("write_file", {"path": "summary.txt", "content": "System stats summary"}),
            _final("Done! I checked the system stats, saved a note, and created summary.txt."),
        ]
        idx = 0

        async def mock_chat(**kwargs):
            nonlocal idx
            r = responses[idx]; idx += 1; return r

        events: list[dict] = []

        async def capture(event: dict) -> None:
            events.append(event)

        original = tools_module.WORKSPACE_ROOT
        tools_module.WORKSPACE_ROOT = tmp_path
        try:
            with patch("ollama.AsyncClient.chat", side_effect=mock_chat):
                agent = Agent(workspace_path=tmp_path)
                result = await agent.think_act_observe(
                    "Check system stats, save them as a note, then write a summary file.",
                    event_callback=capture,
                )
        finally:
            tools_module.WORKSPACE_ROOT = original

        # Final response is correct
        assert "Done" in result or "summary" in result.lower()

        # notes.json was created and has content
        notes_file = tmp_path / "notes.json"
        assert notes_file.exists(), "notes.json should have been created"
        notes_data = json.loads(notes_file.read_text())
        assert len(notes_data["notes"]) == 1
        assert "container stats noted" in notes_data["notes"][0]["content"]

        # summary.txt was created
        summary_file = tmp_path / "summary.txt"
        assert summary_file.exists(), "summary.txt should have been created"
        assert "summary" in summary_file.read_text().lower()

        # Events were emitted correctly — only tool_call events have a "tool" key
        tool_calls_emitted = [e["tool"] for e in events if e.get("type") == "tool_call"]
        assert "get_system_info" in tool_calls_emitted
        assert "manage_notes" in tool_calls_emitted
        assert "write_file" in tool_calls_emitted

    @pytest.mark.asyncio
    async def test_message_history_reflects_full_chain(self, tmp_path):
        """Each tool result is added to message history for LLM context."""
        responses = [
            _tool_call("list_files", {}),
            _tool_call("write_file", {"path": "hello.txt", "content": "hello"}),
            _final("I listed the files and created hello.txt."),
        ]
        idx = 0

        async def mock_chat(**kwargs):
            nonlocal idx
            r = responses[idx]; idx += 1; return r

        original = tools_module.WORKSPACE_ROOT
        tools_module.WORKSPACE_ROOT = tmp_path
        try:
            with patch("ollama.AsyncClient.chat", side_effect=mock_chat):
                agent = Agent(workspace_path=tmp_path)
                await agent.think_act_observe("List files then create hello.txt.")
        finally:
            tools_module.WORKSPACE_ROOT = original

        # History should contain tool results
        tool_results = [
            m for m in agent.message_history
            if "result:" in m.get("content", "").lower()
        ]
        assert len(tool_results) == 2

    @pytest.mark.asyncio
    async def test_approval_gates_execute_command_in_chain(self, tmp_path):
        """Approval callback is called exactly once per execute_command in a chain."""
        responses = [
            _tool_call("execute_command", {"cmd": "echo hello"}),
            _tool_call("write_file", {"path": "out.txt", "content": "echo output"}),
            _final("All done."),
        ]
        idx = 0

        async def mock_chat(**kwargs):
            nonlocal idx
            r = responses[idx]; idx += 1; return r

        approval_calls: list[str] = []

        async def auto_approve(cmd: str) -> bool:
            approval_calls.append(cmd)
            return True

        original = tools_module.WORKSPACE_ROOT
        tools_module.WORKSPACE_ROOT = tmp_path
        try:
            with patch("ollama.AsyncClient.chat", side_effect=mock_chat):
                agent = Agent(workspace_path=tmp_path)
                result = await agent.think_act_observe(
                    "Run echo then save output.",
                    approval_callback=auto_approve,
                )
        finally:
            tools_module.WORKSPACE_ROOT = original

        assert approval_calls == ["echo hello"]
        assert (tmp_path / "out.txt").exists()
        assert "All done" in result

    @pytest.mark.asyncio
    async def test_system_context_persists_across_tool_calls(self, tmp_path):
        """system_context.txt is loaded once and remains in history throughout chain."""
        (tmp_path / "system_context.txt").write_text("You are a helpful coding assistant.")

        responses = [
            _tool_call("get_system_info", {}),
            _final("Stats gathered."),
        ]
        idx = 0

        async def mock_chat(**kwargs):
            nonlocal idx
            # Verify system message is always first in history
            messages = kwargs.get("messages", [])
            assert messages[0]["role"] == "system"
            assert "helpful coding assistant" in messages[0]["content"]
            r = responses[idx]; idx += 1; return r

        original = tools_module.WORKSPACE_ROOT
        tools_module.WORKSPACE_ROOT = tmp_path
        try:
            with patch("ollama.AsyncClient.chat", side_effect=mock_chat):
                agent = Agent(workspace_path=tmp_path)
                await agent.think_act_observe("Get system info.")
        finally:
            tools_module.WORKSPACE_ROOT = original
