"""Agentception: CLI AI orchestrator entry point."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from container import ContainerManager, ContainerConfig

app = typer.Typer(
    help="Agentception - A self-hosted, offline AI orchestrator"
)
console = Console()


async def chat_loop(
    container: ContainerManager,
    model: str,
) -> None:
    """Run interactive chat loop with container.

    Args:
        container: Initialized ContainerManager instance.
        model: Model name (for display).
    """
    console.print(
        Panel(
            f"[bold cyan]Agentception Agent[/bold cyan]\n"
            f"Model: [green]{model}[/green]\n"
            f"Type [bold]'exit'[/bold] or Ctrl+C to quit  •  [bold]'reset'[/bold] to clear history",
            title="[bold]Chat Session[/bold]",
            border_style="cyan",
        )
    )

    try:
        while True:
            # Get user input
            user_input = Prompt.ask("\n[bold green]You[/bold green]").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                console.print("[dim]Goodbye![/dim]")
                break

            if user_input.lower() == "reset":
                await container.send_prompt(json.dumps({"type": "reset"}))
                async for response in container.receive_response():
                    if response.get("type") == "status":
                        console.print("[yellow]↺ Message history cleared.[/yellow]")
                    break
                continue

            # Send prompt to container
            try:
                await container.send_prompt(
                    json.dumps({"type": "prompt", "content": user_input})
                )
            except Exception as e:
                console.print(f"[red]Error sending prompt: {str(e)}[/red]")
                break

            # Receive and display response — loop re-enters after approval requests
            done = False
            while not done:
                approval_pending: Optional[str] = None

                with console.status(
                    "[bold yellow]Agent is thinking...[/bold yellow]",
                    spinner="dots",
                ):
                    try:
                        async for event in container.receive_response():
                            event_type = event.get("type", "")

                            if event_type == "thinking":
                                text = event.get("content", "").strip()
                                if text:
                                    console.print(
                                        Panel(
                                            text,
                                            title="[dim]Agent Thoughts[/dim]",
                                            border_style="dim",
                                        )
                                    )

                            elif event_type == "tool_call":
                                tool = event.get("tool", "?")
                                console.print(
                                    f"  [dim]→ Calling [bold]{tool}[/bold]...[/dim]"
                                )

                            elif event_type == "tool_output":
                                tool = event.get("tool", "?")
                                output = event.get("content", "").strip()
                                console.print(
                                    Panel(
                                        output,
                                        title=f"[yellow]Tool Output: {tool}[/yellow]",
                                        border_style="yellow",
                                    )
                                )

                            elif event_type == "approval_request":
                                approval_pending = event.get("command", "")
                                break  # Exit status context to prompt user

                            elif event_type == "response":
                                response_text = event.get("content", "")
                                if response_text:
                                    console.print(
                                        Panel(
                                            Markdown(response_text),
                                            title="[bold cyan]Agent[/bold cyan]",
                                            border_style="cyan",
                                        )
                                    )
                                done = True
                                break

                            elif event_type == "error":
                                console.print(
                                    f"[red]Agent Error: {event.get('message')}[/red]"
                                )
                                done = True
                                break

                    except Exception as e:
                        console.print(f"[red]Error receiving response: {str(e)}[/red]")
                        done = True

                # Handle approval outside the status context (needs user input)
                if approval_pending is not None:
                    console.print(
                        Panel(
                            f"[bold]Command:[/bold] [yellow]{approval_pending}[/yellow]",
                            title="[bold red]⚠ Approval Required[/bold red]",
                            border_style="red",
                        )
                    )
                    approved = Confirm.ask("[bold]Allow this command?[/bold]")
                    msg_type = "approval_granted" if approved else "approval_denied"
                    await container.send_prompt(json.dumps({"type": msg_type}))
                    if not approved:
                        console.print("[yellow]Command denied.[/yellow]")
                    # Continue the outer while loop to keep receiving
                else:
                    done = True  # No approval needed, exit receive loop

    except KeyboardInterrupt:
        console.print("\n[dim]Session interrupted.[/dim]")


@app.command()
def chat(
    model: str = typer.Option(
        "llama3.2",
        "--model",
        "-m",
        help="LLM model to use (must be available in Ollama)",
    ),
    ollama_host: str = typer.Option(
        "http://host.docker.internal:11434",
        "--ollama-host",
        help="Ollama server URL",
    ),
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace path (for file operations)",
    ),
) -> None:
    """Start an interactive chat session with the AI agent inside Docker."""
    try:
        # Create container configuration
        config = ContainerConfig(
            image_name="agentception:dev",
            workspace_path=workspace,
            ollama_host=ollama_host,
            model=model,
        )

        # Create and start container manager
        container = ContainerManager(config)

        console.print("[cyan]Starting Agent container...[/cyan]")
        asyncio.run(container.start())

        # Run chat loop
        asyncio.run(chat_loop(container, model))

    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)
    finally:
        # Clean up container
        try:
            asyncio.run(container.cleanup())
        except Exception as e:
            console.print(f"[yellow]Cleanup warning: {str(e)}[/yellow]")


@app.command()
def version() -> None:
    """Display version information."""
    typer.echo("agentception 0.1.0")


if __name__ == "__main__":
    app()
