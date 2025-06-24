# Configuration Management Flow

## Purpose
Manage APEX project configurations, system settings, MCP server configurations, and agent behavior parameters for optimal multi-agent development workflows.

## Prerequisites
- APEX project initialized
- Understanding of APEX architecture
- Basic knowledge of JSON configuration formats

## Configuration Overview

### Configuration Types:
- **Project Configuration** - `apex.json` project settings
- **MCP Configuration** - `.mcp.json` Claude Code integration
- **Agent Configuration** - Agent behavior and prompts
- **System Configuration** - APEX runtime settings
- **Environment Configuration** - Environment variables and paths

## Project Configuration

### 1. Primary Configuration File (apex.json)

#### Standard Configuration Structure:
```json
{
  "project_id": "unique-project-uuid",
  "name": "my-calculator",
  "description": "A calculator application with multi-agent development",
  "tech_stack": ["Python", "CLI", "Pytest"],
  "project_type": "CLI Tool",
  "features": ["arithmetic", "testing", "error-handling"],
  "created_at": "2025-01-08T12:00:00Z",
  "version": "1.0.0",
  "apex_version": "0.1.0"
}
```

#### Edit Project Configuration:
```bash
# View current configuration
uv run apex memory show /projects/{project_id}/config

# Edit configuration file
vim apex.json

# Validate configuration
uv run apex config validate

# Reload configuration
uv run apex config reload
```

### 2. Extended Configuration Options

#### Advanced Project Settings:
```json
{
  "project_id": "uuid",
  "name": "api-service",
  "description": "REST API with authentication",
  "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "project_type": "API Service",
  "features": ["authentication", "crud-operations", "rate-limiting"],
  "settings": {
    "code_style": "black",
    "test_framework": "pytest",
    "documentation": "sphinx",
    "ci_cd": "github-actions"
  },
  "agent_config": {
    "supervisor": {
      "planning_style": "agile",
      "review_frequency": "per_task"
    },
    "coder": {
      "coding_style": "pep8",
      "test_driven": true,
      "documentation_level": "detailed"
    },
    "adversary": {
      "security_focus": "high",
      "test_coverage_threshold": 90,
      "performance_testing": true
    }
  }
}
```

## MCP Configuration

### 1. Claude Code Integration (.mcp.json)

#### Standard MCP Configuration:
```json
{
  "mcpServers": {
    "apex-lmdb": {
      "command": "python",
      "args": ["-m", "apex.mcp"],
      "env": {
        "APEX_LMDB_PATH": "./apex.db",
        "APEX_LMDB_MAP_SIZE": "1073741824"
      }
    }
  }
}
```

#### Advanced MCP Configuration:
```json
{
  "mcpServers": {
    "apex-lmdb": {
      "command": "uv",
      "args": ["run", "python", "-m", "apex.mcp"],
      "env": {
        "APEX_LMDB_PATH": "./apex_shared.db",
        "APEX_LMDB_MAP_SIZE": "2147483648",
        "APEX_LOG_LEVEL": "debug",
        "APEX_MCP_TIMEOUT": "30",
        "APEX_PROJECT_ID": "my-project-uuid"
      }
    },
    "apex-git": {
      "command": "python",
      "args": ["-m", "apex.mcp.git"],
      "env": {
        "GIT_REPO_PATH": ".",
        "GIT_AUTO_COMMIT": "true"
      }
    }
  }
}
```

### 2. MCP Configuration Management

#### Validate MCP Setup:
```bash
# Test MCP server connectivity
APEX_LMDB_PATH="./apex.db" uv run python -m apex.mcp --test

# Validate MCP configuration
claude mcp list | grep apex

# Reset MCP configuration
claude mcp restart
```

## Agent Configuration

### 1. Agent Behavior Settings

#### Supervisor Agent Configuration:
```json
{
  "supervisor_config": {
    "planning": {
      "methodology": "agile",
      "task_breakdown_depth": 3,
      "parallel_tasks_limit": 5,
      "review_frequency": "per_milestone"
    },
    "coordination": {
      "check_interval": 300,
      "escalation_threshold": 3,
      "auto_assignment": true
    },
    "git_integration": {
      "auto_commit": true,
      "branch_strategy": "feature",
      "pr_creation": "auto"
    }
  }
}
```

#### Coder Agent Configuration:
```json
{
  "coder_config": {
    "development": {
      "coding_standards": "pep8",
      "test_driven_development": true,
      "documentation_style": "sphinx",
      "code_review_self": true
    },
    "implementation": {
      "prefer_composition": true,
      "error_handling": "comprehensive",
      "logging_level": "info",
      "performance_focus": "medium"
    },
    "quality": {
      "run_tests_before_commit": true,
      "code_coverage_threshold": 80,
      "lint_enforcement": true
    }
  }
}
```

#### Adversary Agent Configuration:
```json
{
  "adversary_config": {
    "security": {
      "threat_modeling": true,
      "vulnerability_scanning": "comprehensive",
      "penetration_testing": "basic",
      "security_review_depth": "thorough"
    },
    "testing": {
      "edge_case_focus": "high",
      "negative_testing": true,
      "performance_testing": true,
      "integration_testing": true
    },
    "review": {
      "code_review_strictness": "high",
      "documentation_review": true,
      "architecture_review": true
    }
  }
}
```

### 2. Store Agent Configuration:
```bash
# Store agent configurations in memory
uv run apex memory write /config/agents/supervisor "$(cat supervisor_config.json)"
uv run apex memory write /config/agents/coder "$(cat coder_config.json)"
uv run apex memory write /config/agents/adversary "$(cat adversary_config.json)"
```

## System Configuration

### 1. APEX Runtime Settings

#### System Configuration File:
```json
{
  "system_config": {
    "database": {
      "type": "lmdb",
      "path": "./apex.db",
      "map_size": "1073741824",
      "auto_backup": true,
      "backup_interval": 3600
    },
    "processing": {
      "max_concurrent_agents": 3,
      "task_timeout": 1800,
      "retry_attempts": 3,
      "health_check_interval": 60
    },
    "communication": {
      "mcp_timeout": 30,
      "agent_polling_interval": 5,
      "coordination_channel": "/coordination",
      "notification_system": true
    },
    "logging": {
      "level": "info",
      "file_rotation": true,
      "max_log_size": "100MB",
      "retention_days": 30
    }
  }
}
```

### 2. Environment Configuration

#### Environment Variables:
```bash
# Core APEX settings
export APEX_LMDB_PATH="./apex.db"
export APEX_LMDB_MAP_SIZE="1073741824"
export APEX_LOG_LEVEL="info"
export APEX_PROJECT_ID="my-project-uuid"

# MCP settings
export APEX_MCP_TIMEOUT="30"
export APEX_MCP_DEBUG="false"

# Agent settings
export APEX_MAX_AGENTS="3"
export APEX_TASK_TIMEOUT="1800"

# Development settings
export APEX_DEBUG_MODE="false"
export APEX_PROFILE_PERFORMANCE="false"
```

#### Environment Configuration File (.env):
```bash
# APEX Environment Configuration
APEX_LMDB_PATH=./apex.db
APEX_LMDB_MAP_SIZE=1073741824
APEX_LOG_LEVEL=info
APEX_PROJECT_ID=my-project-uuid
APEX_MCP_TIMEOUT=30
APEX_MAX_AGENTS=3
APEX_TASK_TIMEOUT=1800
```

## Configuration Workflows

### 1. Project Setup Configuration

#### Initial Configuration Workflow:
```bash
# 1. Create project with specific settings
uv run apex new my-api --tech "Python,FastAPI" --template api-starter

# 2. Customize project configuration
vim apex.json

# 3. Configure agent behavior
vim config/agents.json

# 4. Set up environment
cp .env.example .env
vim .env

# 5. Validate complete configuration
uv run apex config validate --all
```

### 2. Configuration Updates

#### Update Project Settings:
```bash
# Backup current configuration
cp apex.json apex.json.backup

# Update configuration
vim apex.json

# Validate changes
uv run apex config validate

# Apply changes (restart agents if needed)
uv run apex config reload
```

#### Live Configuration Updates:
```bash
# Update agent configuration in memory
uv run apex memory write /config/agents/coder '{
  "development": {
    "test_driven_development": false,
    "documentation_style": "minimal"
  }
}'

# Notify agents of configuration change
uv run apex memory write /notifications/config_update '{
  "type": "config_change",
  "scope": "coder_agent",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'
```

## Configuration Templates

### 1. Project Type Templates

#### Web Application Template:
```json
{
  "name": "web-app",
  "tech_stack": ["JavaScript", "React", "Node.js", "PostgreSQL"],
  "project_type": "Web Application",
  "features": ["frontend", "backend", "database", "authentication"],
  "agent_config": {
    "supervisor": {"planning_style": "sprint"},
    "coder": {"frontend_focus": true, "api_design": true},
    "adversary": {"ui_testing": true, "api_security": true}
  }
}
```

#### API Service Template:
```json
{
  "name": "api-service",
  "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "project_type": "API Service",
  "features": ["rest-api", "authentication", "database", "documentation"],
  "agent_config": {
    "supervisor": {"api_design_review": true},
    "coder": {"api_standards": "openapi", "database_design": true},
    "adversary": {"api_security": "comprehensive", "load_testing": true}
  }
}
```

### 2. Configuration Presets

#### Development Environment Preset:
```json
{
  "preset": "development",
  "settings": {
    "logging": {"level": "debug"},
    "testing": {"auto_run": true},
    "debugging": {"enabled": true},
    "performance": {"profiling": true}
  }
}
```

#### Production Environment Preset:
```json
{
  "preset": "production",
  "settings": {
    "logging": {"level": "warn"},
    "testing": {"comprehensive": true},
    "security": {"strict": true},
    "performance": {"optimized": true}
  }
}
```

## Configuration Validation

### 1. Validation Commands

#### Validate All Configurations:
```bash
# Validate project configuration
uv run apex config validate --project

# Validate MCP configuration
uv run apex config validate --mcp

# Validate agent configurations
uv run apex config validate --agents

# Validate complete setup
uv run apex config validate --all
```

### 2. Configuration Health Checks

#### Automated Health Check:
```bash
#!/bin/bash
# config_health_check.sh

echo "=== APEX Configuration Health Check ==="

# Check project configuration
if uv run apex config validate --project; then
  echo "✓ Project configuration valid"
else
  echo "✗ Project configuration invalid"
fi

# Check MCP connectivity
if claude mcp list | grep -q apex; then
  echo "✓ MCP integration working"
else
  echo "✗ MCP integration failed"
fi

# Check agent configurations
for agent in supervisor coder adversary; do
  if uv run apex memory show /config/agents/$agent > /dev/null 2>&1; then
    echo "✓ $agent configuration accessible"
  else
    echo "✗ $agent configuration missing"
  fi
done

# Check environment
if [ -n "$APEX_PROJECT_ID" ]; then
  echo "✓ Environment configured"
else
  echo "✗ Environment not configured"
fi
```

## Configuration Best Practices

### 1. Version Control
- Store `apex.json` in version control
- Keep environment-specific settings in `.env` (not in VCS)
- Document configuration changes in commit messages

### 2. Environment Management
- Use different configurations for dev/staging/production
- Validate configurations before deployment
- Backup configurations before major changes

### 3. Agent Tuning
- Start with default agent configurations
- Gradually customize based on project needs
- Monitor agent performance after configuration changes

## Troubleshooting Configuration

### Common Issues:

**"Configuration validation failed"**
```bash
# Check JSON syntax
python -m json.tool apex.json

# Validate required fields
uv run apex config validate --verbose
```

**"MCP server not connecting"**
```bash
# Check MCP configuration
cat .mcp.json

# Test MCP server manually
APEX_LMDB_PATH="./apex.db" uv run python -m apex.mcp
```

**"Agent behavior not updating"**
```bash
# Restart agents with new configuration
uv run apex stop && uv run apex start

# Check configuration in memory
uv run apex memory show /config/agents/supervisor
```

## Related Flows
- [Project Creation Flow](project-creation-flow.md) - Initial configuration setup
- [MCP Integration Flow](mcp-integration-flow.md) - MCP configuration details
- [Agent Management Flow](agent-management-flow.md) - Agent configuration application
- [Memory Management Flow](memory-management-flow.md) - Configuration storage
