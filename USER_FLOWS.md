# APEX User Flows and Workflows

This document consolidates all user interaction patterns and workflows for APEX v2.0.

## Table of Contents

1. [Core Orchestration Workflows](#core-orchestration-workflows)
2. [Project Management](#project-management)
3. [Multi-Agent Coordination](#multi-agent-coordination)
4. [System Management](#system-management)

## Core Orchestration Workflows

### Goal-Based Development Flow

APEX v2.0 uses simple goal analysis to create appropriate task sequences:

#### Implementation Goals
**Pattern**: "Implement [feature]" or "Create [component]"
```bash
# Example: "Implement user authentication"
python apex_simple.py interactive
> Goal: Implement user authentication system

# Generates workflow:
# 1. Research and plan approach (Coder, 30min)
# 2. Implement core functionality (Coder, 90min)
# 3. Test and validate implementation (Adversary, 45min)
```

#### Bug Fix Goals
**Pattern**: "Fix [issue]" or "Resolve [problem]"
```bash
# Example: "Fix login validation bug"
> Goal: Fix login validation bug

# Generates workflow:
# 1. Investigate and reproduce issue (Adversary, 30min)
# 2. Implement fix (Coder, 60min)
# 3. Verify fix and test for regressions (Adversary, 30min)
```

#### Generic Goals
**Pattern**: Any other goal type
```bash
# Example: "Improve API performance"
> Goal: Improve API performance

# Generates workflow:
# 1. Analyze current performance (Adversary, 45min)
# 2. Implement optimizations (Coder, 90min)
# 3. Review and validate improvements (Adversary, 30min)
```

### Adversarial Development Philosophy

APEX implements systematic opposition where agents challenge each other:

1. **Systematic Opposition** - Each agent challenges others' work
2. **Iterative Improvement** - Continuous refinement through feedback
3. **Quality Through Conflict** - Better solutions emerge from constructive challenge
4. **Collaborative Competition** - Agents compete to produce the best outcome

#### Agent Roles in Adversarial Development

**Supervisor Agent**:
- Plans and coordinates overall development strategy
- Challenges assumptions about requirements and approach
- Mediates conflicts between Coder and Adversary
- Ensures progress toward project goals

**Coder Agent**:
- Implements solutions with focus on functionality and elegance
- Defends design decisions against Adversary challenges
- Iterates based on feedback from security and quality reviews
- Strives for clean, maintainable code

**Adversary Agent**:
- Challenges implementations for security vulnerabilities
- Tests edge cases and error conditions aggressively
- Questions design assumptions and architectural choices
- Ensures robustness through systematic attack

## Project Management

### Project Creation and Initialization

#### Creating New Projects
```bash
# Standard project creation
uv run apex new my-project --tech "Python,FastAPI" --no-git

# With project template
uv run apex new web-app --template api-service

# Interactive creation
uv run apex new my-app  # Prompts for details
```

#### Initializing Existing Projects
```bash
# Initialize APEX in existing directory
cd existing-project
uv run apex init

# Import existing configuration
uv run apex init --import config.json
```

### Configuration Management

APEX projects use two main configuration files:

#### apex.json (Project Configuration)
```json
{
  "project_id": "unique-project-id",
  "name": "my-calculator",
  "description": "A simple calculator application",
  "tech_stack": ["Python", "CLI"],
  "project_type": "CLI Tool",
  "features": ["arithmetic", "testing", "cli"],
  "created_at": "2025-01-08T12:00:00Z"
}
```

#### .mcp.json (Claude Code Integration)
```json
{
  "mcpServers": {
    "apex-lmdb": {
      "command": "python",
      "args": ["-m", "apex.mcp"],
      "env": {
        "APEX_LMDB_PATH": "./apex_shared.db",
        "APEX_LMDB_MAP_SIZE": "1073741824"
      }
    }
  }
}
```

## Multi-Agent Coordination

### Using Claude Code with APEX MCP Tools

APEX provides specialized MCP tools for multi-agent coordination:

```bash
# Start multiple Claude Code instances in same project
cd my-project

# Terminal 1: Supervisor Agent
claude --prompt "You are the Supervisor agent. Plan and coordinate work."

# Terminal 2: Coder Agent
claude --prompt "You are the Coder agent. Implement features assigned to you."

# Terminal 3: Adversary Agent
claude --prompt "You are the Adversary agent. Review code and find issues."
```

### APEX MCP Tools Reference

- **apex_lmdb_read**: Read data from shared memory
- **apex_lmdb_write**: Write data to shared memory
- **apex_lmdb_list**: List keys with optional prefix
- **apex_lmdb_scan**: Scan key-value pairs with limits
- **apex_lmdb_delete**: Delete keys from memory
- **apex_project_status**: Get project status and summary

### Multi-Agent Communication Example

```bash
# In Claude Code (Supervisor):
> apex_lmdb_write /projects/calc-123/tasks/task1 '{"description": "Create Calculator class", "assigned_to": "coder", "status": "pending"}'

# In Claude Code (Coder):
> apex_lmdb_read /projects/calc-123/tasks/task1
> # Implement the feature...
> apex_lmdb_write /projects/calc-123/tasks/task1 '{"status": "completed", "deliverable": "Calculator class implemented in calc.py"}'

# In Claude Code (Adversary):
> apex_lmdb_read /projects/calc-123/tasks/task1
> # Review the implementation...
> apex_lmdb_write /projects/calc-123/issues/issue1 '{"description": "Calculator lacks input validation", "severity": "medium"}'
```

## System Management

### Session Control

```bash
# Start orchestration with specific goal
uv run apex start --task "Create calculator with error handling"

# Monitor current status
uv run apex status

# Stop all agents
uv run apex stop
```

### Memory Management

The LMDB memory structure organizes project data:

```
/projects/{project_id}/
├── /config          # Project configuration
├── /agents/         # Agent states and prompts
├── /memory/         # Shared memory
│   ├── /tasks/      # Task assignments
│   ├── /code/       # Source code
│   ├── /tests/      # Test suites
│   └── /issues/     # Bug reports
├── /sessions/       # Session history
└── /git/           # Version control state
```

### Status Monitoring

```bash
# View project status
uv run apex status

# Monitor specific components
uv run apex agent status
uv run apex memory show
uv run apex tasks list
```

### Error Handling and Recovery

APEX provides robust error handling:

1. **Automatic Restart**: Failed workers are automatically restarted
2. **State Persistence**: All progress is saved in LMDB
3. **Graceful Degradation**: System continues with reduced capability
4. **Recovery Procedures**: Clear steps for manual intervention

### Logging and Debugging

```bash
# View system logs
uv run apex logs

# Debug specific agent
uv run apex agent logs <agent-name>

# Check memory state
uv run apex memory scan /projects/{id}/

# Validate system health
uv run apex health check
```

## Command Reference

### Essential Commands

```bash
# Project Management
uv run apex new <project>           # Create new project
uv run apex init                    # Initialize existing project
uv run apex list                    # List projects

# Session Control
uv run apex start                   # Start agents
uv run apex start --task "..."      # Start with specific task
uv run apex status                  # Show agent status
uv run apex stop                    # Stop all agents

# System Information
uv run apex version                 # Show version
uv run apex --help                  # Show help
```

### Advanced Operations

```bash
# Agent Management
uv run apex agent list              # List active agents
uv run apex agent restart <agent>   # Restart specific agent
uv run apex agent logs <agent>      # View agent logs

# Memory Operations
uv run apex memory show             # Display memory contents
uv run apex memory cleanup          # Clean up old data
uv run apex memory backup           # Create backup

# Development Tools
uv run apex validate                # Validate project configuration
uv run apex health                  # System health check
uv run apex debug                   # Debug mode with verbose output
```

This consolidation provides a single reference for all APEX user interactions while maintaining the detailed workflow information from the original user flow files.
