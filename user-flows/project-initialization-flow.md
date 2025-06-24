# Project Initialization Flow

## Purpose
Initialize APEX in an existing project directory, adding multi-agent orchestration capabilities to your current codebase.

## Prerequisites
- Existing project directory
- Python 3.11+ installed
- UV package manager installed
- APEX installed (`uv pip install -e ".[dev]"`)

## Step-by-Step Process

### 1. Navigate to Project Directory
```bash
cd /path/to/your/existing/project
```

### 2. Initialize APEX
```bash
uv run apex init
```

**Options:**
- `--import <config.json>` - Import existing APEX configuration file

### 3. Handle Existing Configuration
If `apex.json` already exists:
- APEX will detect existing configuration
- Prompt: "APEX already initialized in this directory"
- Choose to reinitialize or cancel

### 4. Interactive Configuration

#### Basic Information:
1. **Project name** - Default: current directory name
2. **Project description** - Default: "APEX project: {project_name}"

#### Technical Details:
3. **Technologies** - Comma-separated list
   - Examples: Python, JavaScript, React, Django
   - Default: "Python"

4. **Project type** - Choose from available options:
   - CLI Tool, Web Application, API Service, Library, etc.
   - Default: "CLI Tool"

5. **Key features** - Comma-separated feature list
   - Default: "core functionality"

### 5. Alternative: Import Configuration
```bash
uv run apex init --import /path/to/existing/config.json
```

This bypasses interactive setup and uses provided configuration.

## Key Commands

```bash
# Basic initialization
uv run apex init

# Import existing configuration
uv run apex init --import ../other-project/apex.json

# Reinitialize existing project
uv run apex init  # Answer 'yes' to reinitialize prompt
```

## Expected Outcomes

### Created Files:
```
your-project/
├── apex.json          # New APEX configuration
├── .mcp.json          # Claude Code MCP setup (auto-created)
├── apex.db/           # LMDB database (created on first run)
└── [existing files]   # Your original project files remain unchanged
```

### Success Messages:
- ✓ APEX initialized successfully!
- "Run 'apex start' to begin development"

### Generated Configuration:
```json
{
  "project_id": "unique-uuid-generated",
  "name": "your-project-name",
  "description": "APEX project: your-project-name",
  "tech_stack": ["Python"],
  "project_type": "CLI Tool",
  "features": ["core functionality"],
  "created_at": "2025-01-08T12:00:00Z"
}
```

## Configuration Import Format

When using `--import`, the JSON file should contain:
```json
{
  "project_id": "optional-existing-id",
  "name": "project-name",
  "description": "Project description",
  "tech_stack": ["Technology", "List"],
  "project_type": "Project Type",
  "features": ["feature1", "feature2"],
  "created_at": "ISO-timestamp"
}
```

**Note:** If `project_id` is missing, APEX generates a new UUID.

## Integration with Existing Codebase

### APEX Preserves:
- All existing files and directories
- Git history and configuration
- Package dependencies
- Build scripts and configurations

### APEX Adds:
- `apex.json` - Project configuration
- `.mcp.json` - Claude Code MCP integration
- LMDB database for agent communication
- Agent orchestration capabilities

## Next Steps After Initialization

1. **Start agents:**
   ```bash
   uv run apex start
   ```

2. **Begin with a task:**
   ```bash
   uv run apex start --task "Analyze existing codebase and suggest improvements"
   ```

3. **Use Claude Code integration:**
   ```bash
   claude  # Automatically loads APEX MCP tools
   ```

## Common Issues

**"APEX already initialized"**
- Choose to reinitialize if you want to update configuration
- Or use existing configuration by canceling

**"Permission denied writing apex.json"**
- Check directory write permissions
- Ensure you're in the correct project directory

**"Invalid import configuration"**
- Verify JSON syntax in import file
- Check required fields are present

**"MCP setup failed"**
- Non-critical - APEX will still work
- Check Python path and APEX installation

## Related Flows
- [Project Creation Flow](project-creation-flow.md) - Creating new projects from scratch
- [Configuration Management Flow](configuration-management-flow.md) - Managing project settings
- [MCP Integration Flow](mcp-integration-flow.md) - Setting up Claude Code integration
- [Agent Management Flow](agent-management-flow.md) - Starting agents after initialization
