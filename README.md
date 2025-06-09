# APEX - Adversarial Pair EXecution

<pre style="font-family: monospace; line-height: 1;">
 █████╗ ██████╗ ███████╗██╗  ██╗
██╔══██╗██╔══██╗██╔════╝╚██╗██╔╝
███████║██████╔╝█████╗   ╚███╔╝
██╔══██║██╔═══╝ ██╔══╝   ██╔██╗
██║  ██║██║     ███████╗██╔╝ ██╗
╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
</pre>

<div align="center">
<strong>A CLI/TUI orchestration tool for adversarial pair coding with AI agents</strong>

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![Claude Code](https://img.shields.io/badge/Claude-Code-purple.svg)](https://claude.ai/code)
[![Development Status](https://img.shields.io/badge/status-alpha-yellow.svg)](https://github.com/nibzard/apex)

</div>

## Overview

APEX orchestrates multiple Claude Code instances working in an adversarial manner to produce robust, secure code at unprecedented velocity. Built on Claude Code's native MCP system, APEX provides seamless multi-agent workflows with intelligent task distribution and real-time collaboration.

### Key Features

- 🤖 **Three-Agent System**: Supervisor, Coder, and Adversary agents working collaboratively
- 🔄 **Adversarial Workflow**: Continuous code generation, testing, and improvement cycles
- 💾 **State Persistence**: Complete session management with pause/resume capabilities
- ⚡ **Claude Code Integration**: Native MCP integration with automatic setup
- 🔧 **Shared Memory**: LMDB backend for secure agent communication
- 📊 **Real-time Coordination**: Intelligent task distribution and dependency management
- 🚀 **Zero Configuration**: Projects ready for Claude Code out of the box

## Quick Start

### Prerequisites

Before installing APEX, ensure you have:

- **Python 3.11+** installed
- **UV package manager** ([install guide](https://github.com/astral-sh/uv))
- **Claude CLI** installed and configured ([setup guide](https://claude.ai/code))
- **Git** for version control

### Installation

```bash
# Clone the repository
git clone https://github.com/nibzard/apex
cd apex

# Install dependencies and setup development environment
uv sync
uv pip install -e ".[dev]"
```

### Quick Demo

```bash
# Create a new project with Claude Code integration
uv run apex new my-calculator --tech "Python" --no-git

# Enter the project directory
cd my-calculator

# Option 1: Use APEX orchestration
uv run apex start --task "Create a simple calculator with add, subtract, multiply, and divide functions"

# Option 2: Use Claude Code with APEX MCP tools (Recommended)
claude  # Automatically loads APEX MCP integration

# In Claude Code, try:
# > apex_project_status my-calculator-id
# > apex_lmdb_write /projects/my-calculator/task1 '{"description": "Create calculator", "status": "pending"}'
# > apex_lmdb_read /projects/my-calculator/task1
```

### Core Commands

```bash
# Project management
uv run apex new <project>           # Create new project
uv run apex init                    # Initialize existing project
uv run apex list                    # List projects

# Session control
uv run apex start                   # Start agents
uv run apex start --task "..."      # Start with specific task
uv run apex status                  # Show agent status
uv run apex stop                    # Stop all agents

# Version and help
uv run apex version                 # Show version
uv run apex --help                  # Show help
```

## What's Working Now

APEX is in **Alpha** state with core functionality available:

### ✅ **Ready to Use**
- **Project creation**: `apex new` and `apex init` commands work
- **Task workflows**: `apex start --task` creates and tracks multi-agent workflows
- **Status monitoring**: `apex status` shows real-time agent and task information
- **LMDB persistence**: All workflow state is saved and queryable
- **MCP integration**: Complete MCP server with LMDB backend

### 🔧 **Functional but Basic**
- **Agent orchestration**: Supervisor creates tasks, assigns to Coder/Adversary
- **Process management**: Can spawn Claude CLI processes (requires Claude CLI setup)
- **Stream parsing**: Captures and stores agent communication events

### 🚧 **In Development**
- **TUI interface**: Basic structure exists, full interactivity coming soon
- **Session continuity**: Pause/resume functionality planned
- **Git integration**: Automatic commits and branch management

### 📋 **Try It Out**
```bash
# Quick test (no Claude CLI required for basic workflow demo)
git clone https://github.com/nibzard/apex && cd apex
uv sync && uv pip install -e ".[dev]"

# Test basic commands
uv run apex version
uv run apex --help

# Create test config and try workflow
echo '{"project_id":"test-123","name":"test-project","description":"Test project","tech_stack":["Python"],"project_type":"CLI Tool","features":["testing"],"created_at":"2025-01-08T12:00:00"}' > test-config.json
mkdir test-project && cd test-project
uv run apex init --import ../test-config.json
uv run apex start --task "Create a simple hello world program"
uv run apex status
```

## Architecture

APEX integrates with Claude Code's native MCP system for seamless multi-agent workflows:

```
┌─────────────────────────────────────────┐
│              APEX CLI/TUI               │
│    Project Setup │ Monitoring │ Config  │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│            Claude Code                  │
│     Native MCP │ Agent Tools │ stdio    │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│           APEX MCP Server               │
│  apex_lmdb_* │ apex_project_* │ Tools   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│            LMDB Database                │
│  Projects │ Tasks │ Agent State │ Code  │
└─────────────────────────────────────────┘
```

### New Integration Model

Instead of managing external Claude CLI processes, APEX now:

1. **Sets up MCP configuration** automatically when creating projects
2. **Provides APEX MCP tools** to Claude Code instances
3. **Enables multi-agent coordination** through shared LMDB memory
4. **Simplifies deployment** - no external servers to manage

### Agent Roles

- **Supervisor**: Plans tasks, coordinates work, manages git operations
- **Coder**: Implements features, fixes bugs, writes clean code
- **Adversary**: Tests code, finds vulnerabilities, ensures quality

## Core Concepts

### Adversarial Development

APEX implements an adversarial development model where agents challenge each other:

1. **Supervisor** breaks down features into specific tasks
2. **Coder** implements solutions following best practices
3. **Adversary** rigorously tests and finds edge cases
4. Cycle continues until quality standards are met

### Memory System

All agent communication happens through LMDB using MCP tools:

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

### Session Continuity

APEX provides seamless pause/resume capabilities:

- **Checkpoints**: Complete system state snapshots
- **Event Replay**: Restore agent context and conversation history
- **Process Recovery**: Automatic restart with full state restoration

## Commands Reference

### Project Management
```bash
apex new <project>              # Create new project with interactive setup
  --template <name>             # Use project template
  --tech <stack>                # Specify technology stack
  --no-git                      # Skip git initialization

apex init                       # Initialize APEX in existing directory
  --import <config.json>        # Import existing configuration

apex list                       # List all APEX projects
```

### Session Control
```bash
apex start                      # Start all agents in monitoring mode
  --task "<description>"        # Start with specific task/workflow
  --agents <list>               # Start only specified agents

apex status                     # Show detailed agent and task status
apex stop                       # Stop all running agents

# Future commands (planned)
apex pause                      # Pause with checkpoint
apex resume <checkpoint>        # Resume from checkpoint
```

### Development & Monitoring
```bash
apex version                    # Show version information

# Future commands (planned)
apex tui                        # Interactive dashboard
apex agent list                 # List agent details
apex agent logs <agent>         # View agent logs
apex memory show                # Display shared memory
```

### Project Structure

When you create a new APEX project, it generates:

```
my-project/
├── apex.json                   # Project configuration
├── .git/                       # Git repository (optional)
├── apex.db                     # LMDB database (created on first run)
└── ...                         # Your project files
```

## Configuration

### Project Configuration (apex.json)

Each APEX project contains an `apex.json` configuration file:

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

### MCP Integration (.mcp.json)

APEX automatically creates `.mcp.json` files for Claude Code integration:

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

This enables Claude Code to automatically connect to APEX's MCP server when working in any APEX project directory.

### APEX MCP Tools

APEX provides specialized MCP tools for multi-agent coordination:

- **apex_lmdb_read**: Read data from shared memory
- **apex_lmdb_write**: Write data to shared memory
- **apex_lmdb_list**: List keys with optional prefix
- **apex_lmdb_scan**: Scan key-value pairs with limits
- **apex_lmdb_delete**: Delete keys from memory
- **apex_project_status**: Get project status and summary

### Multi-Agent Workflows

With Claude Code + APEX MCP tools, you can:

1. **Start multiple Claude Code instances** in the same project directory
2. **Coordinate through shared memory** using APEX MCP tools
3. **Assign different roles** (Supervisor, Coder, Adversary) to each instance
4. **Track progress** across all agents in real-time

## TUI Interface

The interactive TUI provides real-time monitoring:

```
┌─ APEX Dashboard ────────────────────────────────────────────┐
│ Project: myapp | Session: abc-123 | Git: main (3 ahead)     │
├─────────────────────────────────────────────────────────────┤
│ ┌─ Agent Status ──────────┐ ┌─ Current Tasks ─────────────┐ │
│ │ Supervisor  ✓ Planning  │ │ ▶ Implement user auth       │ │
│ │ Coder       ✓ Coding    │ │   ├─ Create user model      │ │
│ │ Adversary   ✓ Testing   │ │   ├─ Add login endpoint     │ │
│ │                         │ │   └─ Setup JWT tokens       │ │
│ │ Memory: 2.1GB           │ │                             │ │
│ │ Uptime: 02:34:56        │ │ ▶ Add error handling        │ │
│ └─────────────────────────┘ └─────────────────────────────┘ │
│ [F1]Help [F2]Agents [F3]Memory [F4]Tasks [F5]Git [Q]Quit    │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager
- [Claude CLI](https://claude.ai/code) installed and configured
- Git (for version control integration)
- [GitHub CLI](https://cli.github.com/) (for GitHub integration)

## Examples

### Creating a Calculator with Claude Code

```bash
# Create new project with automatic MCP setup
uv run apex new calculator --tech "Python" --no-git
cd calculator

# Start Claude Code (automatically loads APEX MCP server)
claude
```

In Claude Code:
```
> I want to create a calculator with multiple agents. Let me set up the project structure first.

> apex_lmdb_write /projects/calc-123/config '{"name": "calculator", "status": "active"}'

> apex_lmdb_write /projects/calc-123/tasks/task1 '{"description": "Create Calculator class with basic arithmetic", "assigned_to": "coder", "status": "pending"}'

> apex_lmdb_write /projects/calc-123/tasks/task2 '{"description": "Review and test Calculator implementation", "assigned_to": "adversary", "status": "pending"}'

> apex_project_status calc-123
```

This enables seamless multi-agent coordination through shared memory while using Claude Code's familiar interface.

### Multi-Agent Web API Development

```bash
# Create API project with MCP integration
uv run apex new todo-api --tech "Python,FastAPI,SQLAlchemy"
cd todo-api

# Terminal 1: Supervisor Agent
claude --prompt "You are the Supervisor agent for this todo API project. Break down tasks and coordinate work."

# Terminal 2: Coder Agent
claude --prompt "You are the Coder agent. Implement features assigned to you."

# Terminal 3: Adversary Agent
claude --prompt "You are the Adversary agent. Review code and find issues."
```

Each Claude Code instance can coordinate through APEX MCP tools for seamless multi-agent development.

## Development

### Current Implementation Status

APEX has reached **Alpha** status with core functionality implemented:

#### ✅ **Completed Components**
- **Project Structure**: Complete source code organization
- **Build System**: UV package management and dependencies
- **CLI Framework**: Functional commands with Rich output formatting
- **Testing Suite**: Pytest with coverage reporting (41 tests passing)
- **Code Quality**: Pre-commit hooks with Black, Ruff, MyPy
- **Configuration**: Pydantic models and JSON config files
- **Claude Code Integration**: Native MCP integration with automatic setup
- **APEX MCP Server**: Full MCP server with stdio transport for Claude Code
- **Memory Patterns**: Comprehensive LMDB operations with 65% test coverage
- **Agent Coordination**: Supervisor/Coder/Adversary prompts and tools
- **Task Workflow**: Complete task assignment and tracking system
- **E2E Testing**: End-to-end integration tests with actual Claude Code

#### 🚧 **In Progress**
- **TUI Interface**: Interactive dashboard (basic structure complete)
- **Session Continuity**: Pause/resume capabilities
- **Git Integration**: Automatic commit and branch management
- **GitHub Integration**: PR and issue management

#### 📋 **Planned Features**
- **Multi-project Management**: Project switching and templates
- **Performance Monitoring**: Metrics and analytics
- **Remote MCP Servers**: Distributed agent deployment
- **Plugin System**: Custom agent types and tools

### Development Setup

```bash
# Clone and setup
git clone https://github.com/nibzard/apex
cd apex
uv sync
uv pip install -e ".[dev]"

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Code quality checks
uv run black src tests
uv run ruff check --fix src tests
uv run mypy src

# Run all quality checks
uv run pre-commit run --all-files

# Test CLI functionality
uv run apex version
uv run apex --help
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Troubleshooting

### Common Issues

**"No APEX project found in current directory"**
```bash
# Initialize APEX in your project
uv run apex init
```

**"Claude CLI not found"**
```bash
# Install Claude CLI first
# Follow setup guide at https://claude.ai/code
```

**"MCP server connection failed"**
```bash
# Check if APEX MCP server can start
APEX_LMDB_PATH="./test.db" uv run python -m apex.mcp

# Or check Claude Code MCP status
claude mcp list
```

### Performance Notes

APEX is designed for high performance:

- **Sub-100ms**: Agent communication latency via LMDB
- **Sub-10ms**: Memory operations with LMDB
- **3+ Agents**: Concurrent process support
- **Auto-recovery**: Automatic restart on agent failure

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- 📖 **Documentation**: [Full specification](specs.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/nibzard/apex/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/nibzard/apex/discussions)

---

<div align="center">
<sub>Built with ❤️ for the AI-powered development future</sub>
</div>
