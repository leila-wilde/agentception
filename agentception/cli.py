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
from rich.prompt import Prompt


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
            f"Model: {model}\n"
            f"Type 'exit' or Ctrl+C to quit, 'reset' to clear history",
            title="Chat Session",
        )
    )

    try:
        while True:
            # Get user input
            user_input = Prompt.ask("[bold]You[/bold]").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                console.print("[dim]Goodbye![/dim]")
                break

            if user_input.lower() == "reset":
                # Send reset request to container
                await container.send_prompt(
                    json.dumps({"type": "reset"})
                )
                # Read reset confirmation
                async for response in container.receive_response():
                    if response.get("type") == "status":
                        console.print("[yellow]Message history cleared.[/yellow]")
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

            # Receive and display response
            try:
                response_text = ""
                async for response in container.receive_response():
                    if response.get("type") == "response":
                        response_text = response.get("content", "")
                        break
                    elif response.get("type") == "error":
                        console.print(
                            f"[red]Agent Error: {response.get('message')}[/red]"
                        )
                        break

                if response_text:
                    # Display response with markdown formatting
                    console.print(
                        Panel(
                            Markdown(response_text),
                            title="[bold]Agent[/bold]",
                        )
                    )
            except Exception as e:
                console.print(f"[red]Error receiving response: {str(e)}[/red]")
                break

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
