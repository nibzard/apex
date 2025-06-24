# Project Creation Flow

## Purpose
Create a new APEX project from scratch with automatic MCP integration and optional git initialization.

## Prerequisites
- Python 3.11+ installed
- UV package manager installed
- APEX installed (`uv pip install -e ".[dev]"`)
- Claude CLI installed and configured (optional but recommended)

## Step-by-Step Process

### 1. Create New Project
```bash
uv run apex new <project_name>
```

**Options:**
- `--template <name>` - Use a specific project template
- `--tech <stack>` - Specify technology stack (comma-separated)
- `--no-git` - Skip git repository initialization

### 2. Interactive Setup
When prompted, provide:

1. **Project description** - Brief description of your project
   - Default: "A new {project_name} project"

2. **Technology stack** - Technologies you'll use
   - Examples: Python, JavaScript, TypeScript, React, Flask, Django
   - Default: "Python"

3. **Project type** - Choose from:
   - Web Application
   - API Service
   - CLI Tool
   - Library
   - Data Pipeline
   - Other

4. **Key features** - Comma-separated list of main features
   - Default: "core functionality"

### 3. Automatic Setup
APEX will automatically:

1. **Create project directory** at `<project_name>/`
2. **Generate configuration** file `apex.json`
3. **Initialize git repository** (unless `--no-git` specified)
4. **Set up MCP configuration** for Claude Code integration
5. **Create LMDB database** structure
6. **Set up development container** configuration (optional)

### 4. Development Container Setup (Recommended)
For isolated development environment:

```bash
# Create with devcontainer support
uv run apex new my-project --devcontainer

# Or add to existing project
cd my-project
uv run apex init --devcontainer
```

**Devcontainer includes:**
- Claude Code pre-installed and configured
- LMDB MCP server ready to run
- Multi-agent container orchestration
- VS Code development environment

## Key Commands

```bash
# Basic project creation
uv run apex new my-calculator

# With specific tech stack
uv run apex new todo-api --tech "Python,FastAPI,SQLAlchemy"

# Skip git initialization
uv run apex new library-project --no-git

# Use template (when available)
uv run apex new web-app --template react-starter
```

## Expected Outcomes

### Created Files:
```
my-project/
├── apex.json          # Project configuration
├── .git/              # Git repository (if not skipped)
├── .mcp.json          # Claude Code MCP configuration (auto-created)
├── .devcontainer/     # Development container setup (if enabled)
│   ├── devcontainer.json
│   ├── docker-compose.yml
│   └── Dockerfile*
└── apex.db/           # LMDB database (created on first run)
```

### Success Messages:
- ✓ Created project configuration
- ✓ Initialized git repository
- ✓ Configured Claude Code MCP integration
- ✓ Project 'my-project' created successfully!

### Next Steps Displayed:
```bash
cd my-project
apex start --task "Your initial task here"
claude  # Start Claude Code with APEX integration
```

## Configuration Details

### apex.json Structure:
```json
{
  "project_id": "unique-uuid",
  "name": "my-calculator",
  "description": "A simple calculator application",
  "tech_stack": ["Python", "CLI"],
  "project_type": "CLI Tool",
  "features": ["arithmetic", "testing", "cli"],
  "created_at": "2025-01-08T12:00:00Z"
}
```

### .mcp.json Structure:
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

### Devcontainer Quick Start:
```bash
# Open project in VS Code with devcontainer
cd my-project
code .  # VS Code will prompt to "Reopen in Container"

# Or use Docker Compose directly
docker-compose -f .devcontainer/docker-compose.yml up
```

## Common Issues

**"Directory already exists"**
- Choose a different project name or remove the existing directory

**"Git initialization failed"**
- Ensure git is installed and configured
- Use `--no-git` flag to skip git setup

**"MCP configuration failed"**
- Check Python and APEX module accessibility
- MCP setup is optional - project will still work

## Related Flows
- [Project Initialization Flow](project-initialization-flow.md) - Initialize APEX in existing projects
- [MCP Integration Flow](mcp-integration-flow.md) - Detailed Claude Code integration
- [CLI Operations Flow](cli-operations-flow.md) - All APEX commands
- [Agent Management Flow](agent-management-flow.md) - Starting agents after creation
