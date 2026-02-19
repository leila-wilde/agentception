# Agentception - Quick Reference

## Launch

```bash
agentception chat                           # Default
agentception chat -m llama2                 # Different model
agentception chat -w /path/to/workspace     # Custom workspace
```

---

## Session Commands

| Command | Effect |
|---------|--------|
| `exit` or Ctrl+C | End session |
| `reset` | Clear history (notes persist) |
| Any text | Send to agent |

---

## Tools (7 total)

| Tool | What | Example |
|------|------|---------|
| **read_file** | Read file | `Read config.json` |
| **write_file** | Create/write file | `Create hello.txt with "Hi"` |
| **list_files** | List directory | `What's in my workspace?` |
| **execute_command** | Run shell command | `Run: python script.py` |
| **get_system_info** | OS/disk/memory stats | `What are the container stats?` |
| **manage_notes** | Save/read persistent notes | `Save a note: remember X` |
| **web_search** | Web search (stub) | `Search for Python tips` |

**Security:** `execute_command` requires your approval before running. Review each command carefully.

---

## Common Tasks

```
Create & run script:
  You: Create script.py with [code]
  You: Run: python script.py

Project setup:
  You: List files
  You: Create docs/ and src/ directories
  You: Create README.md

Multi-step chain:
  You: Check system stats, save as note, write summary
  (Agent chains: get_system_info → manage_notes → write_file)

Notes & memory:
  You: Save a note: my preferences
  You: Show my notes
  You: reset  (clears chat, notes stay)
```

---

## Approval Flow ⚠️

When agent needs to run a command:
```
┌─ ⚠ Approval Required ─────────────────┐
│ Command: rm -f ./old_files/*          │
└───────────────────────────────────────┘
Allow this command? [y/n]:
```

- **Yes (`y`)**: Run command, show results
- **No (`n`)**: Deny command, agent reacts gracefully

---

## Workspace & Files

- **Default location:** `/home/agentuser/workspace` (in container)
- **Custom:** Use `--workspace` flag
- **Security:** All paths jailed — can't access files outside workspace
- **Notes:** Saved in `notes.json` — survives `reset`
- **Context:** `system_context.txt` loads at startup (optional)

---

## Limits & Features

| ❌ Cannot | ✅ Can |
|----------|--------|
| Access files outside workspace | Read/write within workspace |
| Make external requests (unless SearxNG) | Run shell commands (with approval) |
| Install packages | Report system stats |
| | Store persistent notes |
| | Take a custom personality |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Agent won't start | `docker ps` (Docker running?) |
| Can't reach Ollama | `ollama serve` (start Ollama) |
| Model not found | `ollama pull llama3.2` |
| Memory full | Use smaller model or `reset` |

---

## Environment

| Key | Value |
|-----|-------|
| Workspace | `/home/agentuser/workspace` |
| Ollama | `http://localhost:11434` |
| Docker Image | `agentception:dev` |
| Python | 3.11 |
| Default Model | `llama3.2` |

---

**Full manual:** `docs/USER_MANUAL.md`
