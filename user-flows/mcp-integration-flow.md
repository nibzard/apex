# MCP Integration Flow

## Purpose
Set up and use APEX's Model Context Protocol (MCP) integration with Claude Code for seamless multi-agent development workflows.

## Prerequisites
- Claude CLI installed and configured
- APEX project created or initialized
- Python environment with APEX dependencies

## MCP Overview

### What is MCP Integration?
APEX provides native MCP tools that allow Claude Code instances to:
- Read/write shared memory (LMDB)
- Coordinate between multiple agents
- Access project status and metadata
- Manage task workflows

### Architecture:
```
Claude Code Instance → MCP Client → APEX MCP Server → LMDB Database
```

## Automatic Setup

### Project Creation with MCP:
When creating a new APEX project, MCP integration is automatically configured:

```bash
uv run apex new my-project
```

**Automatic Setup:**
1. Creates `.mcp.json` configuration file
2. Configures APEX LMDB MCP server
3. Sets environment variables
4. Creates database structure

### Generated `.mcp.json`:
```json
{
  "mcpServers": {
    "lmdb": {
      "command": "python",
      "args": ["-m", "apex.mcp.claude_lmdb_server"],
      "env": {
        "APEX_LMDB_PATH": "./apex.db",
        "APEX_LMDB_MAP_SIZE": "1073741824"
      }
    }
  }
}
```

## Manual MCP Setup

### For Existing Projects:
If `.mcp.json` wasn't created automatically:

1. **Initialize APEX:**
   ```bash
   uv run apex init
   ```

2. **Verify MCP Configuration:**
   ```bash
   ls -la .mcp.json  # Should exist
   ```

3. **Test MCP Server:**
   ```bash
   # Test APEX MCP server manually
   APEX_LMDB_PATH="./apex.db" uv run python -m apex.mcp
   ```

### Custom MCP Configuration:
For advanced setups, modify `.mcp.json`:

```json
{
  "mcpServers": {
    "apex-lmdb": {
      "command": "python",
      "args": ["-m", "apex.mcp"],
      "env": {
        "APEX_LMDB_PATH": "./custom_path/apex.db",
        "APEX_LMDB_MAP_SIZE": "2147483648",
        "APEX_LOG_LEVEL": "debug"
      }
    }
  }
}
```

## Claude Code Integration

### Starting Claude Code:
In your APEX project directory:
```bash
claude
```

**Automatic Loading:**
- Claude Code detects `.mcp.json`
- Connects to APEX MCP server
- APEX tools become available

### Verify MCP Connection:
In Claude Code session:
```
> Can you list the available MCP tools?
```

**Expected APEX Tools:**
- `mcp__lmdb__read`
- `mcp__lmdb__write`
- `mcp__lmdb__list`
- `mcp__lmdb__cursor_scan`
- `mcp__lmdb__delete`
- `mcp__lmdb__watch`
- `mcp__lmdb__project_status`

## Using APEX MCP Tools

### 1. Reading Memory Data:
```
> mcp__lmdb__read /projects/my-project/config
```

**Returns project configuration and status**

### 2. Writing Task Data:
```
> mcp__lmdb__write /projects/my-project/tasks/task1 '{
  "description": "Implement user authentication",
  "assigned_to": "coder",
  "priority": "high",
  "status": "pending"
}'
```

### 3. Listing Memory Keys:
```
> mcp__lmdb__list /projects/my-project/
```

**Returns all keys under the project namespace**

### 4. Scanning Key-Value Pairs:
```
> mcp__lmdb__cursor_scan /tasks/ --limit 10
```

**Returns up to 10 task entries with their data**

### 5. Watching for Changes:
```
> mcp__lmdb__watch /projects/my-project/tasks/ --timeout 30
```

**Monitors for changes to task data in real-time**

### 6. Getting Project Status:
```
> mcp__lmdb__project_status my-project-id
```

**Returns comprehensive project overview**

### 7. Deleting Memory Keys:
```
> mcp__lmdb__delete /projects/my-project/temp/cache
```

## Multi-Agent Workflows

### Setting Up Multiple Claude Instances:

#### Terminal 1 - Supervisor Agent:
```bash
cd my-project
claude --prompt "You are the Supervisor agent for this project. Use APEX MCP tools to coordinate work and assign tasks."
```

#### Terminal 2 - Coder Agent:
```bash
cd my-project
claude --prompt "You are the Coder agent. Check for assigned tasks using APEX MCP tools and implement solutions."
```

#### Terminal 3 - Adversary Agent:
```bash
cd my-project
claude --prompt "You are the Adversary agent. Review code and find issues using APEX MCP tools for coordination."
```

### Agent Coordination Example:

#### Supervisor Creates Tasks:
```
> I need to break down "Create user authentication" into tasks for the team.

> mcp__lmdb__write /projects/proj-123/tasks/auth-1 '{
  "description": "Design user authentication schema",
  "assigned_to": "coder",
  "priority": "high",
  "status": "pending",
  "created_by": "supervisor"
}'

> mcp__lmdb__write /projects/proj-123/tasks/auth-2 '{
  "description": "Review authentication implementation for security",
  "assigned_to": "adversary",
  "priority": "medium",
  "status": "pending",
  "depends_on": ["auth-1"]
}'
```

#### Coder Checks Tasks:
```
> Let me check for my assigned tasks.

> mcp__lmdb__list /projects/proj-123/tasks/

> mcp__lmdb__cursor_scan /projects/proj-123/tasks/
```

#### Adversary Monitors Progress:
```
> Let me see what tasks are completed and ready for review.

> mcp__lmdb__watch /projects/proj-123/tasks/ --timeout 10

> mcp__lmdb__cursor_scan /projects/proj-123/tasks/
```

## Memory Organization

### Standard Memory Structure:
```
/projects/{project_id}/
├── /config                  # Project configuration
├── /tasks/                  # Task management
│   ├── /pending/           # Pending tasks
│   ├── /in_progress/       # Active tasks
│   └── /completed/         # Finished tasks
├── /agents/                 # Agent states
│   ├── /supervisor/        # Supervisor agent data
│   ├── /coder/            # Coder agent data
│   └── /adversary/        # Adversary agent data
├── /memory/                 # Shared memory
│   ├── /code/             # Source code
│   ├── /tests/            # Test suites
│   └── /docs/             # Documentation
└── /sessions/              # Session history
```

### Agent Communication Pattern:
1. **Supervisor** writes tasks to `/tasks/pending/`
2. **Agents** read from their assigned task queues
3. **Agents** update task status as work progresses
4. **Results** stored in `/tasks/completed/` with outputs

## Environment Configuration

### APEX MCP Server Environment:
```bash
# LMDB database location
export APEX_LMDB_PATH="./apex.db"

# Database memory map size (1GB default)
export APEX_LMDB_MAP_SIZE="1073741824"

# Logging level
export APEX_LOG_LEVEL="info"

# Connection timeout
export APEX_MCP_TIMEOUT="30"
```

### Claude Code MCP Configuration:
```json
{
  "mcpServers": {
    "apex-lmdb": {
      "command": "uv",
      "args": ["run", "python", "-m", "apex.mcp"],
      "env": {
        "APEX_LMDB_PATH": "./apex.db"
      }
    }
  }
}
```

## Troubleshooting

### MCP Connection Issues:

**"MCP server not found"**
```bash
# Verify APEX installation
uv run python -m apex.mcp --help

# Check project directory
ls -la .mcp.json
```

**"Database connection failed"**
```bash
# Check database permissions
ls -la apex.db/

# Test manual connection
APEX_LMDB_PATH="./apex.db" uv run python -c "from apex.core.lmdb_mcp import LMDBMCP; db = LMDBMCP('./apex.db'); print('Connected')"
```

**"Tools not available in Claude Code"**
```bash
# Restart Claude Code
claude mcp restart

# Check MCP status
claude mcp list
```

### Performance Issues:

**Slow MCP responses**
- Increase `APEX_LMDB_MAP_SIZE`
- Check disk space and permissions
- Reduce memory scan limits

**Memory growing large**
- Clean completed tasks periodically
- Archive old session data
- Monitor with `apex memory show`

## Advanced Usage

### Custom MCP Tools:
Extend APEX with custom MCP tools by modifying the MCP server implementation.

### Remote MCP Servers:
Configure APEX MCP server for remote access:
```json
{
  "mcpServers": {
    "apex-remote": {
      "command": "ssh",
      "args": ["remote-host", "python", "-m", "apex.mcp"],
      "env": {
        "APEX_LMDB_PATH": "/remote/path/apex.db"
      }
    }
  }
}
```

### Multi-Project Setup:
Configure Claude Code to work with multiple APEX projects:
```json
{
  "mcpServers": {
    "apex-project1": {
      "command": "python",
      "args": ["-m", "apex.mcp"],
      "env": {
        "APEX_LMDB_PATH": "./project1/apex.db"
      }
    },
    "apex-project2": {
      "command": "python",
      "args": ["-m", "apex.mcp"],
      "env": {
        "APEX_LMDB_PATH": "./project2/apex.db"
      }
    }
  }
}
```

## Related Flows
- [Claude Multi-Instance Flow](claude-multi-instance-flow.md) - Multiple Claude Code coordination
- [Memory Management Flow](memory-management-flow.md) - Working with shared memory
- [Multi-Agent Coordination Flow](multi-agent-coordination-flow.md) - Agent collaboration patterns
- [Project Creation Flow](project-creation-flow.md) - Initial MCP setup
