# CLI Operations Flow

## Purpose
Comprehensive guide to all APEX command-line interface operations, options, and workflows for managing projects, agents, and system operations.

## Prerequisites
- APEX installed (`uv pip install -e ".[dev]"`)
- Python 3.11+ and UV package manager
- Terminal access

## Command Structure

### Basic Syntax:
```bash
uv run apex <command> [options] [arguments]
```

### Help System:
```bash
uv run apex --help              # Main help
uv run apex <command> --help    # Command-specific help
uv run apex version             # Show version information
```

## Core Commands

### 1. Project Management

#### Create New Project:
```bash
uv run apex new <project_name> [options]
```

**Options:**
- `--template <name>` / `-t` - Use project template
- `--tech <stack>` - Technology stack (comma-separated)
- `--no-git` - Skip git initialization

**Examples:**
```bash
uv run apex new calculator
uv run apex new api-service --tech "Python,FastAPI"
uv run apex new frontend --template react-starter --no-git
```

#### Initialize Existing Project:
```bash
uv run apex init [options]
```

**Options:**
- `--import <config.json>` - Import existing configuration

**Examples:**
```bash
uv run apex init
uv run apex init --import ../other-project/apex.json
```

#### List Projects:
```bash
uv run apex list
```

### 2. Agent Management

#### Start Agents:
```bash
uv run apex start [options]
```

**Options:**
- `--task "<description>"` - Start with specific task
- `--agents <list>` - Start specific agents (comma-separated)
- `--continue <checkpoint>` - Continue from checkpoint

**Examples:**
```bash
uv run apex start
uv run apex start --task "Create user authentication system"
uv run apex start --agents "supervisor,coder"
```

#### Stop Agents:
```bash
uv run apex stop
```

#### Pause/Resume Agents:
```bash
uv run apex pause
uv run apex resume
```

#### Check Status:
```bash
uv run apex status
```

### 3. Agent Sub-Commands

#### Agent List:
```bash
uv run apex agent list
```

#### Restart Agent:
```bash
uv run apex agent restart <agent_name>
```

**Valid Agent Names:**
- `supervisor`
- `coder`
- `adversary`

#### View Agent Logs:
```bash
uv run apex agent logs <agent_name> [options]
```

**Options:**
- `--follow` / `-f` - Follow log output
- `--lines <n>` / `-n` - Number of lines (default: 50)
- `--level <level>` / `-l` - Filter by log level
- `--grep <pattern>` / `-g` - Filter by pattern

**Examples:**
```bash
uv run apex agent logs supervisor
uv run apex agent logs coder --follow --level error
uv run apex agent logs adversary -n 100 --grep "security"
```

### 4. Memory Operations

#### Show Memory Contents:
```bash
uv run apex memory show [key]
```

**Examples:**
```bash
uv run apex memory show                    # List all keys
uv run apex memory show /tasks/pending     # Show specific key
```

#### Query Memory:
```bash
uv run apex memory query <pattern> [options]
```

**Options:**
- `--regex` / `-r` - Use regex instead of glob
- `--limit <n>` / `-l` - Maximum results (default: 50)
- `--content` / `-c` - Search in content, not just keys

**Examples:**
```bash
uv run apex memory query "*task*"
uv run apex memory query "error" --regex --content
uv run apex memory query "/agents/*" --limit 10
```

#### Watch Memory Changes:
```bash
uv run apex memory watch [pattern] [options]
```

**Options:**
- `--timeout <seconds>` / `-t` - Watch timeout (default: 30)
- `--interval <seconds>` / `-i` - Polling interval (default: 1.0)

**Examples:**
```bash
uv run apex memory watch
uv run apex memory watch "/tasks/*" --timeout 60
uv run apex memory watch "*" --interval 0.5
```

### 5. Interface Commands

#### Launch TUI:
```bash
uv run apex tui [options]
```

**Options:**
- `--layout <name>` - TUI layout (default: dashboard)
- `--theme <name>` - Color theme (default: dark)

## Command Options Reference

### Global Options:
Most commands support:
- `--help` - Show command help
- `--verbose` / `-v` - Verbose output
- `--quiet` / `-q` - Suppress non-error output

### Project Creation Options:
```bash
--template <name>     # Use project template
--tech <stack>        # Technology stack (comma-separated)
--no-git             # Skip git initialization
```

### Agent Management Options:
```bash
--task "<desc>"      # Initial task description
--agents <list>      # Specific agents to start
--continue <id>      # Continue from checkpoint
```

### Memory Query Options:
```bash
--regex / -r         # Use regex matching
--limit <n> / -l     # Limit results
--content / -c       # Search content
--timeout <s> / -t   # Operation timeout
--interval <s> / -i  # Polling interval
```

### Log Viewing Options:
```bash
--follow / -f        # Follow log output
--lines <n> / -n     # Number of lines
--level <level> / -l # Filter by level
--grep <pattern> / -g # Filter by pattern
```

## Workflow Examples

### Complete Project Setup:
```bash
# 1. Create project
uv run apex new my-api --tech "Python,FastAPI"

# 2. Enter project
cd my-api

# 3. Start with task
uv run apex start --task "Create REST API for user management"

# 4. Monitor progress
uv run apex status

# 5. View logs
uv run apex agent logs coder --follow
```

### Development Workflow:
```bash
# Start agents
uv run apex start

# Check what's happening
uv run apex status

# Monitor specific agent
uv run apex agent logs adversary --follow --level warn

# Restart problematic agent
uv run apex agent restart coder

# Launch interactive interface
uv run apex tui
```

### Debugging Workflow:
```bash
# Check overall status
uv run apex status

# View recent memory changes
uv run apex memory watch --timeout 10

# Search for errors
uv run apex memory query "*error*" --content

# View error logs
uv run apex agent logs supervisor --level error -n 100
```

### Memory Investigation:
```bash
# List all memory keys
uv run apex memory show

# Look at task status
uv run apex memory show /tasks/pending

# Search for specific content
uv run apex memory query "authentication" --content

# Watch for new tasks
uv run apex memory watch "/tasks/*"
```

## Exit Codes

### Standard Exit Codes:
- `0` - Success
- `1` - General error
- `2` - Invalid arguments
- `130` - Interrupted by user (Ctrl+C)

### Command-Specific Behavior:
- **start** - Returns when agents are started (doesn't wait for completion)
- **status** - Returns after displaying current status
- **logs** - With `--follow`, runs until interrupted
- **memory watch** - Runs until timeout or interruption

## Environment Variables

### APEX Configuration:
```bash
export APEX_LMDB_PATH="/path/to/database"     # Custom LMDB location
export APEX_LOG_LEVEL="debug"                # Set log level
export APEX_CONFIG_DIR="/path/to/configs"    # Custom config directory
```

### UV Integration:
```bash
# All commands should be run with UV
uv run apex <command>

# Or install globally and run directly
uv pip install -e ".[dev]"
apex <command>
```

## Common Patterns

### Quick Start Pattern:
```bash
uv run apex new project && cd project && uv run apex start --task "Initial setup"
```

### Monitoring Pattern:
```bash
uv run apex status && uv run apex memory show && uv run apex agent logs supervisor -n 20
```

### Restart Pattern:
```bash
uv run apex stop && uv run apex start --continue last
```

## Troubleshooting Commands

### System Health Check:
```bash
uv run apex version                    # Check APEX version
uv run apex status                     # Check agent status
uv run apex memory show /config       # Check project config
```

### Log Analysis:
```bash
uv run apex agent logs supervisor --level error
uv run apex agent logs coder --grep "fail" -n 50
uv run apex agent logs adversary --follow
```

### Memory Debugging:
```bash
uv run apex memory query "*error*" --content
uv run apex memory watch "/sessions/*" --timeout 30
uv run apex memory show /agents/supervisor/status
```

## Related Flows
- [Project Creation Flow](project-creation-flow.md) - Detailed project setup
- [Agent Management Flow](agent-management-flow.md) - Managing agents
- [Status Monitoring Flow](status-monitoring-flow.md) - System monitoring
- [Memory Management Flow](memory-management-flow.md) - Working with shared memory
