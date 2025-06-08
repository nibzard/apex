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

APEX orchestrates multiple Claude CLI processes working in an adversarial manner to produce robust, secure code at unprecedented velocity. The system maintains developer flow through intelligent session management, real-time monitoring, and seamless pause/resume capabilities.

### Key Features

- 🤖 **Three-Agent System**: Supervisor, Coder, and Adversary agents working collaboratively
- 🔄 **Adversarial Workflow**: Continuous code generation, testing, and improvement cycles
- 💾 **State Persistence**: Complete session management with pause/resume capabilities
- ⚡ **Real-time Monitoring**: Live TUI interface showing agent activity and progress
- 🔧 **MCP Integration**: Model Context Protocol for secure agent communication
- 📊 **LMDB Backend**: Lightning-fast memory-mapped database for state management
- 🎯 **Smart Orchestration**: Intelligent task distribution and dependency management

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
# Create a new project
uv run apex new my-calculator --tech "Python" --no-git

# Enter the project directory
cd my-calculator

# Start APEX with a task
uv run apex start --task "Create a simple calculator with add, subtract, multiply, and divide functions"

# Monitor progress
uv run apex status

# View the TUI dashboard (coming soon)
uv run apex tui
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

APEX uses a multi-layered architecture with three specialized AI agents:

```
┌─────────────────────────────────────────┐
│              APEX CLI/TUI               │
│    Command Parser │ TUI │ Session Mgr   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│           Orchestration Engine          │
│  Process Manager │ Stream Parser │ etc  │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│          Claude CLI Processes           │
│  Supervisor │    Coder    │ Adversary   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│            LMDB MCP Server              │
│  Agent State │ Project Data │ History   │
└─────────────────────────────────────────┘
```

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

### MCP Server Configuration

APEX automatically configures MCP servers for agent communication:

```json
{
  "mcpServers": {
    "lmdb": {
      "command": "python",
      "args": ["-m", "apex.mcp.lmdb_server"],
      "env": {
        "LMDB_PATH": "./apex.db",
        "LMDB_MAP_SIZE": "10737418240"
      }
    }
  }
}
```

### Agent Tool Permissions

Each agent type has specific tool permissions:

- **Supervisor**: Full access (task management, git operations, MCP tools)
- **Coder**: Code editing, file operations, testing, progress reporting
- **Adversary**: Code analysis, testing, issue reporting, decision sampling

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

### Creating a Calculator

```bash
# Create new project
uv run apex new calculator --tech "Python" --no-git
cd calculator

# Start with a specific task
uv run apex start --task "Create a command-line calculator with basic arithmetic operations (add, subtract, multiply, divide) and error handling"

# Check progress
uv run apex status
```

Output:
```
Starting APEX agents...
✓ Started workflow: abc-123-def
Task: Create a command-line calculator with basic arithmetic operations...

Workflow Status:
Status: pending
Tasks: 3
  1. Analyze the following request and plan implementat... → coder
  2. Implement the solution for: Create a command-line... → coder
  3. Test and review the implementation for: Create a ... → adversary
```

### Web API Project

```bash
# Create API project
uv run apex new todo-api --tech "Python,FastAPI,SQLAlchemy"
cd todo-api

# Initialize with detailed task
uv run apex start --task "Build a RESTful API for a todo application with user authentication, CRUD operations for todos, and SQLite database backend"
```

## Development

### Current Implementation Status

APEX has reached **Alpha** status with core functionality implemented:

#### ✅ **Completed Components**
- **Project Structure**: Complete source code organization
- **Build System**: UV package management and dependencies
- **CLI Framework**: Functional commands with Rich output formatting
- **Testing Suite**: Pytest with coverage reporting
- **Code Quality**: Pre-commit hooks with Black, Ruff, MyPy
- **Configuration**: Pydantic models and JSON config files
- **Process Manager**: Claude CLI process orchestration
- **LMDB MCP Server**: Shared memory backend with stdio transport
- **Agent System**: Supervisor/Coder/Adversary agent prompts and coordination
- **Task Workflow**: Complete task assignment and tracking system
- **Stream Parser**: Real-time Claude CLI output parsing and persistence

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
# Check if LMDB server can start
uv run python -m apex.mcp.lmdb_server
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
