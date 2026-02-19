# Agentception - User Manual

Welcome to **Agentception**, a self-hosted, offline AI orchestrator that runs inside a Docker container. This manual explains how to launch the agent and use all available commands and tools.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation & Setup](#installation--setup)
3. [Launching the Agent](#launching-the-agent)
4. [Chat Commands](#chat-commands)
5. [Available Tools](#available-tools)
6. [Workspace & File Operations](#workspace--file-operations)
7. [Persistent Memory & Personality](#persistent-memory--personality)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

Agentception is a **Python-based AI agent** that runs inside a Docker container for safety and isolation. The agent can:
- Read and write files
- Execute shell commands
- Report container system stats (disk, memory, OS)
- Store persistent notes that survive conversation resets
- Search the web (stub — requires SearxNG for real results)
- Maintain conversation history across multiple messages
- Take on a custom personality via a `system_context.txt` file

**Requirements:**
- Docker (running)
- Ollama (running locally on port 11434)
- Python 3.11+
- 2GB+ RAM available

---

## Installation & Setup

### 1. Install Agentception

```bash
# Clone or navigate to the repository
cd /home/nyxx/Projects/agentception

# Activate the virtual environment
source .venv/bin/activate

# Install in development mode
pip install -e .
```

### 2. Start Ollama (separate terminal)

```bash
ollama serve
```

The agent expects Ollama to be available at `http://localhost:11434` (or via Docker bridge at `http://host.docker.internal:11434`).

### 3. Build the Docker Image

```bash
docker build -t agentception:dev .
```

This creates a Docker image with Python 3.11, curl, git, and a sandboxed workspace at `/home/agentuser/workspace`.

---

## Launching the Agent

### Basic Chat Session

Start an interactive conversation with the agent:

```bash
agentception chat
```

**What happens:**
1. A Docker container starts with the Agent inside
2. You see a welcome panel with the model name
3. You can type messages and the agent responds
4. Container is automatically cleaned up when you exit

### Advanced Options

```bash
# Specify a different model (must exist in Ollama)
agentception chat --model llama3.2

# Specify Ollama server location (if not local)
agentception chat --ollama-host http://my-ollama-server:11434

# Specify a custom workspace directory
agentception chat --workspace /path/to/custom/workspace
```

### Shorthand Commands

```bash
# Same as --model
agentception chat -m llama3.2

# Same as --workspace
agentception chat -w /path/to/workspace
```

### Example Session

```bash
$ agentception chat

┌─ Chat Session ─────────────────────────────────┐
│ Agentception Agent                              │
│ Model: llama3.2                                 │
│ Type 'exit' or Ctrl+C to quit, 'reset' to      │
│ clear history                                   │
└────────────────────────────────────────────────┘

You: Hello! What files are in my workspace?

Agent:
┌─ Agent ─────────────────────────────────────────┐
│ Let me check your workspace files...             │
│ [file listing result from agent]                │
└────────────────────────────────────────────────┘

You: Create a file called test.txt with "Hello World"

Agent:
┌─ Agent ─────────────────────────────────────────┐
│ File created successfully at test.txt            │
└────────────────────────────────────────────────┘

You: exit
[Session interrupted - container cleaned up]
```

---

## Chat Commands

While in a chat session, you can use these special commands:

### `exit` or `Ctrl+C`
Ends the chat session and exits the program. The container is automatically cleaned up.

```bash
You: exit
[dim]Goodbye![/dim]
```

### `reset`
Clears the agent's message history. The agent will forget the current conversation but tools remain available.

```bash
You: reset
[yellow]Message history cleared.[/yellow]
```

This is useful if:
- The conversation becomes too long (context window limits)
- You want to start a fresh task
- The agent is stuck or confused

### Regular Messages
Any other input is sent to the agent as a prompt. The agent reads it, may call tools, and responds.

---

## Available Tools

The agent has access to **7 tools** inside the Docker container:

### 1. **read_file(path: str) → str**
Read the contents of a file.

**Example:**
```
You: Read the file called config.json
Agent: [reads file and displays content]
```
- `path`: Relative or absolute path to the file (workspace only)

---

### 2. **write_file(path: str, content: str) → str**
Create or overwrite a file with content.

**Example:**
```
You: Create a file named notes.md with the text "# My Notes"
Agent: [creates file and confirms]
```
- `path`: Path for the new file
- `content`: Text to write
- Parent directories are created automatically

---

### 3. **list_files(path: str = ".") → str**
List files and directories in a path.

**Example:**
```
You: What's in my workspace?
Agent: [lists all files and directories]
```
- `path` (optional): Directory to list — defaults to workspace root

---

### 4. **execute_command(command: str) → str**
Execute a shell command and return its output.

**Example:**
```
You: Run: python script.py
Agent: [executes command, shows stdout + stderr]
```
- `command`: Shell command (can include pipes, redirects)
- Runs inside the container — **Security:** Docker sandbox limits blast radius

---

### 5. **get_system_info() → str**
Report container stats: disk usage, memory, and OS version.

**Example:**
```
You: What are the container stats?
Agent:
  OS: Linux 5.15.0 / x86_64
  Python: 3.11.9
  Disk: 4.2GB / 20.0GB (21.0% used, 15.8GB free)
  Memory: 1.2GB / 8.0GB (15.0% used)
```
- No parameters required
- Disk measured at the workspace mount point
- Memory read from `/proc/meminfo`

---

### 6. **manage_notes(action: str, content: str = "") → str**
Read, append, or clear persistent notes stored as `notes.json` in the workspace.

Notes **survive `reset`** — they're written to disk, not held in memory.

**Example:**
```
You: Save a note: prefer async functions for all I/O
Agent: Note saved. Total notes: 1

You: Show my notes
Agent: Notes (1):
  [2026-02-19T22:00:00Z] prefer async functions for all I/O

You: Clear all notes
Agent: All notes cleared.
```

| `action` | Effect |
|----------|--------|
| `read` | Return all saved notes with timestamps |
| `append` | Save a new note (requires `content`) |
| `clear` | Delete all notes |

- Notes persist until the workspace is wiped (not cleared by `reset`)
- Great for: preferences, reminders, facts the agent should remember

---

### 7. **web_search(query: str, max_results: int = 5) → str**
Search the web for a topic. **Currently a stub** — structured for SearxNG integration.

**Example:**
```
You: Search for Python asyncio best practices
Agent: {
  "query": "Python asyncio best practices",
  "results": [{"title": "...", "url": "...", "snippet": "..."}],
  "note": "[STUB] Real web search requires SearxNG integration."
}
```

**Enabling real search with SearxNG:**
```bash
# Run SearxNG locally:
docker run -d -p 8080:8080 searxng/searxng

# Launch agent with SearxNG URL:
SEARXNG_URL=http://localhost:8080 agentception chat
```

---

## Workspace & File Operations

### Workspace Root
All file operations are **confined to the workspace directory**:
- **Default location (in container):** `/home/agentuser/workspace`
- **Custom location:** Use `--workspace` flag when launching

### File Safety
The agent **cannot access files outside the workspace**. Path escape attempts are blocked:

```bash
# These will be rejected by the agent:
You: Read /etc/passwd          # Outside workspace
You: Write to ../../secrets.txt # Escaping workspace
```

### Workspace Structure

When you launch the agent, you get a clean workspace:

```
/home/agentuser/workspace/
├── (empty or your custom files)
└── [your files will appear here]
```

### Examples

**Example 1: Create and read a config file**
```
You: Create a config.json file with {"name": "Agentception", "version": "0.1.0"}

Agent: [creates file]

You: Read config.json

Agent: [displays file contents]
```

**Example 2: Run a Python script**
```
You: Create a script.py that prints "Hello from Python"

Agent: [creates file with script]

You: Run the script using Python

Agent: [executes: python script.py]
```

**Example 3: List and organize files**
```
You: What files do I have?

Agent: [lists all files]

You: Create a docs/ folder and move README.md into it

Agent: [creates folder and moves file]
```

---

## Persistent Memory & Personality

### Notes — Long-Term Memory

The agent can store notes that survive `reset` commands. Notes are written to `notes.json` in the workspace:

```
You: Save a note: always use pathlib.Path for file operations
You: Save a note: user prefers concise answers

# After reset:
You: reset
[yellow]Message history cleared.[/yellow]

You: What are my notes?
Agent: Notes (2):
  [2026-02-19T21:00:00Z] always use pathlib.Path for file operations
  [2026-02-19T21:01:00Z] user prefers concise answers
```

Notes are cleared when the container exits — they live in the workspace volume, not in a database.

### system_context.txt — Persistent Personality

Create a file called `system_context.txt` in the workspace **before** launching the agent. Its contents will be injected as a system-level instruction every time the Agent starts.

**Example — give the agent a custom persona:**
```bash
# Create the context file in your workspace
echo "You are Aria, a concise and helpful coding assistant.
You prefer Python, always use type hints, and keep answers short.
When given a task, always check what files exist first." \
  > /path/to/workspace/system_context.txt

# Launch the agent — it will automatically load the context
agentception chat --workspace /path/to/workspace
```

**What it's good for:**
- Persistent tone/personality
- Standing instructions (e.g., "always summarize your plan before acting")
- Domain priming (e.g., "this is a Flask web app using PostgreSQL")
- Preferred coding style or language rules

**Notes:**
- The file is loaded once at agent startup
- An empty or missing file is silently ignored
- `reset` clears the conversation but the system context message is NOT removed
- The file is plain text — no special format required

---

## Troubleshooting

### Agent won't start
**Error:** `Error: Agent container failed to start`

**Solutions:**
1. Ensure Docker is running: `docker ps`
2. Rebuild the image: `docker build -t agentception:dev .`
3. Check Docker disk space: `docker system df`

### Can't connect to Ollama
**Error:** `Failed to connect to Ollama at http://host.docker.internal:11434`

**Solutions:**
1. Ensure Ollama is running: `ollama serve` (in another terminal)
2. Check Ollama is listening: `curl http://localhost:11434`
3. Specify custom Ollama host: `agentception chat --ollama-host http://my-server:11434`
4. If not using Docker on Linux, adjust host address

### Model not found
**Error:** `Model llama3.2 not found`

**Solutions:**
1. Pull the model: `ollama pull llama3.2`
2. List available models: `ollama list`
3. Use an available model: `agentception chat --model llama2`

### Container runs out of memory
**Error:** `Docker container killed (OOMKilled)`

**Solutions:**
1. Increase Docker memory limit in Docker Desktop settings
2. Use a smaller model
3. Reset history with `reset` command during session

### File operations fail
**Error:** `Path 'X' escapes workspace root`

**Solutions:**
1. Use relative paths (e.g., `config.json` instead of `/etc/config.json`)
2. Verify files are in workspace: `list_files`
3. Create directories first if needed

### Commands not executing
**Issue:** `execute_command` returns no output

**Solutions:**
1. Verify command syntax
2. Check if tools/executables exist in container
3. Use full paths: `/usr/bin/python` instead of `python`
4. Check command permissions

---

## Advanced Usage

### Working with Projects

```bash
# Start the agent with a custom workspace
agentception chat --workspace /path/to/my/project

# Inside the session:
You: List all files
You: Create a build script
You: Run the build
You: Check results
```

### Switching Models

During a session, you can't change models, but you can:

```bash
# Exit current session
You: exit

# Start new session with different model
agentception chat --model llama2
```

### Long Conversations

If the agent starts forgetting context:

```bash
You: reset     # Clear history
# Continue with summary or new task
```

---

## Getting Help

```bash
# Show available commands
agentception --help

# Show version
agentception version

# Show help for chat command
agentception chat --help
```

---

## Performance Tips

1. **Choose the right model:** Smaller models (like llama2) are faster but less capable
2. **Clear history:** Use `reset` if conversation gets long (notes survive reset)
3. **Prime the agent:** Use `system_context.txt` for standing instructions instead of repeating them
4. **Batch operations:** Group related tasks together
5. **Use specific prompts:** Clear instructions = better results

---

## Security Notes

🔒 **Sandboxing:** The agent runs inside a Docker container, isolating it from your host system.

🔒 **Workspace Jailing:** All file operations are confined to the workspace directory.

🔒 **No Network Access:** The agent cannot make external network requests by default (web search is a stub unless SearxNG is configured).

⚠️ **Caution:** Commands executed via `execute_command` can still cause damage within the container. Use carefully.

---

## What's Next?

Now that you know how to launch and use Agentception, try these tasks:

- Create a project structure
- Write and run scripts
- Process data files
- Build and test applications
- Automate repetitive tasks

The agent's real power comes from combining these tools with natural language reasoning. Tell it what you want to accomplish, and it will figure out the steps!

---

**Made with ❤️ as part of the MiniVibes educational challenge**
