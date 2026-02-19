# Copilot Instructions for Agentception

This file provides guidance for AI agents working on the agentception project—a self-hosted, offline CLI AI orchestrator built in Python.

**Quick links:** Specification (`docs/Specification.md`) | Workflow (`COPILOT.md`) | Session log (`SESSION.md`)

## Build, Test & Lint Commands

**Dependencies:** Install via Poetry (or use existing `poetry.lock`):
```bash
poetry install                    # Install all dependencies + dev tools
```

**Linting & formatting:**
```bash
ruff check src/ agentception/     # Lint with ruff
black src/ agentception/          # Format code
mypy src/ agentception/           # Type checking
```

**Testing:** (once tests are created in `tests/`)
```bash
pytest                            # Run all tests
pytest tests/test_file.py         # Run single test file
pytest tests/test_file.py::test_func  # Run single test
pytest --cov                      # With coverage report
pytest -k pattern                 # Run tests matching pattern
```

**CLI entry point:**
```bash
agentception chat                 # Start interactive chat
agentception version              # Show version
```

## High-Level Architecture

**Agentception** is a multi-component system:

1. **Orchestrator** (`src/` or `agentception/`): Python logic implementing the "Think-Act-Observe" loop. Receives user prompts, sends them to the LLM, parses tool calls, executes them, and returns results to the LLM.
2. **LLM Backend**: Ollama running locally, supporting tool calling.
3. **CLI Interface** (`agentception/cli.py`): Rich-formatted terminal UI (entry point via Typer commands like `agentception chat`).
4. **Tool Layer** (`src/tools.py`): Core tools (read/write files, execute shell commands, list directories) + assistant tools (web search, system monitoring, note management, browser control).
5. **Sandbox**: Docker container (default, high-security) or restricted Python venv for tool execution.
6. **Future GUI**: FastAPI server bridge for web/desktop frontends communicating via WebSockets.

For complete technical requirements, see `docs/Specification.md`.

## Code Style & Conventions

This project follows **PEP 8** with strict type safety and error handling. See `COPILOT.md` for full details.

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
- **Line length**: 100 characters (see `pyproject.toml`)

### Key Dependencies
From `pyproject.toml`:
- **Rich**: CLI formatting and terminal UI
- **Typer**: CLI command entry points
- **Ollama**: LLM backend SDK
- **FastAPI** (future): Bridge server for GUI mode
- **Playwright** (future): Headless browser control
- **Pydantic**: Data validation and settings

### Development Tools
- **black**: Code formatter (line-length: 100)
- **ruff**: Fast Python linter
- **mypy**: Type checker (disallow_untyped_defs: false)
- **pytest**: Unit testing framework
- **pytest-asyncio**: Async test support

## Build & Development

### Project Structure
```
agentception/
├── agentception/
│   ├── __init__.py
│   └── cli.py              # Typer CLI entry point
├── src/
│   ├── __init__.py
│   └── tools.py            # Core tool implementations
├── tests/                  # Unit tests (to be created)
├── docs/
│   ├── Specification.md    # Technical requirements
│   └── MiniVibesConsigne.md # Project context
├── pyproject.toml          # Poetry config + tool settings
├── Dockerfile              # Sandbox environment
└── .github/
    └── copilot-instructions.md # This file
```

### Dependency Management
Uses **Poetry** for reproducible builds:
```bash
poetry install              # Install from lock file
poetry add <package>        # Add new dependency
poetry add --group dev <pkg> # Add dev dependency
poetry show --tree          # Show dependency tree
```

### Testing Strategy
- **Unit tests**: Place in `tests/` directory. Mock Ollama API responses when testing orchestrator logic.
- **Focus areas**: Verify tool security (e.g., path escaping in `write_file`), decision logic, and orchestrator loop
- **Integration**: Test full loop with known prompts, verify file system changes in sandbox
- Tests are run with `pytest` and should be async-compatible (`pytest-asyncio`)

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

## MCP Servers

An MCP configuration file is available at `.github/mcp-config.json`. Recommended MCP servers for this project:

- **Filesystem MCP**: Navigate project structure, read specifications, review test coverage
- **Bash MCP**: Execute development commands (tests, linting, builds, Poetry workflows)
- **Docker MCP**: Inspect container configs, verify sandbox isolation, debug Ollama connectivity

### Setup Instructions

To configure these servers:

1. Install MCP server implementations:
   ```bash
   npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-bash
   ```

2. Configure your IDE/Copilot client to use `.github/mcp-config.json` as the MCP servers configuration

3. Set the working directory to the project root for consistent paths across tools
