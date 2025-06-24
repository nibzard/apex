# Memory Management Flow

## Purpose
Browse, query, monitor, and manage APEX's shared LMDB memory system where agents store project data, tasks, code, and coordination information.

## Prerequisites
- APEX project with initialized LMDB database
- Access to CLI tools or TUI interface
- MCP integration (for direct memory access)

## Memory Architecture

### LMDB Storage Structure:
```
/projects/{project_id}/
├── /config              # Project configuration and metadata
├── /agents/             # Agent-specific data and states
│   ├── /supervisor/     # Supervisor agent data
│   ├── /coder/         # Coder agent data
│   └── /adversary/     # Adversary agent data
├── /tasks/             # Task management
│   ├── /pending/       # Pending tasks
│   ├── /in_progress/   # Active tasks
│   └── /completed/     # Finished tasks
├── /memory/            # Shared memory space
│   ├── /code/         # Source code storage
│   ├── /tests/        # Test suites
│   ├── /docs/         # Documentation
│   └── /artifacts/    # Build artifacts
├── /coordination/      # Inter-agent communication
├── /sessions/          # Session history and checkpoints
└── /notifications/     # Agent notifications
```

## Memory Access Methods

### 1. CLI Operations

#### View All Memory Keys:
```bash
uv run apex memory show
```

**Output:**
```
Memory Keys:
projects/ (15 keys)
  /projects/calc-123/config
  /projects/calc-123/tasks/pending/task-001
  ...

agents/ (8 keys)
  /agents/supervisor/status
  /agents/coder/progress
  ...

Total keys: 23
```

#### View Specific Key:
```bash
uv run apex memory show /projects/calc-123/config
```

**Output:**
```json
{
  "project_id": "calc-123",
  "name": "calculator",
  "status": "active",
  "created_at": "2025-01-08T12:00:00Z"
}
```

#### Query Memory with Patterns:
```bash
# Find all task-related keys
uv run apex memory query "*task*"

# Search content for specific terms
uv run apex memory query "authentication" --content

# Use regex patterns
uv run apex memory query "^/projects/.*/tasks" --regex
```

#### Watch Memory Changes:
```bash
# Monitor all changes
uv run apex memory watch

# Monitor specific patterns
uv run apex memory watch "/tasks/*" --timeout 60

# Monitor with custom interval
uv run apex memory watch "*" --interval 2
```

### 2. TUI Memory Browser

#### Launch TUI and Navigate to Memory:
```bash
uv run apex tui
# Press F3 or M for Memory screen
```

**TUI Features:**
- Hierarchical tree view of memory structure
- Real-time updates
- Search functionality
- Key-value editing (planned)

### 3. MCP Tools (Claude Code)

#### Direct Memory Access:
```
# Read memory data
> mcp__lmdb__read /projects/calc-123/tasks/pending/task-001

# Write memory data
> mcp__lmdb__write /projects/calc-123/notes/implementation '{
  "component": "calculator",
  "notes": "Need to add error handling for division by zero"
}'

# List keys with prefix
> mcp__lmdb__list /projects/calc-123/

# Scan key-value pairs
> mcp__lmdb__cursor_scan /tasks/ --limit 10
```

## Common Memory Operations

### 1. Project Data Management

#### View Project Configuration:
```bash
uv run apex memory show /projects/{project_id}/config
```

#### Update Project Status:
```
# Via MCP in Claude Code
> mcp__lmdb__write /projects/{project_id}/config '{
  "project_id": "calc-123",
  "name": "calculator",
  "status": "development",
  "current_phase": "implementation"
}'
```

### 2. Task Management

#### Check Pending Tasks:
```bash
uv run apex memory query "/tasks/pending/*"
```

#### Monitor Task Progress:
```bash
uv run apex memory watch "/tasks/*" --timeout 300
```

**Expected Output:**
```
+ CREATED /tasks/pending/task-005
~ MODIFIED /tasks/in_progress/task-003
- DELETED /tasks/pending/task-002
```

#### Create New Task:
```
> mcp__lmdb__write /projects/{id}/tasks/pending/new-task '{
  "description": "Add input validation",
  "assigned_to": "coder",
  "priority": "medium",
  "created_at": "2025-01-08T14:30:00Z"
}'
```

### 3. Code Storage and Retrieval

#### Store Code Implementation:
```
> mcp__lmdb__write /projects/{id}/memory/code/calculator.py '{
  "file_path": "src/calculator.py",
  "content": "class Calculator:\\n    def add(self, a, b):\\n        return a + b",
  "version": "1.0",
  "author": "coder_agent"
}'
```

#### Retrieve Code:
```bash
uv run apex memory show /projects/{id}/memory/code/calculator.py
```

### 4. Agent Coordination

#### Check Agent Status:
```bash
uv run apex memory query "/agents/*/status"
```

#### Send Agent Notification:
```
> mcp__lmdb__write /projects/{id}/notifications/coder '{
  "from": "supervisor",
  "message": "New high priority task assigned",
  "task_id": "task-007",
  "timestamp": "2025-01-08T15:00:00Z"
}'
```

## Memory Monitoring Workflows

### 1. Development Monitoring

#### Active Development Session:
```bash
# Terminal 1: Watch task changes
uv run apex memory watch "/tasks/*"

# Terminal 2: Watch code changes
uv run apex memory watch "/memory/code/*"

# Terminal 3: Monitor agent coordination
uv run apex memory watch "/coordination/*"
```

### 2. Debugging Memory Issues

#### Find Recent Changes:
```bash
# Look for error messages
uv run apex memory query "*error*" --content

# Check recent task failures
uv run apex memory query "/tasks/failed/*"

# Monitor agent status
uv run apex memory show /agents/coder/status
```

#### Investigate Performance Issues:
```bash
# Check memory usage
uv run apex memory query "*" --limit 1000 | wc -l

# Look for large data entries
uv run apex memory scan / --limit 50

# Monitor database growth
watch -n 5 'du -sh apex.db'
```

### 3. Project Health Monitoring

#### Daily Health Check:
```bash
# Check project status
uv run apex memory show /projects/{id}/config

# Verify agent coordination
uv run apex memory query "/agents/*/last_seen"

# Check for pending issues
uv run apex memory query "/issues/*" --content
```

## Memory Maintenance

### 1. Cleanup Operations

#### Archive Completed Tasks:
```
# Move completed tasks to archive
> mcp__lmdb__write /projects/{id}/archive/tasks/completed-batch-1 '{
  "archived_at": "2025-01-08T16:00:00Z",
  "task_count": 15,
  "date_range": "2025-01-01 to 2025-01-07"
}'

# Remove from active space
> mcp__lmdb__delete /projects/{id}/tasks/completed/task-001
```

#### Clean Temporary Data:
```bash
# Remove temporary coordination messages
uv run apex memory query "/coordination/temp/*" --limit 100 | xargs -I {} uv run apex memory delete {}
```

### 2. Backup and Restore

#### Backup Memory State:
```bash
# Export all project data
uv run apex memory query "/projects/{id}/*" > project_backup.json

# Export specific namespace
uv run apex memory query "/tasks/*" > tasks_backup.json
```

#### Restore Memory State:
```
# Restore from backup (custom script needed)
# Parse JSON and restore with mcp__lmdb__write
```

## Advanced Memory Operations

### 1. Bulk Operations

#### Batch Task Updates:
```bash
# Update all pending tasks with new priority
for task in $(uv run apex memory query "/tasks/pending/*"); do
  # Update task priority logic here
done
```

#### Mass Data Migration:
```
# Migrate data structure
> mcp__lmdb__cursor_scan /old_structure/ --limit 1000
# Process and write to new structure
> mcp__lmdb__write /new_structure/migrated_data '{...}'
```

### 2. Memory Analysis

#### Data Size Analysis:
```bash
# Find largest memory entries
uv run apex memory scan / --limit 1000 | sort -k2 -n

# Memory usage by namespace
uv run apex memory query "/projects/*" | wc -l
uv run apex memory query "/tasks/*" | wc -l
uv run apex memory query "/agents/*" | wc -l
```

#### Access Pattern Analysis:
```bash
# Monitor most frequently accessed keys
uv run apex memory watch "*" --timeout 3600 | grep "READ" | sort | uniq -c | sort -nr
```

## Data Format Guidelines

### Standard JSON Structure:
```json
{
  "id": "unique-identifier",
  "type": "data-type",
  "content": "actual-data",
  "metadata": {
    "created_at": "ISO-timestamp",
    "created_by": "agent-name",
    "version": "1.0"
  }
}
```

### Task Data Format:
```json
{
  "task_id": "uuid",
  "description": "Human readable description",
  "assigned_to": "agent-name",
  "status": "pending|in_progress|completed|failed",
  "priority": "low|medium|high",
  "created_at": "ISO-timestamp",
  "dependencies": ["task-id1", "task-id2"]
}
```

### Code Storage Format:
```json
{
  "file_path": "relative/path/to/file.py",
  "content": "file-content-as-string",
  "language": "python",
  "version": "1.2.3",
  "metadata": {
    "author": "agent-name",
    "last_modified": "ISO-timestamp",
    "description": "Brief description of changes"
  }
}
```

## Troubleshooting Memory Issues

### Database Corruption:
```bash
# Check database integrity
APEX_LMDB_PATH="./apex.db" python -c "
from apex.core.lmdb_mcp import LMDBMCP
db = LMDBMCP('./apex.db')
print('Database accessible:', db.read('/') is not None)
"
```

### Memory Growth Issues:
```bash
# Monitor database size
watch -n 10 'du -sh apex.db && echo "Keys:" && uv run apex memory query "*" | wc -l'

# Find large entries
uv run apex memory scan / --limit 100 | sort -k2 -nr | head -20
```

### Access Performance:
```bash
# Test read performance
time uv run apex memory show /projects/{id}/config

# Test write performance
time uv run apex memory write /test/performance "test data"
```

## Related Flows
- [MCP Integration Flow](mcp-integration-flow.md) - Using MCP tools for memory access
- [Task Workflow Flow](task-workflow-flow.md) - Task data in memory
- [Claude Multi-Instance Flow](claude-multi-instance-flow.md) - Shared memory coordination
- [TUI Navigation Flow](tui-navigation-flow.md) - Memory browser interface
