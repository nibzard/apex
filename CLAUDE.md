# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

APEX (Adversarial Pair EXecution) is a CLI/TUI orchestration tool that manages multiple Claude CLI processes working in an adversarial manner to produce robust, secure code. The system uses three agent types: Supervisor, Coder, and Adversary, all communicating through an LMDB database via the Model Context Protocol (MCP).

## Architecture

### Core Components
- **Orchestration Engine**: Manages Claude CLI processes, parses streaming JSON output, and handles session continuations
- **Agent System**: Three specialized agents (Supervisor, Coder, Adversary) each running in separate Claude CLI processes
- **LMDB MCP Server**: Provides shared memory and state persistence using LMDB with MCP tool interfaces
- **Transport Layer**: Uses stdio for local MCP communication, with optional SSE support for remote connections

### Key Design Patterns
- **Process Isolation**: Each agent runs in its own `claude -p` process with `--output-format stream-json`
- **MCP Tool Naming**: All tools follow the convention `mcp__serverName__toolName` (e.g., `mcp__lmdb__read`)
- **Streaming JSON Parsing**: Real-time parsing of Claude CLI output with event-driven state updates
- **State Persistence**: All agent communication and state changes are stored in LMDB for pause/resume capabilities

## Development Commands

### Project Setup
```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e ".[dev,docs]"

# Setup pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_process_manager.py

# Run with coverage
uv run pytest --cov=apex --cov-report=html

# Run MCP compliance tests
uv run pytest tests/mcp/

# Run integration tests
uv run pytest tests/integration/
```

### Code Quality
```bash
# Format code
uv run black src tests

# Lint and fix
uv run ruff check --fix src tests

# Type checking
uv run mypy src

# Run all quality checks
uv run pre-commit run --all-files
```

### Development Server
```bash
# Start development environment
uv run python scripts/setup_dev.py

# Run benchmarks
uv run python scripts/run_benchmarks.py

# Build documentation
uv run mkdocs serve
```

## Technical Implementation Details

### Agent Communication Flow
1. APEX spawns Claude CLI processes with MCP configurations
2. Each agent gets specific tool permissions via `--allowedTools`
3. Agents communicate by reading/writing to LMDB via MCP tools
4. Stream parser captures all JSON events for state management
5. Agents use git and gh CLI directly for version control operations

### Version Control
- **Supervisor Agent**: Uses `git commit`, `gh pr create`, `gh issue create`
- **Coder Agent**: Uses `git add`, `git status` to stage changes
- **Adversary Agent**: Uses `git log`, `git diff` for code review
- Agents have these tools available through standard Claude CLI capabilities

### LMDB Memory Structure
```
/projects/{project_id}/
  ├── /config          # Project metadata
  ├── /agents/          # Agent states and prompts
  ├── /memory/          # Shared memory (tasks, code, tests, issues)
  ├── /sessions/        # Session history and checkpoints
  └── /git/             # Git status and commit history
```

### MCP Server Integration
- Primary LMDB server provides core memory operations
- Optional Git server for version control operations
- GitHub server for remote repository management
- Permission server for handling tool access control

### Session Continuation
- Checkpoints capture complete system state including process states, memory snapshots, and pending operations
- Resume functionality restarts processes with full context restoration
- Event replay ensures consistency across interruptions

## Key Dependencies

- **Claude Integration**: Uses `claude` CLI with streaming JSON output and MCP configuration
- **MCP Framework**: Model Context Protocol for agent communication
- **LMDB**: Lightning Memory-Mapped Database for state persistence
- **Git/GitHub CLI**: Version control operations (agents use these directly)
- **UV**: Package management and dependency resolution
- **Textual**: Terminal User Interface framework
- **Pydantic**: Data validation and serialization

## Configuration Files

### MCP Server Configuration
- `configs/lmdb_mcp.json`: LMDB MCP server setup for all agents

### Development Tools
- `pyproject.toml`: Project dependencies and tool configuration
- `.github/workflows/`: CI/CD pipeline definitions
- `tests/`: Comprehensive test suite including MCP compliance tests

## Important Notes

- Agent prompts are dynamically generated based on project configuration
- All tool names must follow MCP naming convention for proper routing
- LMDB operations use transactions for ACID compliance
- Process management includes automatic restart and health monitoring
- Security features include OAuth 2.0 for remote MCP servers and TLS for SSE transport