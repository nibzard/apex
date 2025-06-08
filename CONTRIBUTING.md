# Contributing to APEX

We welcome contributions to APEX! This document provides guidelines for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Project Structure](#project-structure)
- [Architecture Guidelines](#architecture-guidelines)
- [MCP Development](#mcp-development)
- [Release Process](#release-process)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [UV](https://github.com/astral-sh/uv) package manager
- [Claude CLI](https://claude.ai/code) installed and configured
- Git for version control
- Basic understanding of MCP (Model Context Protocol)

### Development Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nibzard/apex
   cd apex
   ```

2. **Set up virtual environment and dependencies**
   ```bash
   uv sync
   uv pip install -e ".[dev,docs]"
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Verify installation**
   ```bash
   uv run pytest --version
   uv run apex --help
   ```

5. **Run initial tests**
   ```bash
   uv run pytest
   ```

## Development Setup

### Environment Configuration

Create a `.env` file in the project root:

```env
# Claude CLI configuration
ANTHROPIC_API_KEY=your_api_key_here

# Development settings
APEX_DEBUG=true
APEX_LOG_LEVEL=debug

# Testing configuration
APEX_TEST_DB_PATH=./test_apex.db
```

### Development Scripts

```bash
# Start development environment
uv run python scripts/setup_dev.py

# Run benchmarks
uv run python scripts/run_benchmarks.py

# Build documentation
uv run mkdocs serve

# Create development database
uv run python scripts/create_test_db.py

# GitHub CLI helpers
gh repo view --web                    # Open repo in browser
gh issue list --state open           # List open issues
gh pr list --state open              # List open PRs
gh workflow list                      # List GitHub Actions workflows
```

## Code Style and Standards

### Python Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Static type checking

```bash
# Format code
uv run black src tests

# Lint and fix issues
uv run ruff check --fix src tests

# Type checking
uv run mypy src

# Run all checks
uv run pre-commit run --all-files
```

### Code Standards

1. **Type Hints**: All functions must have complete type annotations
2. **Docstrings**: Use Google-style docstrings for all public functions
3. **Error Handling**: Use appropriate exception types and meaningful messages
4. **Logging**: Use `structlog` for structured logging
5. **Async/Await**: Prefer async patterns for I/O operations

### Example Code Style

```python
import asyncio
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()

async def process_agent_events(
    agent_id: str, 
    events: List[Dict[str, Any]],
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """Process events from a specific agent.
    
    Args:
        agent_id: Unique identifier for the agent
        events: List of event dictionaries to process
        timeout: Optional timeout in seconds
        
    Returns:
        Dictionary containing processing results
        
    Raises:
        ProcessingError: If event processing fails
        TimeoutError: If operation exceeds timeout
    """
    logger.info("Processing agent events", agent_id=agent_id, count=len(events))
    
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error("Failed to process events", agent_id=agent_id, error=str(e))
        raise ProcessingError(f"Event processing failed: {e}") from e
```

## Testing

### Test Structure

```
tests/
├── unit/                 # Unit tests for individual components
├── integration/          # Integration tests for component interactions
├── e2e/                 # End-to-end tests for full workflows
├── mcp/                 # MCP compliance and server tests
└── fixtures/            # Test data and fixtures
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/

# Run with coverage
uv run pytest --cov=apex --cov-report=html --cov-report=term

# Run specific test file
uv run pytest tests/unit/test_process_manager.py

# Run specific test function
uv run pytest tests/unit/test_process_manager.py::test_start_agent

# Run tests matching pattern
uv run pytest -k "test_mcp"

# Run tests with verbose output
uv run pytest -v

# Run tests in parallel
uv run pytest -n auto
```

### Writing Tests

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test component interactions and MCP communication
3. **E2E Tests**: Test complete workflows from CLI to agent execution
4. **MCP Tests**: Validate MCP server compliance and tool functionality

Example test structure:

```python
import pytest
from unittest.mock import AsyncMock, Mock
from apex.core.process_manager import ProcessManager

class TestProcessManager:
    """Test suite for ProcessManager class."""
    
    @pytest.fixture
    async def process_manager(self):
        """Create ProcessManager instance for testing."""
        return ProcessManager(project_id="test-project")
    
    @pytest.mark.asyncio
    async def test_start_agent(self, process_manager):
        """Test agent process startup."""
        # Given
        agent_type = "coder"
        task = "Implement user authentication"
        
        # When
        process = await process_manager.start_agent(agent_type, task)
        
        # Then
        assert process is not None
        assert process.agent_type == agent_type
        assert agent_type in process_manager.processes
    
    @pytest.mark.asyncio
    async def test_start_agent_failure(self, process_manager):
        """Test agent startup failure handling."""
        # Test error conditions
        pass
```

### MCP Testing

Special considerations for testing MCP components:

```python
@pytest.mark.mcp
class TestLMDBMCPServer:
    """Test LMDB MCP server compliance."""
    
    @pytest.mark.asyncio
    async def test_tool_read_write(self, mcp_server):
        """Test basic read/write operations."""
        # Test MCP tool functionality
        pass
    
    @pytest.mark.asyncio
    async def test_mcp_compliance(self, mcp_server):
        """Test MCP protocol compliance."""
        # Validate against MCP specification
        pass
```

## Submitting Changes

### Git Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   uv run pytest
   uv run pre-commit run --all-files
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(mcp): add LMDB cursor operations
fix(cli): resolve session resume timeout issue
docs: update MCP configuration examples
test(agents): add adversary agent integration tests
```

### Pull Request Process

1. **Create descriptive PR title and description**
2. **Link related issues**
3. **Ensure all checks pass**
4. **Request review from maintainers**
5. **Address review feedback**
6. **Maintain clean commit history**

## Project Structure

Understanding the codebase organization:

```
apex/
├── src/apex/
│   ├── cli/                 # Command-line interface
│   ├── tui/                 # Terminal user interface
│   ├── core/                # Core orchestration logic
│   ├── agents/              # Agent management
│   ├── mcp/                 # MCP server implementations
│   ├── orchestration/       # Process and session management
│   ├── vcs/                 # Version control integration
│   └── utils/               # Shared utilities
├── configs/                 # MCP configuration files
├── tests/                   # Test suite
├── docs/                    # Documentation
└── scripts/                 # Development scripts
```

### Key Components

- **ProcessManager**: Manages Claude CLI processes
- **StreamParser**: Parses streaming JSON from Claude CLI
- **LMDBMCP**: MCP server for database operations
- **SessionManager**: Handles session persistence and continuation
- **AgentCoordinator**: Orchestrates agent communication

## Architecture Guidelines

### Design Principles

1. **Process Isolation**: Each agent runs in separate processes
2. **Event-Driven**: Use event streams for real-time updates
3. **State Persistence**: All state changes are persisted to LMDB
4. **MCP Integration**: All agent communication via MCP tools
5. **Error Recovery**: Graceful handling of failures with automatic recovery

### Adding New Features

When adding new features:

1. **Design MCP tools first** - Define the interface for agent communication
2. **Implement core logic** - Add business logic with proper error handling
3. **Add CLI/TUI interfaces** - Provide user-facing commands and displays
4. **Write comprehensive tests** - Cover unit, integration, and E2E scenarios
5. **Update documentation** - Include usage examples and architecture notes

### MCP Development

When working with MCP components:

1. **Follow naming conventions**: `mcp__serverName__toolName`
2. **Implement proper schemas**: Use Pydantic for request/response validation
3. **Handle errors gracefully**: Return appropriate MCP error codes
4. **Add compliance tests**: Validate against MCP specification
5. **Document tool capabilities**: Include clear descriptions and examples

Example MCP tool implementation:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.types as types

app = Server("apex-lmdb")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available LMDB tools."""
    return [
        Tool(
            name="mcp__lmdb__read",
            description="Read value from LMDB by key",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to read"}
                },
                "required": ["key"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "mcp__lmdb__read":
        key = arguments["key"]
        value = await lmdb_read(key)
        return [TextContent(type="text", text=str(value))]
    
    raise ValueError(f"Unknown tool: {name}")
```

## Release Process

### Version Management

We use semantic versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite** including MCP compliance tests
   ```bash
   uv run pytest --cov=apex
   uv run pytest tests/mcp/ -v
   ```
4. **Build and test** distribution packages
   ```bash
   uv build
   ```
5. **Create release tag** and GitHub release
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   
   # Create GitHub release
   gh release create v1.0.0 \
     --title "APEX v1.0.0" \
     --notes-file CHANGELOG.md \
     --draft
   ```
6. **Publish to PyPI** (automated via GitHub Actions)

### Pre-release Testing

Before releasing:

```bash
# Run comprehensive test suite
uv run pytest --cov=apex

# Test MCP compliance
uv run pytest tests/mcp/ -v

# Run performance benchmarks
uv run python scripts/run_benchmarks.py

# Test package building
uv build

# Test installation from wheel
pip install dist/apex-*.whl
```

## GitHub CLI Integration

APEX integrates with GitHub CLI for enhanced development workflows:

### Issue Management
```bash
# Create new issue
gh issue create --title "Bug: Agent process crashes" \
               --body "Description of the issue" \
               --label "bug,agent-system"

# List and filter issues
gh issue list --label "mcp" --state open
gh issue view 123

# Close issues from commits
git commit -m "fix: resolve agent crash issue\n\nFixes #123"
```

### Pull Request Workflow
```bash
# Create PR with template
gh pr create --template .github/pull_request_template.md

# Review PRs
gh pr checkout 456  # Checkout PR locally
gh pr diff          # View PR diff
gh pr review --approve --body "LGTM!"

# Merge PRs
gh pr merge --squash --delete-branch
```

### Release Management
```bash
# List releases
gh release list

# Create pre-release
gh release create v1.0.0-beta.1 \
  --prerelease \
  --title "APEX v1.0.0 Beta 1" \
  --notes "Beta release for testing"

# Upload release assets
gh release upload v1.0.0 dist/apex-1.0.0.tar.gz
```

### Project Management
```bash
# View project boards
gh project list --owner nibzard

# Add issue to project
gh project item-add 1 --owner nibzard --content-id 123

# View workflow runs
gh run list --workflow=ci.yml
gh run view 123456 --log
```

## Getting Help

- **Documentation**: Read [specs.md](specs.md) for detailed architecture
- **Issues**: Check existing issues or create new ones with `gh issue create`
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Maintainers provide feedback on pull requests

## Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- Documentation acknowledgments

Thank you for contributing to APEX! 🚀