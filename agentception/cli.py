"""Agentception: CLI AI orchestrator entry point."""

import typer

app = typer.Typer(
    help="Agentception - A self-hosted, offline AI orchestrator"
)


@app.command()
def chat() -> None:
    """Start an interactive chat session with the AI agent."""
    typer.echo("Chat mode - Coming soon!")


@app.command()
def version() -> None:
    """Display version information."""
    typer.echo("agentception 0.1.0")


if __name__ == "__main__":
    app()
