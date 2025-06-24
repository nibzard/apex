# APEX Development Container

This directory contains the complete development container setup for APEX, designed for isolated multi-agent execution with Claude Code integration.

## Quick Start

1. **Open in VS Code with Dev Containers extension**
   ```bash
   code .
   # VS Code will prompt to "Reopen in Container"
   ```

2. **Start LMDB server and agents**
   ```bash
   docker-compose up lmdb-server supervisor-agent coder-agent adversary-agent
   ```

3. **Access development environment**
   ```bash
   # Main development container
   docker-compose exec apex-dev bash

   # Individual agent containers
   docker-compose exec supervisor-agent bash
   docker-compose exec coder-agent bash
   docker-compose exec adversary-agent bash
   ```

## Container Architecture

### Development Container (`apex-dev`)
- **Purpose**: Main development environment with VS Code integration
- **Features**:
  - Claude Code pre-installed
  - Full APEX development environment
  - Python toolchain (UV, pytest, black, ruff, mypy)
  - Git and GitHub CLI
- **Ports**: 8000 (LMDB), 8001 (TUI), 8002 (Monitoring)

### LMDB Server Container (`lmdb-server`)
- **Purpose**: Shared LMDB MCP server for agent coordination
- **Features**:
  - High-performance LMDB database
  - MCP protocol compliance
  - Health checks and auto-restart
- **Port**: 8000

### Agent Containers
- **supervisor-agent**: Task coordination and git operations
- **coder-agent**: Code implementation and file operations
- **adversary-agent**: Testing, security, and quality assurance

Each agent container:
- Isolated execution environment
- Claude Code with agent-specific tool permissions
- Shared LMDB access for coordination
- Automatic restart on failure

## Configuration Files

### `devcontainer.json`
- VS Code development container configuration
- Extensions, settings, and port forwarding
- Environment variables and volume mounts

### `docker-compose.yml`
- Multi-container orchestration
- Service dependencies and networking
- Volume management and health checks

### `Dockerfile`
- Base development container image
- Claude Code, Python, and toolchain setup
- User configuration and permissions

### `Dockerfile.agent`
- Optimized agent container image
- Minimal dependencies for Claude Code execution
- Agent-specific configuration

### `setup.sh`
- Automated development environment setup
- LMDB initialization and MCP configuration
- Development tooling and aliases

## Development Workflow

### 1. Container Development
```bash
# Start development environment
docker-compose up apex-dev

# Access development shell
docker-compose exec apex-dev bash

# Run APEX commands
apex new myproject
apex start
apex tui
```

### 2. Agent Testing
```bash
# Start individual agents for testing
docker-compose up lmdb-server
docker-compose up supervisor-agent
docker-compose up coder-agent
docker-compose up adversary-agent

# Monitor agent logs
docker-compose logs -f supervisor-agent
docker-compose logs -f coder-agent
docker-compose logs -f adversary-agent
```

### 3. LMDB Monitoring
```bash
# Access LMDB directly
docker-compose exec apex-dev python -c "
import apex.core.memory
apex.core.memory.inspect_database()
"

# Query LMDB via MCP tools
docker-compose exec apex-dev claude -p 'List all keys in LMDB' \
  --mcp-config /workspace/.apex/mcp-config.json \
  --allowedTools mcp__lmdb__list
```

## Environment Variables

### Global Configuration
- `APEX_ENVIRONMENT`: Development environment (default: `development`)
- `APEX_LMDB_PATH`: Path to LMDB database
- `APEX_LMDB_MAP_SIZE`: Maximum LMDB database size
- `ANTHROPIC_API_KEY`: Claude API key (required)

### Agent-Specific
- `APEX_AGENT_TYPE`: Agent type (supervisor/coder/adversary)
- `MCP_SERVER_HOST`: LMDB server hostname
- `MCP_SERVER_PORT`: LMDB server port

## Volumes

### Persistent Data
- `apex-lmdb-data`: LMDB database files (shared across containers)
- `apex-agent-logs`: Agent execution logs

### Development Mounts
- `../:/workspace:cached`: Source code (bind mount for live editing)
- `/var/run/docker.sock`: Docker socket (for container management)

## Network Configuration

All containers share the `apex-network` bridge network for inter-container communication:

- **lmdb-server**: Accessible at `lmdb-server:8000`
- **Agent containers**: Connect to LMDB via network
- **Port forwarding**: Development ports exposed to host

## Security Features

### Container Isolation
- Each agent runs in its own isolated container
- Resource limits and process isolation
- Network segmentation between services

### Tool Permissions
- Agent-specific tool allowlists
- MCP tool namespacing (`mcp__lmdb__*`)
- Controlled file system access

### Data Protection
- Volume-based persistent storage
- Environment variable injection
- Secure API key handling

## Troubleshooting

### Container Issues
```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs <service-name>

# Restart services
docker-compose restart <service-name>

# Rebuild containers
docker-compose build --no-cache
```

### LMDB Issues
```bash
# Check LMDB server health
docker-compose exec lmdb-server python -c "
import socket
socket.create_connection(('localhost', 8000), timeout=5)
print('LMDB server is healthy')
"

# Reset LMDB database
docker-compose down
docker volume rm apex_apex-lmdb-data
docker-compose up lmdb-server
```

### Agent Issues
```bash
# Check Claude Code installation
docker-compose exec supervisor-agent claude --version

# Test MCP connectivity
docker-compose exec supervisor-agent python -c "
import json
with open('/workspace/.apex/mcp-config.json') as f:
    config = json.load(f)
print('MCP config loaded successfully')
"

# Restart agent
docker-compose restart supervisor-agent
```

## Performance Optimization

### Resource Allocation
- Adjust container memory limits in `docker-compose.yml`
- Monitor resource usage with `docker stats`
- Scale agent containers based on workload

### LMDB Performance
- Tune `APEX_LMDB_MAP_SIZE` for your dataset
- Monitor LMDB database size and performance
- Use SSD storage for optimal performance

### Network Optimization
- Use host networking for development if needed
- Monitor inter-container communication latency
- Optimize MCP tool usage patterns

This development container setup provides a complete, isolated environment for APEX development with full Claude Code integration and multi-agent orchestration capabilities.
