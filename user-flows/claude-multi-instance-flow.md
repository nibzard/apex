# Claude Multi-Instance Flow

## Purpose
Run multiple Claude Code instances simultaneously in the same APEX project, enabling true multi-agent development with each instance playing a different role (Supervisor, Coder, Adversary).

## Prerequisites
- Claude CLI installed and configured
- APEX project with MCP integration enabled
- Multiple terminal windows/tabs
- Sufficient system resources for concurrent instances

## Multi-Instance Architecture

### Flow Overview:
```
┌─ Terminal 1 ─────────┐    ┌─ Terminal 2 ─────────┐    ┌─ Terminal 3 ─────────┐
│ Supervisor Agent     │    │ Coder Agent          │    │ Adversary Agent      │
│ claude --prompt="..." │    │ claude --prompt="..." │    │ claude --prompt="..." │
│                      │    │                      │    │                      │
│ Plans & Coordinates  │    │ Implements Solutions │    │ Reviews & Tests      │
└──────────┬───────────┘    └──────────┬───────────┘    └──────────┬───────────┘
           │                           │                           │
           └─────────────────┬─────────────────┬─────────────────┘
                             │                 │
                    ┌────────▼─────────────────▼────────┐
                    │      APEX MCP Server              │
                    │   (Shared LMDB Database)          │
                    └───────────────────────────────────┘
```

## Step-by-Step Setup

### 1. Prepare APEX Project
```bash
# Create or enter existing project
cd my-project

# Verify MCP configuration exists
ls -la .mcp.json

# Optionally start APEX orchestration (for monitoring)
uv run apex start &
```

### 2. Launch Supervisor Agent (Terminal 1)
```bash
cd my-project
claude --prompt "You are the SUPERVISOR AGENT for this APEX project. Your responsibilities:

1. Break down user requests into specific tasks
2. Assign tasks to Coder and Adversary agents via APEX MCP tools
3. Monitor project progress and coordinate workflow
4. Handle git operations and project management
5. Use these APEX MCP tools for coordination:
   - mcp__lmdb__write: Create tasks and assign work
   - mcp__lmdb__read: Check project status and agent progress
   - mcp__lmdb__list: Monitor task queues and completion
   - mcp__lmdb__project_status: Get overall project overview

Always coordinate through the shared LMDB memory using MCP tools."
```

### 3. Launch Coder Agent (Terminal 2)
```bash
cd my-project
claude --prompt "You are the CODER AGENT for this APEX project. Your responsibilities:

1. Check for assigned tasks using APEX MCP tools
2. Implement features, fix bugs, and write clean code
3. Update task status as you work
4. Store code and implementation details in shared memory
5. Use these APEX MCP tools:
   - mcp__lmdb__read: Check for assigned tasks
   - mcp__lmdb__write: Update task progress and store results
   - mcp__lmdb__list: Monitor your task queue

Focus on implementation and code quality. Coordinate with other agents through shared memory."
```

### 4. Launch Adversary Agent (Terminal 3)
```bash
cd my-project
claude --prompt "You are the ADVERSARY AGENT for this APEX project. Your responsibilities:

1. Review completed implementations for security and quality
2. Find bugs, vulnerabilities, and edge cases
3. Create comprehensive tests
4. Challenge assumptions and implementation decisions
5. Use these APEX MCP tools:
   - mcp__lmdb__read: Review completed work and implementation
   - mcp__lmdb__write: Report issues and test results
   - mcp__lmdb__list: Monitor completed tasks ready for review

Be thorough and critical. Your job is to improve code quality through rigorous testing and review."
```

## Agent Coordination Workflow

### 1. Initial Project Setup

#### Supervisor Initializes Project:
```
Supervisor> I need to set up the project structure and create initial tasks.

> mcp__lmdb__project_status {project-id}

> mcp__lmdb__write /projects/{id}/config '{
  "status": "active",
  "current_phase": "planning",
  "agents": ["supervisor", "coder", "adversary"],
  "coordination_channel": "/projects/{id}/coordination"
}'
```

### 2. Task Assignment Workflow

#### Supervisor Creates Tasks:
```
Supervisor> Let me break down the user request "Create a REST API for user management" into tasks.

> mcp__lmdb__write /projects/{id}/tasks/task-001 '{
  "description": "Design user data model and database schema",
  "assigned_to": "coder",
  "priority": "high",
  "status": "pending",
  "dependencies": [],
  "created_by": "supervisor"
}'

> mcp__lmdb__write /projects/{id}/tasks/task-002 '{
  "description": "Implement user registration endpoint",
  "assigned_to": "coder",
  "priority": "high",
  "status": "pending",
  "dependencies": ["task-001"],
  "created_by": "supervisor"
}'

> mcp__lmdb__write /projects/{id}/tasks/task-003 '{
  "description": "Review registration endpoint for security vulnerabilities",
  "assigned_to": "adversary",
  "priority": "medium",
  "status": "pending",
  "dependencies": ["task-002"],
  "created_by": "supervisor"
}'
```

### 3. Coder Implementation Workflow

#### Coder Checks for Tasks:
```
Coder> Let me check what tasks are assigned to me.

> mcp__lmdb__list /projects/{id}/tasks/

> mcp__lmdb__cursor_scan /projects/{id}/tasks/ --filter assigned_to=coder,status=pending

I see task-001: "Design user data model and database schema". Let me work on this.
```

#### Coder Updates Progress:
```
Coder> I'm starting work on the user data model.

> mcp__lmdb__write /projects/{id}/tasks/task-001 '{
  "description": "Design user data model and database schema",
  "assigned_to": "coder",
  "status": "in_progress",
  "progress": "Started analyzing requirements",
  "updated_by": "coder"
}'
```

#### Coder Completes Task:
```
Coder> I've completed the user data model design.

> mcp__lmdb__write /projects/{id}/tasks/task-001 '{
  "description": "Design user data model and database schema",
  "assigned_to": "coder",
  "status": "completed",
  "result": {
    "files_created": ["models/user.py", "database/schema.sql"],
    "description": "Created User model with fields: id, username, email, password_hash, created_at, updated_at"
  },
  "completed_by": "coder"
}'

> mcp__lmdb__write /projects/{id}/code/user_model '{
  "file": "models/user.py",
  "content": "class User(db.Model): ...",
  "status": "completed"
}'
```

### 4. Adversary Review Workflow

#### Adversary Monitors Completed Work:
```
Adversary> Let me check for completed implementations to review.

> mcp__lmdb__cursor_scan /projects/{id}/tasks/ --filter status=completed

I see task-002 is completed. Let me review the registration endpoint implementation.

> mcp__lmdb__read /projects/{id}/code/registration_endpoint
```

#### Adversary Reports Issues:
```
Adversary> I found several security issues in the registration endpoint.

> mcp__lmdb__write /projects/{id}/issues/security-001 '{
  "title": "Password validation insufficient",
  "description": "Registration endpoint accepts weak passwords",
  "severity": "high",
  "affected_task": "task-002",
  "recommended_fix": "Implement strong password requirements",
  "reported_by": "adversary"
}'

> mcp__lmdb__write /projects/{id}/tasks/task-004 '{
  "description": "Fix password validation security issue",
  "assigned_to": "coder",
  "priority": "high",
  "status": "pending",
  "related_issue": "security-001",
  "created_by": "adversary"
}'
```

## Communication Patterns

### 1. Notification System
Agents can create notifications for each other:

```
> mcp__lmdb__write /projects/{id}/notifications/coder '{
  "from": "supervisor",
  "message": "High priority task assigned: task-005",
  "timestamp": "2025-01-08T14:30:00Z"
}'
```

### 2. Status Updates
Regular status updates help coordinate work:

```
> mcp__lmdb__write /projects/{id}/status/daily-standup '{
  "date": "2025-01-08",
  "supervisor": "Created 3 new tasks, blocked on client feedback",
  "coder": "Completed user authentication, working on API endpoints",
  "adversary": "Found 2 security issues, created tests for auth module"
}'
```

### 3. Coordination Channel
Use a shared coordination space for announcements:

```
> mcp__lmdb__write /projects/{id}/coordination/announcement-001 '{
  "type": "announcement",
  "from": "supervisor",
  "message": "Switching to sprint planning mode - all agents please focus on task-priority-review",
  "timestamp": "2025-01-08T15:00:00Z"
}'
```

## Memory Organization for Multi-Instance

### Agent-Specific Namespaces:
```
/projects/{id}/
├── /agents/
│   ├── /supervisor/
│   │   ├── /inbox/          # Messages to supervisor
│   │   ├── /status/         # Supervisor status updates
│   │   └── /decisions/      # Planning decisions
│   ├── /coder/
│   │   ├── /inbox/          # Messages to coder
│   │   ├── /progress/       # Implementation progress
│   │   └── /implementations/ # Code implementations
│   └── /adversary/
│       ├── /inbox/          # Messages to adversary
│       ├── /reviews/        # Code review results
│       └── /issues/         # Found issues and bugs
```

### Shared Coordination Spaces:
```
/projects/{id}/
├── /coordination/           # Inter-agent communication
├── /tasks/                  # Task management
├── /issues/                 # Bug reports and issues
├── /notifications/          # Agent notifications
└── /status/                 # Project status updates
```

## Monitoring Multi-Instance Setup

### Check Agent Activity:
```bash
# In separate terminal, monitor via APEX CLI
uv run apex status

# Or monitor memory activity
uv run apex memory watch "/projects/{id}/coordination/*"
```

### Monitor Task Progress:
```bash
# Watch task updates
uv run apex memory watch "/projects/{id}/tasks/*" --timeout 60

# Query recent task activity
uv run apex memory query "*task*" --content
```

## Performance Considerations

### Resource Management:
- Each Claude instance consumes memory and CPU
- Shared LMDB database handles concurrent access
- Monitor system resources during operation

### Optimization Tips:
- Use task dependencies to prevent resource conflicts
- Implement clear communication protocols
- Regular memory cleanup of completed tasks

### Scaling Recommendations:
- Start with 2-3 instances maximum
- Monitor performance before adding more agents
- Consider task complexity when scaling

## Common Issues and Solutions

### Instance Synchronization:
**Problem:** Agents working on same task simultaneously
**Solution:** Use task status locking and dependencies

```
> mcp__lmdb__write /projects/{id}/tasks/task-001 '{
  "status": "in_progress",
  "locked_by": "coder",
  "lock_timestamp": "2025-01-08T14:30:00Z"
}'
```

### Communication Delays:
**Problem:** Agents not seeing each other's updates
**Solution:** Implement notification polling

```
# Each agent regularly checks for notifications
> mcp__lmdb__list /projects/{id}/agents/coder/inbox/
```

### Memory Conflicts:
**Problem:** Concurrent writes to same keys
**Solution:** Use atomic operations and agent-specific namespaces

## Related Flows
- [MCP Integration Flow](mcp-integration-flow.md) - Setting up MCP for multi-instance
- [Multi-Agent Coordination Flow](multi-agent-coordination-flow.md) - Advanced coordination patterns
- [Memory Management Flow](memory-management-flow.md) - Managing shared memory
- [Task Workflow Flow](task-workflow-flow.md) - Task assignment and completion
