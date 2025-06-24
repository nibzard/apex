# Task Workflow Flow

## Purpose
Create, assign, track, and complete tasks within the APEX multi-agent system. Manage the full lifecycle of development work from user request to completion.

## Prerequisites
- APEX project initialized
- Agents started (at least Supervisor)
- LMDB database accessible

## Workflow Overview

### Task Lifecycle:
1. **User Request** → Task breakdown
2. **Task Assignment** → Agent receives work
3. **Task Execution** → Agent implements solution
4. **Task Review** → Quality assurance
5. **Task Completion** → Results stored

## Step-by-Step Process

### 1. Creating a Workflow

#### Start with Task Assignment:
```bash
uv run apex start --task "Create a REST API for user management"
```

**What Happens:**
1. Supervisor agent receives user request
2. Breaks down into specific subtasks
3. Assigns tasks to appropriate agents
4. Creates workflow tracking

#### Manual Task Creation (via MCP):
```bash
# In Claude Code with APEX MCP integration
mcp__lmdb__write /projects/my-project/tasks/task1 '{
  "description": "Implement user registration endpoint",
  "assigned_to": "coder",
  "priority": "high",
  "status": "pending"
}'
```

### 2. Task Breakdown Process

#### Supervisor Creates Subtasks:
For request: "Create user authentication system"

**Generated Tasks:**
1. **Analysis Task** (Coder)
   - Analyze requirements and plan implementation
   - Priority: High

2. **Implementation Task** (Coder)
   - Implement authentication solution
   - Depends on: Analysis Task
   - Priority: High

3. **Testing Task** (Adversary)
   - Test and review implementation
   - Depends on: Implementation Task
   - Priority: Medium

### 3. Task Assignment

#### Automatic Assignment:
- **Supervisor** → Planning, coordination, git operations
- **Coder** → Implementation, bug fixes, feature development
- **Adversary** → Testing, security review, quality assurance

#### Task Priorities:
- **High** - Critical tasks blocking other work
- **Medium** - Standard priority tasks
- **Low** - Nice-to-have improvements

### 4. Task Execution

#### Agent Workflow:
1. **Retrieve pending tasks:**
   ```bash
   # Agents automatically poll for tasks
   mcp__lmdb__read /agents/coder/tasks/pending
   ```

2. **Execute task:**
   - Agent processes assigned work
   - Creates code, tests, documentation
   - Updates progress in memory

3. **Complete task:**
   ```bash
   # Agent marks task complete with results
   mcp__lmdb__write /tasks/completed/task-id '{
     "status": "completed",
     "result": "Implementation details...",
     "completed_by": "coder_agent"
   }'
   ```

### 5. Monitoring Task Progress

#### Check Workflow Status:
```bash
uv run apex status
```

**Displays:**
- Pending tasks per agent
- Next task preview
- Overall workflow progress

#### View Specific Task:
```bash
# Via MCP tools in Claude Code
mcp__lmdb__read /tasks/pending/task-uuid
mcp__lmdb__read /tasks/completed/task-uuid
```

## Task Data Structure

### Task Information:
```json
{
  "task_id": "uuid-generated",
  "description": "Implement user login endpoint",
  "assigned_to": "coder",
  "priority": "high",
  "status": "pending",
  "depends_on": ["analysis-task-uuid"],
  "assigned_by": "supervisor",
  "created_at": "2025-01-08T12:00:00Z"
}
```

### Completed Task:
```json
{
  "task_id": "uuid-generated",
  "description": "Implement user login endpoint",
  "assigned_to": "coder",
  "status": "completed",
  "result": {
    "files_created": ["login.py", "auth_utils.py"],
    "tests_added": ["test_login.py"],
    "documentation": "Login endpoint documentation..."
  },
  "completed_by": "coder_agent",
  "completed_at": "2025-01-08T14:30:00Z"
}
```

## Memory Organization

### Task Storage Structure:
```
/tasks/
├── /pending/           # Active tasks waiting for execution
│   ├── task-uuid-1     # Individual task data
│   └── task-uuid-2
├── /completed/         # Finished tasks with results
│   ├── task-uuid-3
│   └── task-uuid-4
├── /index/            # Task index with metadata
│   ├── task-uuid-1    # Status, timestamps, assignments
│   └── ...
└── /workflows/        # High-level workflow tracking
    └── workflow-uuid  # Workflow metadata and task list
```

### Agent Task Queues:
```
/agents/
├── /supervisor/tasks/pending    # Supervisor's task queue
├── /coder/tasks/pending         # Coder's task queue
└── /adversary/tasks/pending     # Adversary's task queue
```

## Workflow Management

### Workflow Creation:
```json
{
  "workflow_id": "workflow-uuid",
  "user_request": "Create user authentication system",
  "task_ids": ["task1", "task2", "task3"],
  "status": "in_progress",
  "created_at": "2025-01-08T12:00:00Z"
}
```

### Workflow Status:
- **pending** - Tasks created but not started
- **in_progress** - Some tasks completed
- **completed** - All tasks finished

## Advanced Task Operations

### Task Dependencies:
Tasks can depend on other tasks:
```json
{
  "task_id": "implementation-task",
  "depends_on": ["analysis-task", "design-task"],
  "description": "Implement feature after analysis and design"
}
```

### Task Coordination:
- Agents check dependencies before starting tasks
- Dependent tasks wait for prerequisites
- Automatic task ordering based on dependencies

### Task Reassignment:
```bash
# Restart agent to reassign failed tasks
uv run apex agent restart coder
```

## MCP Integration

### Available MCP Tools:
- `mcp__lmdb__read` - Read task data
- `mcp__lmdb__write` - Create/update tasks
- `mcp__lmdb__list` - List tasks by pattern
- `mcp__lmdb__project_status` - Get workflow overview

### Example Task Management:
```bash
# Create new task
mcp__lmdb__write /tasks/pending/new-task '{
  "description": "Add input validation",
  "assigned_to": "coder",
  "priority": "medium"
}'

# Check pending tasks for agent
mcp__lmdb__list /agents/coder/tasks/pending

# Complete task
mcp__lmdb__write /tasks/completed/task-uuid '{
  "status": "completed",
  "result": "Validation added to all endpoints"
}'
```

## Common Patterns

### Feature Development:
1. **Planning** (Supervisor) → **Implementation** (Coder) → **Testing** (Adversary)
2. **Code Review** (Adversary) → **Fixes** (Coder) → **Final Review** (Adversary)

### Bug Fixing:
1. **Analysis** (Coder) → **Fix Implementation** (Coder) → **Testing** (Adversary)

### Security Review:
1. **Code Audit** (Adversary) → **Security Fixes** (Coder) → **Re-audit** (Adversary)

## Common Issues

**"No pending tasks"**
- Start workflow with task: `apex start --task "description"`
- Manually create tasks via MCP tools

**"Task dependencies not resolved"**
- Check prerequisite tasks are completed
- Verify dependency task IDs are correct

**"Agent not processing tasks"**
- Check agent is running: `apex status`
- Restart agent: `apex agent restart <agent>`
- Review agent logs: `apex agent logs <agent>`

**"Task stuck in pending"**
- Check agent assignment is correct
- Verify no circular dependencies
- Restart workflow if needed

## Related Flows
- [Agent Management Flow](agent-management-flow.md) - Managing agents that process tasks
- [Multi-Agent Coordination Flow](multi-agent-coordination-flow.md) - How agents work together
- [Memory Management Flow](memory-management-flow.md) - Accessing task data
- [Status Monitoring Flow](status-monitoring-flow.md) - Tracking task progress
