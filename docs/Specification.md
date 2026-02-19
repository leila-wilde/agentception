# Agentception: offline CLI agent specification

## 1. System architecture

### User interface:

- **CLI mode**: a loop-based terminal interface using `Rich` for formatting.
- **GUI mode (future)**: a web-based or desktop frontend (React/Tailwind or Electron) communicating via a local FastAPI server.
- **The brain (LLM**): Ollama running locally. Supports Tool Calling.
- **The orchestrator**: python logic that manages the "Think-Act-Observe" loop.
- **The sandbox**: Docker (Development/High-Security mode) or a restricted local Python virtual environment (general use mode).

## 2. Toolset (capabilities)

### Core file & system tools

- `read_file(path)`: Returns string content. Uses `pathlib`.
- `write_file(path, content)`: Creates/overwrites files.
- `execute_command(cmd)`: Runs shell commands (Linux/bash in container, Shell on host).
- `list_files(path)`: Directory listing.

### Assistant capabilities

- `web_search(query)`: local SearxNG or lightweight scraper.
- `get_system_info()`: CPU/RAM/Process monitoring.
- manage_notes(action, content): persistent storage in `notes.json`.
- `browser_control(action, url)`: headless browsing via Playwright.

## 3. Distribution & UI (the "app" layer)

- **Packaging**: use `Poetry` or `pip` for dependency management. Package as a standalone executable using `PyInstaller` so users don't need Python installed.
- **CLI entry point**: create a global command (e.g., `agentception chat`) using the `Typer` library.
- **GUI bridge**:
    - Implement a **FastAPI** layer within the orchestrator.
    - This allows a separate GUI (Desktop/Web) to send prompts and receive formatted "thoughts" and "tool results" via WebSockets.

## 4. Security design

- **containment**: default to Docker for file-system manipulation.
- **approval flow**: mandatory user confirmation for `execute_command` and `web_search`.
- **connectivity**: connects to Ollama via `host.docker.internal` or local Unix sockets.

## 5. State management

- **short-term memory**: message history buffer.
- **long-term context**: a `config.json` file in the user's home directory (`~/.agentception/config.json`) for persistent preferences.