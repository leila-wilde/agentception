# Copilot Instructions for Agentception

This file provides guidance for AI agents working on the agentception project—a self-hosted, offline CLI AI orchestrator built in Python.

## High-Level Architecture

**Agentception** is a multi-component system:

1. **Orchestrator** (core): Python logic implementing the "Think-Act-Observe" loop. Receives user prompts, sends them to the LLM, parses tool calls, executes them, and returns results to the LLM.
2. **LLM Backend**: Ollama running locally, supporting tool calling.
3. **CLI Interface**: Rich-formatted terminal UI (entry point via Typer commands like `agentception chat`).
4. **Tool Layer**: Core tools (read/write files, execute shell commands, list directories) + assistant tools (web search, system monitoring, note management, browser control).
5. **Sandbox**: Docker container (default, high-security) or restricted Python venv for tool execution.
6. **Future GUI**: FastAPI server bridge for web/desktop frontends communicating via WebSockets.

For complete technical requirements, see `docs/Specification.md`.

## Code Style & Conventions

### Naming
- **Variables/functions**: `snake_case` (PEP 8)
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Tool names**: Descriptive and explicit (e.g., `execute_shell_command`, not `run_cmd`)

### Mandatory Standards
- **Type hints**: All function signatures must include type hints
- **Path handling**: Always use `pathlib.Path` for cross-platform compatibility (especially Docker)
- **Error handling**: Wrap all tool execution in try-except blocks that return string error messages to the LLM (never crash the orchestrator)
- **Async code**: Use `asyncio` for the Think-Act-Observe loop and FastAPI bridge for non-blocking updates

### Modules & Imports
- Prefer standard library first, then well-maintained FOSS libraries
- Key dependencies (from spec): Rich (CLI formatting), Typer (CLI entry), FastAPI (bridge server), Playwright (browser), Ollama SDK

## Build & Development

The project structure is still being developed. When implementing:

1. **Dependency management**: Use Poetry or pip with a `requirements.txt` or `pyproject.toml`
2. **Entry point**: Create global CLI command via Typer (e.g., `agentception chat`)
3. **Packaging**: Plan for PyInstaller distribution (executable, no Python required)

### Testing
- **Unit tests**: Place in `tests/` directory. Mock Ollama API responses when testing orchestrator logic.
- **Focus**: Verify tool security (e.g., path escaping in `write_file`), decision logic, and orchestrator loop
- **Integration**: Test full loop with known prompts, verify file system changes in sandbox

### Running Tests (when implemented)
```bash
pytest tests/
pytest tests/test_specific.py::TestClass::test_method  # single test
```

## Git Workflow

Follow **Conventional Commits** from `COPILOT.md`:

```
<type>(<scope>): <subject>

<body>

*commit co-authored-by Copilot as part of a 'vibe-coding' educational project*
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code changes (no feature or fix)
- `style`: Formatting/linting
- `test`: Test additions
- `chore`: Build, dependencies, config

### Discipline
- Commit only working features (no broken intermediate states)
- One logical change per commit
- Reference issues if applicable (e.g., "Fixes #5")
- All session work is documented in `SESSION.md`

## Documentation

- **Project specs**: `docs/Specification.md`
- **AI collaboration protocol**: `COPILOT.md` (coding standards, workflow, session logging)
- **This file**: Implementation guidance for Copilot sessions
- **Session log**: `SESSION.md` — all prompts timestamped and attributed

## Key Project Context

This is an **educational project** (MiniVibes challenge) with:
- Strict time constraints (rapid delivery)
- Limited tokens (prefer mini models, one premium request available)
- Focus on vibe coding (effective AI-human collaboration)
- Transparent prompting (all interactions logged in `SESSION.md`)

## Security Considerations

- **Default to Docker** for file operations
- **Mandatory user approval** for `execute_command` and `web_search` tools
- **Path safety**: Validate all file paths to prevent escape from workspace
- **Ollama connectivity**: Use `host.docker.internal` for Docker-to-host communication

## MCP Servers (Optional)

For enhanced development workflows, consider configuring these MCP servers:

- **Filesystem MCP**: Navigate and understand the project structure, read specifications, review test coverage
- **Docker MCP**: Inspect container configs, verify sandbox isolation, debug container connectivity
- **Bash MCP**: Run development commands (tests, linting, builds) when the project reaches that phase
