"""Orchestrator for the Agentception AI agent.

Implements the Think-Act-Observe loop by coordinating LLM reasoning
with tool execution and response handling.
"""

import asyncio
import inspect
import json
import re
from typing import Any, Awaitable, Callable, Optional
from pathlib import Path

from ollama import AsyncClient


# Import tools
import sys
sys.path.insert(0, str(Path(__file__).parent))
from tools import (
    read_file,
    write_file,
    list_files,
    execute_command,
    get_system_info,
    manage_notes,
    web_search,
)


class Agent:
    """Coordinates the Think-Act-Observe loop with Ollama LLM."""

    def __init__(
        self,
        model: str = "llama3.2",
        ollama_host: str = "http://localhost:11434",
        workspace_path: Optional[Path] = None,
    ) -> None:
        """Initialize the Agent with Ollama configuration.

        Args:
            model: Model name for Ollama. Defaults to "llama3.2".
            ollama_host: Ollama server URL. Defaults to localhost.
            workspace_path: Path to workspace directory for context loading.
                            Defaults to /home/agentuser/workspace.
        """
        self.model = model
        self.ollama_host = ollama_host
        self.client = AsyncClient(host=ollama_host)
        self.workspace_path = workspace_path or Path("/home/agentuser/workspace")

        # Available tools mapping
        self.tools: dict[str, Callable] = {
            "read_file": read_file,
            "write_file": write_file,
            "list_files": list_files,
            "execute_command": execute_command,
            "get_system_info": get_system_info,
            "manage_notes": manage_notes,
            "web_search": web_search,
        }

        # Message history — optionally seeded with persistent system context
        self.message_history: list[dict[str, Any]] = []
        self._load_system_context()

    def _load_system_context(self) -> None:
        """Load system_context.txt from workspace as a system message.

        If the file exists and has content, it is prepended to message history
        as a system role message, giving the agent a persistent personality or
        standing instructions across sessions.
        """
        context_file = self.workspace_path / "system_context.txt"
        try:
            if context_file.exists():
                system_context = context_file.read_text().strip()
                if system_context:
                    self.message_history.append(
                        {"role": "system", "content": system_context}
                    )
        except Exception:
            pass  # Silently skip unreadable context file

    def _get_tool_schema(self, func: Callable) -> dict[str, Any]:
        """Convert a Python function to Ollama tool schema format.

        Args:
            func: The function to convert.

        Returns:
            JSON schema dict compatible with Ollama tool-calling API.
        """
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or ""
        
        # Extract description from docstring (first line)
        description = docstring.split("\n")[0] if docstring else "No description"

        # Build parameters schema
        properties: dict[str, dict[str, Any]] = {}
        required_params: list[str] = []

        for param_name, param in sig.parameters.items():
            param_type = param.annotation
            
            # Get type string
            if param_type == str:
                type_str = "string"
            elif param_type == int:
                type_str = "integer"
            elif param_type == float:
                type_str = "number"
            elif param_type == bool:
                type_str = "boolean"
            elif param_type == list or param_type == list[str]:
                type_str = "array"
            else:
                type_str = "string"

            properties[param_name] = {
                "type": type_str,
                "description": f"Parameter {param_name}",
            }

            # Track required parameters (no defaults)
            if param.default == inspect.Parameter.empty:
                required_params.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required_params,
                },
            },
        }

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Get schemas for all available tools.

        Returns:
            List of tool schemas for Ollama tool-calling API.
        """
        return [self._get_tool_schema(func) for func in self.tools.values()]

    def _parse_tool_call(self, response_text: str) -> Optional[tuple[str, dict[str, Any]]]:
        """Parse LLM response to extract tool call if present.

        Ollama tool-calling responses contain tool invocations in a specific format.
        This method identifies and parses those invocations.

        Args:
            response_text: The LLM response text.

        Returns:
            Tuple of (tool_name, arguments_dict) if tool call found, else None.
        """
        # Look for tool invocation markers
        # Ollama typically formats tool calls as:
        # [TOOL_CALL] function_name(args_json) [/TOOL_CALL]
        # or in newer versions uses structured format
        
        if not response_text:
            return None

        # Check for common tool call patterns
        if "[TOOL_CALL]" in response_text:
            # Extract tool call block
            try:
                start = response_text.index("[TOOL_CALL]") + len("[TOOL_CALL]")
                end = response_text.index("[/TOOL_CALL]")
                tool_call_text = response_text[start:end].strip()

                # Parse format: function_name(json_args)
                if "(" in tool_call_text and ")" in tool_call_text:
                    paren_start = tool_call_text.index("(")
                    paren_end = tool_call_text.rindex(")")
                    
                    tool_name = tool_call_text[:paren_start].strip()
                    args_json_str = tool_call_text[paren_start + 1 : paren_end]
                    
                    args = json.loads(args_json_str)
                    return (tool_name, args)
            except (ValueError, json.JSONDecodeError, KeyError):
                pass

        # Check for JSON-formatted tool calls (alternative format)
        try:
            # Look for JSON object with tool_use structure
            if "tool_use" in response_text.lower() or "tool_call" in response_text.lower():
                # Try to extract JSON from response
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                json_str = response_text[json_start:json_end]
                
                data = json.loads(json_str)
                if "name" in data and "arguments" in data:
                    return (data["name"], data["arguments"])
        except (ValueError, json.JSONDecodeError, KeyError):
            pass

        return None

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Dictionary of arguments for the tool.

        Returns:
            String result of tool execution (or error message).
        """
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"

        try:
            tool_func = self.tools[tool_name]
            result = await tool_func(**arguments)
            return str(result)
        except TypeError as e:
            return f"Error: Invalid arguments for '{tool_name}': {str(e)}"
        except Exception as e:
            return f"Error executing '{tool_name}': {str(e)}"

    async def think_act_observe(
        self,
        user_prompt: str,
        approval_callback: Optional[Callable[[str], Awaitable[bool]]] = None,
        event_callback: Optional[Callable[[dict[str, Any]], Awaitable[None]]] = None,
    ) -> str:
        """Execute one iteration of the Think-Act-Observe loop.

        Args:
            user_prompt: The user's input/instruction.
            approval_callback: Optional async callable invoked before execute_command.
                               Receives the command string, returns True to allow.
            event_callback: Optional async callable fired for intermediate events:
                            thinking (LLM reasoning text), tool_call, tool_output.

        Returns:
            Final response to the user.
        """
        # THINK: Add user message to history
        self.message_history.append({
            "role": "user",
            "content": user_prompt,
        })

        while True:
            # THINK: Get LLM response with tool availability
            try:
                response = await self.client.chat(
                    model=self.model,
                    messages=self.message_history,
                    tools=self.get_tools_schema(),
                )
            except Exception as e:
                return f"Error communicating with Ollama: {str(e)}"

            response_text = response.get("message", {}).get("content", "")

            # Add assistant response to history
            self.message_history.append({
                "role": "assistant",
                "content": response_text,
            })

            # ACT: Check if LLM requested a tool call
            tool_call = self._parse_tool_call(response_text)

            if not tool_call:
                # No tool call — LLM has produced its final answer
                return response_text

            tool_name, arguments = tool_call

            # Emit reasoning text as a "thinking" event — strip tool call markers first
            if event_callback is not None:
                thinking_text = re.sub(
                    r"\[TOOL_CALL\].*?\[/TOOL_CALL\]", "", response_text, flags=re.DOTALL
                ).strip()
                if thinking_text:
                    await event_callback({"type": "thinking", "content": thinking_text})

            # APPROVAL: Gate execute_command behind an optional approval callback
            if tool_name == "execute_command" and approval_callback is not None:
                cmd = arguments.get("cmd", "")
                approved = await approval_callback(cmd)
                if not approved:
                    tool_result = "Command execution denied by user."
                    self.message_history.append({
                        "role": "user",
                        "content": f"Tool '{tool_name}' result: {tool_result}",
                    })
                    continue  # Let LLM react to the denial

            # Emit tool_call event before execution
            if event_callback is not None:
                await event_callback({"type": "tool_call", "tool": tool_name, "args": arguments})

            # ACT: Execute the requested tool
            tool_result = await self.execute_tool(tool_name, arguments)

            # Emit tool_output event after execution
            if event_callback is not None:
                await event_callback({"type": "tool_output", "tool": tool_name, "content": tool_result})

            # OBSERVE: Add tool result back to history for LLM context
            self.message_history.append({
                "role": "user",
                "content": f"Tool '{tool_name}' result: {tool_result}",
            })

    def reset(self) -> None:
        """Clear message history for a new conversation."""
        self.message_history = []
