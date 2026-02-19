"""Docker entrypoint for running Agent inside container.

This script runs inside the Docker container and manages the Agent's
interaction loop, reading prompts from stdin and writing responses to stdout
using a JSON protocol.
"""

import asyncio
import json
import os
import sys
from pathlib import Path


async def main() -> None:
    """Run the Agent inside Docker container.

    Reads JSON prompts from stdin, executes Agent.think_act_observe(),
    and writes JSON responses to stdout.
    """
    # Add src to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    try:
        from orchestrator import Agent
    except ImportError as e:
        error_response = {
            "type": "error",
            "message": f"Failed to import Agent: {str(e)}",
        }
        print(json.dumps(error_response))
        sys.exit(1)

    # Get configuration from environment
    ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    model = os.getenv("AGENTCEPTION_MODEL", "llama3.2")

    try:
        # Initialize Agent
        agent = Agent(model=model, ollama_host=ollama_host)

        # Write ready signal
        ready_response = {
            "type": "status",
            "status": "ready",
            "model": model,
            "ollama_host": ollama_host,
        }
        print(json.dumps(ready_response), flush=True)

        # Main interaction loop
        while True:
            try:
                # Read prompt from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                # Parse JSON prompt
                try:
                    request = json.loads(line.strip())
                except json.JSONDecodeError as e:
                    error_response = {
                        "type": "error",
                        "message": f"Invalid JSON: {str(e)}",
                    }
                    print(json.dumps(error_response), flush=True)
                    continue

                # Handle different request types
                request_type = request.get("type", "prompt")

                if request_type == "prompt":
                    prompt = request.get("content", "")
                    if not prompt:
                        error_response = {
                            "type": "error",
                            "message": "Empty prompt",
                        }
                        print(json.dumps(error_response), flush=True)
                        continue

                    # Execute orchestration loop
                    try:
                        response = await agent.think_act_observe(prompt)

                        # Send response
                        response_obj = {
                            "type": "response",
                            "content": response,
                        }
                        print(json.dumps(response_obj), flush=True)

                    except Exception as e:
                        error_response = {
                            "type": "error",
                            "message": f"Orchestration failed: {str(e)}",
                        }
                        print(json.dumps(error_response), flush=True)

                elif request_type == "reset":
                    # Reset message history
                    agent.reset()
                    status_response = {
                        "type": "status",
                        "status": "reset",
                    }
                    print(json.dumps(status_response), flush=True)

                elif request_type == "exit":
                    # Graceful exit
                    exit_response = {
                        "type": "status",
                        "status": "exiting",
                    }
                    print(json.dumps(exit_response), flush=True)
                    break

                else:
                    error_response = {
                        "type": "error",
                        "message": f"Unknown request type: {request_type}",
                    }
                    print(json.dumps(error_response), flush=True)

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                exit_response = {
                    "type": "status",
                    "status": "interrupted",
                }
                print(json.dumps(exit_response), flush=True)
                break

    except Exception as e:
        error_response = {
            "type": "error",
            "message": f"Container initialization failed: {str(e)}",
        }
        print(json.dumps(error_response), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
