# APEX - Adversarial Pair EXecution

<div align="center">

```
 █████╗ ██████╗ ███████╗██╗  ██╗
██╔══██╗██╔══██╗██╔════╝╚██╗██╔╝
███████║██████╔╝█████╗   ╚███╔╝
██╔══██║██╔═══╝ ██╔══╝   ██╔██╗
██║  ██║██║     ███████╗██╔╝ ██╗
╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
```

**A CLI/TUI orchestration tool for adversarial pair coding with AI agents**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![Claude Code](https://img.shields.io/badge/Claude-Code-purple.svg)](https://claude.ai/code)
[![Development Status](https://img.shields.io/badge/status-pre--alpha-orange.svg)](https://github.com/nibzard/apex)

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

### Installation

```bash
# Clone from source (currently pre-release)
git clone https://github.com/nibzard/apex
cd apex
uv sync && uv pip install -e ".[dev]"

# Run development setup
PYTHONPATH=./src uv run python scripts/setup_dev.py
```

### Basic Usage

```bash
# Run CLI (development mode)
./scripts/dev.sh cli --help

# Show version
./scripts/dev.sh cli version

# Run tests
./scripts/dev.sh test

# Format and lint code
./scripts/dev.sh lint
```

> **Note**: APEX is currently in active development. The CLI commands above show the basic structure, but full functionality is still being implemented according to the [detailed specifications](specs.md).

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

## Commands

### Project Management
```bash
apex new <project>              # Create new project
apex init                       # Initialize in existing directory
apex list                       # List all projects
```

### Session Control
```bash
apex start                      # Start all agents
apex pause                      # Pause with checkpoint
apex resume <checkpoint>        # Resume from checkpoint
apex stop                       # Stop all agents
```

### Monitoring
```bash
apex tui                        # Interactive dashboard
apex status                     # Agent status summary
apex logs <agent>              # View agent logs
apex metrics                    # Performance metrics
```

### MCP Management
```bash
apex mcp list                   # List MCP servers
apex mcp test <server>          # Test connectivity
apex mcp tools <server>         # List available tools
apex mcp validate               # Run compliance tests
```

## Configuration

### MCP Server Setup

APEX uses JSON configuration files for MCP servers:

```json
{
  "mcpServers": {
    "lmdb": {
      "command": "python",
      "args": ["-m", "apex.mcp.lmdb_server"],
      "env": {
        "LMDB_PATH": "./apex.db"
      }
    },
    "git": {
      "command": "python", 
      "args": ["-m", "apex.mcp.git_server"],
      "env": {
        "GIT_REPO_PATH": "."
      }
    }
  }
}
```

### Security Configuration

```yaml
# .apex/security.yaml
security:
  mcp:
    tools:
      rate_limits:
        default: 100  # requests per minute
      permissions:
        supervisor: ["*"]
        coder: ["mcp__lmdb__*", "mcp__git__status"]
        adversary: ["mcp__lmdb__read", "mcp__lmdb__list"]
```

## TUI Interface

The interactive TUI provides real-time monitoring:

```
┌─ APEX Dashboard ─────────────────────────────────────────────┐
│ Project: myapp | Session: abc-123 | Git: main (3 ahead)     │
├──────────────────────────────────────────────────────────────┤
│ ┌─ Agent Status ──────────┐ ┌─ Current Tasks ─────────────┐ │
│ │ Supervisor  ✓ Planning  │ │ ▶ Implement user auth      │ │
│ │ Coder       ✓ Coding    │ │   ├─ Create user model     │ │
│ │ Adversary   ✓ Testing   │ │   ├─ Add login endpoint    │ │
│ │                         │ │   └─ Setup JWT tokens      │ │
│ │ Memory: 2.1GB           │ │                             │ │
│ │ Uptime: 02:34:56        │ │ ▶ Add error handling       │ │
│ └─────────────────────────┘ └─────────────────────────────┘ │
│ [F1]Help [F2]Agents [F3]Memory [F4]Tasks [F5]Git [Q]Quit     │
└──────────────────────────────────────────────────────────────┘
```

## Requirements

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager
- [Claude CLI](https://claude.ai/code) installed and configured
- Git (for version control integration)
- [GitHub CLI](https://cli.github.com/) (for GitHub integration)

## Development

### Current Status

APEX is in **active development** with the following components:

- ✅ **Project Structure**: Complete source code organization
- ✅ **Build System**: UV package management and dependencies  
- ✅ **CLI Framework**: Basic command structure with Typer
- ✅ **Testing Suite**: Pytest with coverage reporting
- ✅ **Code Quality**: Pre-commit hooks with Black, Ruff, MyPy
- ✅ **Configuration**: Pydantic models and TOML config
- 🚧 **Process Manager**: Claude CLI orchestration (planned)
- 🚧 **LMDB MCP Server**: Shared memory backend (planned)
- 🚧 **Agent System**: Supervisor/Coder/Adversary agents (planned)
- 🚧 **TUI Interface**: Real-time monitoring dashboard (planned)

### Development Setup

```bash
# Clone and setup
git clone https://github.com/nibzard/apex
cd apex
uv sync
uv pip install -e ".[dev,docs]"

# Run development setup
PYTHONPATH=./src uv run python scripts/setup_dev.py

# Run tests
./scripts/dev.sh test

# Development commands
./scripts/dev.sh --help
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Performance

APEX is designed for high performance:

- **Sub-100ms**: Agent communication latency
- **Sub-10ms**: LMDB operations
- **10+ Agents**: Concurrent process support
- **99.9%**: System reliability with auto-recovery

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