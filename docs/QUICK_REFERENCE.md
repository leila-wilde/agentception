# Agentception - Quick Reference Guide

## Launch Commands

```bash
# Basic chat session
agentception chat

# With custom model
agentception chat --model llama2
agentception chat -m llama2

# With custom workspace
agentception chat --workspace /path/to/workspace
agentception chat -w /path/to/workspace

# With custom Ollama server
agentception chat --ollama-host http://my-server:11434

# Show help
agentception --help
agentception chat --help

# Show version
agentception version
```

---

## Chat Session Shortcuts

| Command | Action |
|---------|--------|
| `exit` | End session (Ctrl+C also works) |
| `reset` | Clear conversation history |
| `any text` | Send message to agent |

---

## Available Tools

### Read File
```
You: Read [filename]
```
- Returns: File contents
- Scope: Workspace only

### Write File
```
You: Create a file named [filename] with content: [content]
```
- Returns: Success/error message
- Scope: Workspace only

### List Files
```
You: What files are in my workspace?
```
- Returns: Directory listing with sizes
- Scope: Workspace directory

### Execute Command
```
You: Run [shell command]
```
- Returns: Command output (stdout + stderr)
- Scope: Container environment

### Get System Info
```
You: What are the system stats?
You: How much disk space is left?
```
- Returns: OS version, Python version, disk usage (GB + %), memory usage (GB + %)
- Scope: Container stats only

### Manage Notes *(persistent memory)*
```
You: Save a note: [your text]
You: Show my notes
You: Clear all my notes
```
- Actions: `append` (save), `read` (list all), `clear` (delete all)
- Storage: `notes.json` in workspace — persists across `reset` commands
- Use for: to-do lists, reminders, facts the agent should remember

### Web Search *(stub — SearxNG-ready)*
```
You: Search the web for [topic]
You: Look up [question]
```
- Returns: JSON results (currently simulated — real results need SearxNG)
- To enable: set `SEARXNG_URL` environment variable

---

## Common Tasks

### Create a Python Script
```
You: Create a script called hello.py that prints "Hello World"
You: Run hello.py
```

### Manage Files
```
You: List all files in my workspace
You: Create a directory called data
You: Create a README.md file
You: Read README.md
```

### Run Commands
```
You: Show me the current date
You: What's my current directory?
You: Run this command: ls -la
```

### Check System Status
```
You: What are the container stats?
You: How much disk space do I have left?
You: What OS and Python version are we on?
```

### Use Persistent Notes
```
You: Save a note: buy groceries tomorrow
You: Save a note: the API key is stored in config.json
You: Show all my notes
You: Clear my notes
```

### Personal Assistant Workflows
```
You: I'm your personal assistant agent. Load my context and notes.
You: Remember that I prefer Python over JavaScript for scripting.
You: What did I ask you to remember?
```

### Search the Web *(stub)*
```
You: Search the web for Python best practices
You: Look up SearxNG self-hosted search setup
```

### Project Management
```
You: I'm starting a new project. Set up the basic structure.
You: Create a requirements.txt with these packages: [list]
You: Build and test my project
```

---

## Important Limitations

- ❌ Cannot access files outside workspace
- ❌ Web search returns stubs (requires SearxNG to enable real results)
- ❌ Cannot install arbitrary packages (container is fixed)
- ✅ CAN read/write files within workspace
- ✅ CAN execute shell commands
- ✅ CAN maintain conversation history
- ✅ CAN report disk/memory/OS system stats
- ✅ CAN store persistent notes (survive `reset`)
- ✅ CAN be given a custom personality via `system_context.txt`

---

## Environment Info

| Component | Location/Value |
|-----------|-----------------|
| **Workspace (container)** | `/home/agentuser/workspace` |
| **Workspace (custom)** | Specified via `--workspace` flag |
| **Notes file** | `<workspace>/notes.json` |
| **System context** | `<workspace>/system_context.txt` |
| **Ollama Server** | `http://localhost:11434` (host) |
| **SearxNG (optional)** | `SEARXNG_URL` env var |
| **Docker Image** | `agentception:dev` |
| **Python Version** | 3.11 |
| **Model (default)** | `llama3.2` |

---

## Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| Agent won't start | Ensure Docker is running: `docker ps` |
| Can't connect to Ollama | Start Ollama: `ollama serve` |
| Model not found | Pull model: `ollama pull llama3.2` |
| Out of memory | Use smaller model or `reset` history |
| File not found | Check path: `list_files` first |
| Command not found | Check if tool exists in container |

---

## Model Selection

```bash
# Popular models to try:
agentception chat --model llama2       # Smaller, faster
agentception chat --model llama3.2     # Default, balanced
agentception chat --model mistral      # Larger, slower but more capable
```

Pull new models with:
```bash
ollama pull [model_name]
ollama list  # See available models
```

---

## Tips & Tricks

💡 **Multi-step Tasks:** Break down complex tasks into simple steps  
💡 **Persistent Notes:** Use `manage_notes` to keep reminders across resets  
💡 **Custom Personality:** Create `system_context.txt` in the workspace to give the agent standing instructions  
💡 **File Organization:** Use directories to organize your workspace  
💡 **History Management:** Use `reset` if context gets too long (notes survive reset)  
💡 **Specific Prompts:** Clear instructions = better results  
💡 **Tool Chains:** Combine tools (e.g., create → execute → read results)

---

## Example Session Transcript

```bash
$ agentception chat

You: What's in my workspace?

Agent: [shows empty workspace]

You: Create a Python script that generates random numbers

Agent: [creates script with random number generator]

You: Run the script 5 times

Agent: [executes script, shows 5 sets of random outputs]

You: Save the output to a file called results.txt

Agent: [creates results file with outputs]

You: Show me what's in results.txt

Agent: [reads and displays file contents]

You: exit
Goodbye!
```

---

## Getting Help

```bash
# Full user manual
cat docs/USER_MANUAL.md

# Command reference
agentception --help
agentception chat --help

# Check version
agentception version
```

---

**For detailed information, see [USER_MANUAL.md](./USER_MANUAL.md)**
