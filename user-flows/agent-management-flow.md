# Agent Management Flow

## Purpose
Start, stop, pause, resume, and monitor the three APEX agents (Supervisor, Coder, Adversary) that work together to accomplish development tasks.

## Prerequisites
- APEX project initialized (`apex.json` exists)
- APEX installed with dependencies
- Claude CLI installed and configured (for full functionality)

## Agent Types Overview

### The Three Agents:
1. **Supervisor** - Plans tasks, coordinates work, manages git operations
2. **Coder** - Implements features, fixes bugs, writes clean code
3. **Adversary** - Tests code, finds vulnerabilities, ensures quality

## Step-by-Step Process

### 1. Starting Agents

#### Start All Agents:
```bash
uv run apex start
```

#### Start with Specific Task:
```bash
uv run apex start --task "Create a user authentication system"
```

#### Start Specific Agents:
```bash
uv run apex start --agents "supervisor,coder"
uv run apex start --agents "adversary"
```

### 2. Monitoring Agent Status

#### Check Overall Status:
```bash
uv run apex status
```

**Status Display Includes:**
- Agent running/stopped status
- Memory usage per agent
- Uptime for each agent
- Pending task counts
- Next task preview

#### View Detailed Agent List:
```bash
uv run apex agent list
```

### 3. Managing Individual Agents

#### Restart Specific Agent:
```bash
uv run apex agent restart supervisor
uv run apex agent restart coder
uv run apex agent restart adversary
```

#### View Agent Logs:
```bash
uv run apex agent logs supervisor
uv run apex agent logs coder --follow
uv run apex agent logs adversary --lines 100 --level error
```

**Log Options:**
- `--follow` / `-f` - Follow log output in real-time
- `--lines` / `-n` - Number of lines to show (default: 50)
- `--level` / `-l` - Filter by log level (error, warn, info, debug)
- `--grep` / `-g` - Filter by search pattern

### 4. Pausing and Resuming

#### Pause All Agents:
```bash
uv run apex pause
```

#### Resume All Agents:
```bash
uv run apex resume
```

### 5. Stopping Agents

#### Stop All Agents:
```bash
uv run apex stop
```

## Key Commands Reference

```bash
# Starting
uv run apex start                              # Start all agents
uv run apex start --task "task description"    # Start with specific task
uv run apex start --agents "supervisor,coder"  # Start specific agents

# Monitoring
uv run apex status                             # Show system status
uv run apex agent list                         # List all agents

# Individual Management
uv run apex agent restart <agent_name>         # Restart specific agent
uv run apex agent logs <agent_name>            # View agent logs

# Session Control
uv run apex pause                              # Pause all agents
uv run apex resume                             # Resume all agents
uv run apex stop                               # Stop all agents
```

## Expected Outcomes

### Starting Agents Successfully:
```
✓ Started supervisor agent
✓ Started coder agent
✓ Started adversary agent

Use 'apex status' to monitor agents
Use 'apex tui' for interactive monitoring
```

### Status Display Example:
```
Agent Status:
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Agent      ┃ Status      ┃ Memory  ┃ Uptime   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ supervisor │ 🟢 Running  │ 45 MB   │ 2m 15s   │
│ coder      │ 🟢 Running  │ 52 MB   │ 2m 10s   │
│ adversary  │ 🟢 Running  │ 38 MB   │ 2m 8s    │
└────────────┴─────────────┴─────────┴──────────┘

Task Summary:
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Agent      ┃ Pending Tasks ┃ Next Task                               ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Supervisor │ 1             │ Plan authentication system architecture │
│ Coder      │ 2             │ Implement user registration endpoint... │
│ Adversary  │ 1             │ Review registration security vulnera... │
└────────────┴───────────────┴─────────────────────────────────────────┘

Total Memory: 135 MB
Active Processes: 3
```

## Agent Workflow Process

### With Task Assignment:
1. **Supervisor** receives user task
2. **Supervisor** breaks down into subtasks
3. **Supervisor** assigns tasks to **Coder** and **Adversary**
4. **Coder** implements solutions
5. **Adversary** tests and reviews implementations
6. Cycle continues until task completion

### Without Specific Task:
1. Agents start in monitoring mode
2. Wait for tasks via CLI, TUI, or MCP tools
3. Process tasks as they're assigned
4. Maintain idle state when no work available

## TUI Integration

### Interactive Management:
```bash
uv run apex tui
```

**TUI Features:**
- Real-time agent status monitoring
- Start/stop agents with buttons
- View logs in real-time
- Task assignment and tracking
- Memory browser

**Navigation:**
- `F1` - Help
- `F2` - Agents screen
- `F3` - Memory browser
- `F4` - Task manager
- `Q` - Quit

## Process Management Details

### Agent Process Structure:
Each agent runs as a separate Claude CLI process:
```bash
claude -p /path/to/agent/prompt --output-format stream-json
```

### Memory Management:
- Shared LMDB database for communication
- Each agent has isolated memory space
- Cross-agent communication via memory tools

### Health Monitoring:
- Automatic process restart on failure
- Memory usage tracking
- Uptime monitoring
- Log aggregation

## Common Issues

**"No APEX project found"**
- Run `apex init` first to initialize project
- Ensure you're in correct directory with `apex.json`

**"Claude CLI not found"**
- Install Claude CLI: https://claude.ai/code
- Ensure Claude CLI is in PATH

**"Agent failed to start"**
- Check Claude CLI configuration
- Verify LMDB database accessibility
- Review agent logs for specific errors

**"Agents consuming high memory"**
- Monitor with `apex status`
- Restart specific agents if needed
- Check for memory leaks in logs

## Related Flows
- [Task Workflow Flow](task-workflow-flow.md) - How agents process tasks
- [Status Monitoring Flow](status-monitoring-flow.md) - Detailed monitoring
- [TUI Navigation Flow](tui-navigation-flow.md) - Interactive management
- [Logging & Debugging Flow](logging-debugging-flow.md) - Troubleshooting agents
