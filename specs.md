# APEX - Adversarial Pair EXecution

**A CLI/TUI orchestration tool for adversarial pair coding with AI agents**

```
 █████╗ ██████╗ ███████╗██╗  ██╗
██╔══██╗██╔══██╗██╔════╝╚██╗██╔╝
███████║██████╔╝█████╗   ╚███╔╝
██╔══██║██╔═══╝ ██╔══╝   ██╔██╗
██║  ██║██║     ███████╗██╔╝ ██╗
╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
Adversarial Pair EXecution v1.0
```

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Team Responsibilities](#team-responsibilities)
4. [Core Features](#core-features)
5. [Agent System](#agent-system)
6. [Claude CLI Integration](#claude-cli-integration)
7. [LMDB Memory System](#lmdb-memory-system)
8. [Continuation System](#continuation-system)
9. [Project Setup & CLAUDE.md](#project-setup--claudemd)
10. [CLI/TUI Specification](#cli-tui-specification)
11. [Development Setup](#development-setup)

## Overview

APEX orchestrates multiple Claude CLI processes working in an adversarial manner to produce robust, secure code at unprecedented velocity. The tool maintains developer flow through intelligent session management, real-time monitoring, and seamless pause/resume capabilities. All agent state and communication happens through LMDB via MCP protocol.

### Quick Start
```bash
# Install
uv install apex

# Start new project (interactive setup)
apex new myproject

# Start agents
apex start

# Interactive TUI
apex tui

# Resume session
apex resume --session abc123
```

## Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                         APEX CLI/TUI                            │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────┐ │
│  │  Command  │  │    TUI    │  │  Session  │  │   Project   │ │
│  │  Parser   │  │  (Textual)│  │  Manager  │  │   Setup     │ │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └──────┬──────┘ │
└────────┼──────────────┼──────────────┼───────────────┼────────┘
         │              │              │               │
┌────────▼──────────────▼──────────────▼───────────────▼────────┐
│                    Orchestration Engine                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Process   │  │   Stream    │  │ Continuation │           │
│  │   Manager   │  │   Parser    │  │   System     │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
└─────────┼────────────────┼────────────────┼───────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼───────────────────┐
│                    Claude CLI Processes                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Coder     │  │  Adversary  │  │ Supervisor  │           │
│  │   Process   │  │   Process   │  │   Process   │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
└─────────┼────────────────┼────────────────┼───────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼───────────────────┐
│                    LMDB MCP Server                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │    Agent    │  │   Project   │  │   Session   │           │
│  │    State    │  │    Data     │  │   History   │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    APEX Data Flow                               │
│                                                                 │
│  User Input                                                     │
│      │                                                          │
│      ▼                                                          │
│  APEX CLI ──────► Process Manager                              │
│                        │                                        │
│                        ├─► Spawn: claude -p "supervisor..."     │
│                        ├─► Spawn: claude -p "coder..."         │
│                        └─► Spawn: claude -p "adversary..."      │
│                                │                                │
│                                ▼                                │
│                     Stream JSON Parser                          │
│                          │                                      │
│                          ▼                                      │
│                   Parse & Store in LMDB:                        │
│                   • /sessions/{id}/events                       │
│                   • /agents/{id}/state                          │
│                   • /agents/{id}/messages                       │
│                   • /tools/{id}/calls                           │
│                   • /tools/{id}/results                         │
│                                │                                │
│                                ▼                                │
│                      MCP Tool Execution                         │
│                   (LMDB reads/writes via MCP)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Team Responsibilities

### Team Alpha: Core Infrastructure
**Scope**: Process management, LMDB integration, MCP server
```
apex/
├── src/
│   ├── apex/
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration management
│   │   ├── types.py         # Shared type definitions
│   │   └── utils.py         # Common utilities
│   └── core/
│       ├── __init__.py
│       ├── process_manager.py  # Claude CLI process spawning
│       ├── stream_parser.py    # JSON stream parsing
│       ├── lmdb_mcp.py        # LMDB + MCP server
│       └── memory.py          # Memory structure management
```

### Team Beta: Agent System
**Scope**: Agent prompts, coordination logic, MCP tools
```
apex/
└── src/
    └── agents/
        ├── __init__.py
        ├── prompts.py       # Agent prompt templates
        ├── coordinator.py   # Agent coordination logic
        ├── tools.py         # MCP tool definitions
        └── lifecycle.py     # Agent lifecycle management
```

### Team Gamma: Orchestration & Continuation
**Scope**: Session management, continuation, state persistence
```
apex/
└── src/
    └── orchestration/
        ├── __init__.py
        ├── engine.py        # Main orchestration engine
        ├── session.py       # Session management
        ├── continuation.py  # Pause/resume system
        ├── state.py         # State persistence in LMDB
        └── events.py        # Event stream processing
```

### Team Delta: CLI/TUI Interface
**Scope**: User interface, project setup, monitoring
```
apex/
└── src/
    ├── cli/
    │   ├── __init__.py
    │   ├── commands.py      # CLI command definitions
    │   ├── setup.py         # Project setup wizard
    │   └── output.py        # Formatted output helpers
    └── tui/
        ├── __init__.py
        ├── app.py           # Main TUI application
        ├── screens/         # TUI screens
        │   ├── dashboard.py
        │   ├── agents.py
        │   └── logs.py
        └── widgets/         # Custom TUI widgets
```

### Team Epsilon: Version Control Integration
**Scope**: Git operations and GitHub integration
```
apex/
└── src/
    └── vcs/
        ├── __init__.py
        ├── git_ops.py       # Git operations
        ├── github_client.py # GitHub API integration
        └── auto_commit.py   # Automatic commit logic
```

## Core Features

### Process Management
```
┌─────────────────────────────────────────────┐
│          Process Management                 │
│                                             │
│  APEX Process Manager                       │
│       │                                     │
│       ├─► Claude Process (Supervisor)       │
│       │   └─► stdout pipe ──► Parser       │
│       │                                     │
│       ├─► Claude Process (Coder)           │
│       │   └─► stdout pipe ──► Parser       │
│       │                                     │
│       └─► Claude Process (Adversary)        │
│           └─► stdout pipe ──► Parser       │
│                                             │
│  Features:                                  │
│  • Process lifecycle management             │
│  • Automatic restart on failure             │
│  • Resource monitoring                      │
│  • Clean shutdown handling                  │
└─────────────────────────────────────────────┘
```

### Memory Organization
```
┌─────────────────────────────────────────────┐
│           LMDB Memory Structure             │
│                                             │
│  /projects/{project_id}/                    │
│    ├── /config                              │
│    │   ├── name                             │
│    │   ├── description                      │
│    │   └── tech_stack                      │
│    │                                        │
│    ├── /agents/                             │
│    │   ├── supervisor/                      │
│    │   │   ├── prompt                       │
│    │   │   ├── state                        │
│    │   │   └── messages[]                   │
│    │   ├── coder/...                        │
│    │   └── adversary/...                    │
│    │                                        │
│    ├── /memory/                             │
│    │   ├── /tasks/*                         │
│    │   ├── /code/*                          │
│    │   ├── /tests/*                         │
│    │   ├── /issues/*                        │
│    │   └── /status/*                        │
│    │                                        │
│    ├── /sessions/                           │
│    │   └── {session_id}/                    │
│    │       ├── events[]                     │
│    │       ├── checkpoints[]                │
│    │       └── metrics                      │
│    │                                        │
│    └── /git/                                │
│        ├── branch                           │
│        ├── commits[]                        │
│        └── pr_status                        │
└─────────────────────────────────────────────┘
```

## Agent System

### Agent Execution Model
```python
class AgentProcess:
    """Manages a Claude CLI process for an agent"""

    def __init__(self, agent_type: AgentType, project_id: str):
        self.agent_type = agent_type
        self.project_id = project_id
        self.process = None
        self.parser = StreamParser()

    async def start(self):
        """Start the Claude CLI process"""
        # Load agent prompt from LMDB
        prompt = await self.load_agent_prompt()

        # Build command with MCP config
        cmd = [
            "claude",
            "-p", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--model", "claude-sonnet-4-20250514",
            "--mcp-config", "configs/lmdb_mcp.json",
            "--allowedTools", "mcp__lmdb__read,mcp__lmdb__write,mcp__lmdb__list,mcp__lmdb__watch",
            "--max-turns", "50"
        ]

        # Start process
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Start parsing output
        asyncio.create_task(self.parse_output())

    async def parse_output(self):
        """Parse streaming JSON output"""
        async for line in self.process.stdout:
            try:
                event = json.loads(line)
                await self.handle_event(event)
            except json.JSONDecodeError:
                continue

    async def handle_event(self, event: dict):
        """Handle parsed JSON event"""
        event_type = event.get("type")

        if event_type == "system":
            await self.handle_system_event(event)
        elif event_type == "assistant":
            await self.handle_assistant_event(event)
        elif event_type == "user":
            await self.handle_user_event(event)
        elif event_type == "result":
            await self.handle_result_event(event)

        # Store all events in LMDB
        await self.store_event(event)
```

### Agent Prompts
```python
class AgentPrompts:
    """Agent prompt templates"""

    SUPERVISOR_TEMPLATE = """You are a Supervisor agent in the APEX system working on project: {project_name}

Project Description: {project_description}
Tech Stack: {tech_stack}

Your role is to:
1. Break down user requests into specific tasks
2. Coordinate work between Coder and Adversary agents
3. Monitor progress through LMDB shared memory
4. Manage git commits and pull requests

Available MCP Tools:
- mcp__lmdb__read(key): Read from shared memory
- mcp__lmdb__write(key, value): Write to shared memory
- mcp__lmdb__list(prefix): List keys with prefix
- mcp__lmdb__watch(pattern): Watch for changes
- mcp__lmdb__cursor_scan(start, end, limit): Efficient range scan
- Bash(git *): Execute git commands
- Bash(gh *): Execute GitHub CLI commands
- mcp__git__status(): Check git status
- mcp__git__commit(message): Create git commit
- mcp__github__pr_create(title, body): Create GitHub PR
- mcp__github__issue_create(title, body, labels): Create GitHub issue
- mcp__github__pr_merge(pr_number): Merge pull request
- mcp__github__release_create(tag, title, notes): Create GitHub release
- mcp__apex__progress(task_id, percent, message): Report progress

Memory Structure:
- /tasks/*: Task assignments and status
- /code/*: Source code files
- /tests/*: Test files and results
- /issues/*: Bugs and vulnerabilities
- /status/*: Agent status updates

Current user request: {user_request}
"""

    CODER_TEMPLATE = """You are a Coder agent in the APEX system working on project: {project_name}

Your role is to:
1. Implement features based on tasks in /tasks/*
2. Fix issues reported in /issues/*
3. Write clean, secure, well-documented code
4. Update your status in /status/coder
5. Report progress using mcp__apex__progress tool

Available MCP Tools:
- mcp__lmdb__read(key): Read from shared memory
- mcp__lmdb__write(key, value): Write to shared memory
- mcp__lmdb__list(prefix): List keys with prefix
- mcp__lmdb__watch(pattern): Watch for changes
- mcp__lmdb__cursor_scan(start, end, limit): Efficient range scan
- Bash(git *): Execute git commands
- Bash(gh *): Execute GitHub CLI commands

Workflow:
1. Check /tasks/pending for new assignments
2. Read task details and implement solution
3. Write code to /code/{filename}
4. Update task status to 'completed'
5. Monitor /issues/* for bugs to fix
"""

    ADVERSARY_TEMPLATE = """You are an Adversary agent in the APEX system working on project: {project_name}

Your role is to:
1. Test code written by the Coder agent
2. Find bugs, vulnerabilities, and edge cases
3. Write comprehensive test suites
4. Report issues for the Coder to fix
5. Use sampling API for decision-making

Available MCP Tools:
- mcp__lmdb__read(key): Read from shared memory
- mcp__lmdb__write(key, value): Write to shared memory
- mcp__lmdb__list(prefix): List keys with prefix
- mcp__lmdb__watch(pattern): Watch for changes
- mcp__apex__sample(prompt, options): Use model sampling for decisions

Workflow:
1. Watch /code/* for new or modified files
2. Analyze code for issues
3. Write tests to /tests/*
4. Report issues to /issues/{severity}/{id}
5. Update your status in /status/adversary

Focus on:
- Security vulnerabilities (SQL injection, XSS, etc.)
- Edge cases and error handling
- Performance issues
- Code quality and best practices
"""
```

## Claude CLI Integration

### Stream Event Types
```python
@dataclass
class StreamEvent:
    """Parsed streaming JSON event from Claude CLI"""

    type: str  # "system", "assistant", "user", "result"
    timestamp: datetime
    session_id: str
    agent_id: str
    raw_event: dict

@dataclass
class SystemEvent(StreamEvent):
    """System initialization event"""
    subtype: str  # "init"
    tools: List[str]
    mcp_servers: List[dict]

@dataclass
class AssistantEvent(StreamEvent):
    """Assistant message event"""
    message: dict
    tool_use: Optional[List[dict]]

@dataclass
class ToolCallEvent(StreamEvent):
    """Tool call event"""
    tool_name: str
    tool_id: str
    parameters: dict

@dataclass
class ToolResultEvent(StreamEvent):
    """Tool result event"""
    tool_id: str
    result: Any
    error: Optional[str]
```

### Stream Parser Implementation
```python
class StreamParser:
    """Parse Claude CLI streaming JSON output"""

    def __init__(self, agent_id: str, session_id: str):
        self.agent_id = agent_id
        self.session_id = session_id
        self.lmdb = LMDBClient()

    async def parse_line(self, line: str) -> Optional[StreamEvent]:
        """Parse a single line of JSON output"""
        try:
            data = json.loads(line.strip())
            return await self.create_event(data)
        except json.JSONDecodeError:
            return None

    async def create_event(self, data: dict) -> StreamEvent:
        """Create typed event from raw JSON"""
        event_type = data.get("type")

        base_args = {
            "type": event_type,
            "timestamp": datetime.now(),
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "raw_event": data
        }

        if event_type == "system":
            return SystemEvent(
                **base_args,
                subtype=data.get("subtype"),
                tools=data.get("tools", []),
                mcp_servers=data.get("mcp_servers", [])
            )
        elif event_type == "assistant":
            message = data.get("message", {})
            content = message.get("content", [])
            tool_use = [c for c in content if c.get("type") == "tool_use"]

            return AssistantEvent(
                **base_args,
                message=message,
                tool_use=tool_use if tool_use else None
            )
        # ... handle other event types

    async def store_event(self, event: StreamEvent):
        """Store parsed event in LMDB"""
        # Store in session history
        session_key = f"/sessions/{event.session_id}/events"
        await self.lmdb.append(session_key, event.dict())

        # Store agent-specific data
        if isinstance(event, AssistantEvent):
            agent_key = f"/agents/{event.agent_id}/messages"
            await self.lmdb.append(agent_key, event.message)

        # Store tool calls for continuation
        if isinstance(event, ToolCallEvent):
            tool_key = f"/tools/calls/{event.tool_id}"
            await self.lmdb.write(tool_key, event.dict())
```

## LMDB Memory System

### MCP Server Implementation
```python
class LMDBMCP:
    """MCP server for LMDB access"""

    def __init__(self, db_path: str):
        self.env = lmdb.open(db_path, map_size=10*1024*1024*1024)  # 10GB
        self.tools = self.register_tools()

    def register_tools(self) -> dict:
        """Register MCP tools"""
        return {
            "lmdb_read": self.tool_read,
            "lmdb_write": self.tool_write,
            "lmdb_list": self.tool_list,
            "lmdb_watch": self.tool_watch,
            "lmdb_delete": self.tool_delete,
            "lmdb_transaction": self.tool_transaction
        }

    async def tool_read(self, key: str) -> Any:
        """Read value from LMDB"""
        with self.env.begin() as txn:
            value = txn.get(key.encode())
            if value:
                return json.loads(value.decode())
            return None

    async def tool_write(self, key: str, value: Any) -> bool:
        """Write value to LMDB"""
        with self.env.begin(write=True) as txn:
            txn.put(
                key.encode(),
                json.dumps(value).encode()
            )
            # Notify watchers
            await self.notify_watchers(key, value)
            return True

    async def tool_list(self, prefix: str) -> List[str]:
        """List keys with prefix"""
        keys = []
        with self.env.begin() as txn:
            cursor = txn.cursor()
            for key, _ in cursor.iternext():
                key_str = key.decode()
                if key_str.startswith(prefix):
                    keys.append(key_str)
        return keys

    async def tool_watch(self, pattern: str) -> AsyncIterator[dict]:
        """Watch for changes to keys matching pattern"""
        # Implementation uses asyncio queues for real-time updates
        queue = asyncio.Queue()
        self.add_watcher(pattern, queue)

        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self.remove_watcher(pattern, queue)
```

### Memory Access Patterns
```python
class MemoryPatterns:
    """Common memory access patterns for agents"""

    @staticmethod
    async def supervisor_create_task(mcp: LMDBMCP, task: dict):
        """Supervisor creates a new task"""
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "description": task["description"],
            "assigned_to": task.get("assigned_to", "coder"),
            "priority": task.get("priority", "medium"),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "depends_on": task.get("depends_on", [])
        }

        # Write to pending tasks
        await mcp.tool_write(f"/tasks/pending/{task_id}", task_data)

        # Update task index
        await mcp.tool_write(f"/tasks/index/{task_id}", {
            "status": "pending",
            "assigned_to": task_data["assigned_to"]
        })

        return task_id

    @staticmethod
    async def coder_complete_task(mcp: LMDBMCP, task_id: str, files: dict):
        """Coder completes a task"""
        # Write code files
        for filename, content in files.items():
            await mcp.tool_write(f"/code/{filename}", {
                "content": content,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            })

        # Update task status
        task_key = f"/tasks/pending/{task_id}"
        task = await mcp.tool_read(task_key)
        if task:
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()

            # Move to completed
            await mcp.tool_write(f"/tasks/completed/{task_id}", task)
            await mcp.tool_delete(task_key)

            # Update index
            await mcp.tool_write(f"/tasks/index/{task_id}", {
                "status": "completed"
            })

    @staticmethod
    async def adversary_report_issue(mcp: LMDBMCP, issue: dict):
        """Adversary reports an issue"""
        issue_id = str(uuid.uuid4())
        severity = issue.get("severity", "medium")

        issue_data = {
            "id": issue_id,
            "severity": severity,
            "type": issue.get("type"),  # "security", "bug", "performance"
            "file": issue.get("file"),
            "line": issue.get("line"),
            "description": issue.get("description"),
            "reproduction": issue.get("reproduction"),
            "suggested_fix": issue.get("suggested_fix"),
            "created_at": datetime.now().isoformat(),
            "status": "open"
        }

        # Write to issues
        await mcp.tool_write(f"/issues/{severity}/{issue_id}", issue_data)

        # Update issue count
        count_key = f"/metrics/issues/{severity}"
        count = await mcp.tool_read(count_key) or 0
        await mcp.tool_write(count_key, count + 1)
```

## Continuation System

### Continuation Architecture
```python
@dataclass
class Continuation:
    """Complete system state for pause/resume"""

    # Session identification
    session_id: str
    checkpoint_id: str
    timestamp: datetime

    # Process states
    process_states: Dict[str, ProcessState]

    # LMDB snapshot
    memory_snapshot: MemorySnapshot

    # Event history
    event_history: List[StreamEvent]

    # Active operations
    pending_tools: List[PendingToolCall]

    # Git state
    git_state: GitState

    # Metadata
    metadata: ContinuationMetadata

@dataclass
class ProcessState:
    """State of a Claude CLI process"""
    agent_type: str
    process_id: Optional[int]
    last_prompt: str
    conversation_history: List[dict]
    current_task: Optional[str]
    status: str  # "active", "paused", "completed"

@dataclass
class MemorySnapshot:
    """Snapshot of LMDB at checkpoint"""
    timestamp: datetime
    keys: Dict[str, Any]  # All relevant keys and values
    version: int

class ContinuationManager:
    """Manage pause/resume operations"""

    async def create_checkpoint(self, session_id: str) -> str:
        """Create a checkpoint of current state"""
        checkpoint_id = str(uuid.uuid4())

        # Gather process states
        process_states = {}
        for agent_type, process in self.processes.items():
            process_states[agent_type] = await self.capture_process_state(process)

        # Create memory snapshot
        memory_snapshot = await self.create_memory_snapshot(session_id)

        # Get event history
        events_key = f"/sessions/{session_id}/events"
        event_history = await self.lmdb.read(events_key) or []

        # Create continuation object
        continuation = Continuation(
            session_id=session_id,
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now(),
            process_states=process_states,
            memory_snapshot=memory_snapshot,
            event_history=event_history,
            pending_tools=self.get_pending_tools(),
            git_state=await self.capture_git_state(),
            metadata=ContinuationMetadata(
                reason="user_requested",
                created_by="apex"
            )
        )

        # Store continuation
        cont_key = f"/continuations/{checkpoint_id}"
        await self.lmdb.write(cont_key, continuation.dict())

        return checkpoint_id

    async def resume_from_checkpoint(self, checkpoint_id: str):
        """Resume from a checkpoint"""
        # Load continuation
        cont_key = f"/continuations/{checkpoint_id}"
        cont_data = await self.lmdb.read(cont_key)
        if not cont_data:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        continuation = Continuation(**cont_data)

        # Restore memory state
        await self.restore_memory_snapshot(continuation.memory_snapshot)

        # Restart processes with context
        for agent_type, state in continuation.process_states.items():
            await self.restart_process_with_state(agent_type, state)

        # Resume pending operations
        for tool_call in continuation.pending_tools:
            await self.resume_tool_call(tool_call)

        return continuation.session_id
```

## Project Setup & CLAUDE.md

### Project Setup Wizard
```python
class ProjectSetup:
    """Interactive project setup"""

    async def setup_new_project(self, project_name: str):
        """Setup new APEX project"""
        # Create project directory
        project_dir = Path(project_name)
        project_dir.mkdir(exist_ok=True)

        # Interactive prompts
        questions = [
            {
                "type": "input",
                "name": "description",
                "message": "Project description:",
                "default": f"A new {project_name} project"
            },
            {
                "type": "checkbox",
                "name": "tech_stack",
                "message": "Select technologies:",
                "choices": [
                    "Python", "JavaScript", "TypeScript", "React",
                    "Flask", "FastAPI", "Django", "Node.js",
                    "PostgreSQL", "MongoDB", "Redis", "SQLite"
                ]
            },
            {
                "type": "list",
                "name": "project_type",
                "message": "Project type:",
                "choices": [
                    "Web Application",
                    "API Service",
                    "CLI Tool",
                    "Library",
                    "Data Pipeline",
                    "Machine Learning",
                    "Other"
                ]
            },
            {
                "type": "input",
                "name": "features",
                "message": "Key features (comma-separated):",
                "default": "authentication, database, API"
            }
        ]

        answers = await self.prompt_user(questions)

        # Generate CLAUDE.md using Claude
        claude_md = await self.generate_claude_md(project_name, answers)

        # Write CLAUDE.md
        (project_dir / "CLAUDE.md").write_text(claude_md)

        # Initialize git
        await self.init_git(project_dir)

        # Store project config in LMDB
        project_id = str(uuid.uuid4())
        await self.store_project_config(project_id, project_name, answers)

        return project_id

    async def generate_claude_md(self, project_name: str, config: dict) -> str:
        """Use Claude to generate customized CLAUDE.md"""
        prompt = f"""Generate a CLAUDE.md file for an APEX project with these details:

Project Name: {project_name}
Description: {config['description']}
Tech Stack: {', '.join(config['tech_stack'])}
Project Type: {config['project_type']}
Key Features: {config['features']}

The CLAUDE.md should include:
1. Project overview and architecture
2. Development guidelines specific to the tech stack
3. Testing requirements
4. Security considerations
5. Performance targets
6. Code style guidelines

Make it specific and actionable for AI agents working on this project."""

        # Run Claude to generate CLAUDE.md
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "text",
            "--model", "claude-sonnet-4-20250514"
        ]

        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await result.communicate()
        return stdout.decode()
```

### CLAUDE.md Template Structure
```markdown
# Project: {project_name}

## Overview
{project_description}

## Architecture
- **Tech Stack**: {tech_stack}
- **Project Type**: {project_type}
- **Key Features**: {features}

## Development Guidelines

### Code Organization
- Follow {language}-specific best practices
- Use meaningful variable and function names
- Keep functions small and focused
- Document complex logic

### {tech_specific_section}
[Generated based on selected technologies]

## Agent Coordination

### Task Flow
1. Supervisor breaks down features into tasks
2. Coder implements based on task specifications
3. Adversary tests implementation thoroughly
4. Cycle continues until quality standards met

### Memory Keys
- `/tasks/*` - Feature tasks and assignments
- `/code/*` - Implementation files
- `/tests/*` - Test suites and results
- `/issues/*` - Bugs and improvements
- `/docs/*` - Documentation updates

## Quality Standards
- Code coverage: minimum 90%
- Security: No critical vulnerabilities
- Performance: {performance_targets}
- Documentation: All public APIs documented

## Git Workflow
- Branch naming: `feature/`, `fix/`, `chore/`
- Commit format: Conventional Commits
- PR reviews: All code must pass tests

## Specific Requirements
{project_specific_requirements}
```

## CLI/TUI Specification

### CLI Commands - Detailed
```bash
# Project Management
apex new <project>           # Interactive project setup wizard
  Options:
    --template <name>        # Use predefined template
    --no-git                 # Skip git initialization
    --tech <stack>          # Preset technology stack

apex init                    # Initialize APEX in existing project
  Options:
    --import <config>       # Import configuration

apex list                    # List all APEX projects
  Output format:
    PROJECT_ID  NAME        STATUS    LAST_RUN
    abc-123     myapp       active    2h ago
    def-456     backend     paused    1d ago

# Session Control
apex start                   # Start all agents
  Options:
    --agents <list>         # Start specific agents only
    --continue <id>         # Continue from checkpoint
    --task <description>    # Set initial task

apex pause                   # Pause all agents
  Options:
    --checkpoint            # Create named checkpoint
    --timeout <seconds>     # Wait for clean pause

apex resume <checkpoint>     # Resume from checkpoint
  Options:
    --agents <list>         # Resume specific agents
    --reset-memory          # Clear working memory

# Agent Management
apex agent <subcommand>
  list                      # Show agent status
  logs <agent>             # Stream agent logs
    Options:
      --tail <n>           # Last n lines
      --follow             # Follow log output
      --filter <pattern>   # Filter messages
  restart <agent>          # Restart agent process
  prompt <agent>           # View/edit agent prompt
    Options:
      --edit               # Open in editor
      --reset              # Reset to default

# Memory Operations
apex memory <subcommand>
  show [key]               # Display memory contents
    Options:
      --format <fmt>       # json|yaml|table
      --depth <n>          # Traversal depth
  query <pattern>          # Query memory with pattern
  export [file]            # Export memory snapshot
  import <file>            # Import memory snapshot
  watch <pattern>          # Watch for changes

# Git Integration
apex git <subcommand>
  status                   # Enhanced git status
  log                      # Show APEX-annotated commits
    Options:
      --tasks              # Include task references
      --agents             # Show agent contributions
  auto-commit              # Trigger auto-commit
    Options:
      --message <msg>      # Custom message
      --no-tests           # Skip test requirement

# GitHub Integration
apex github <subcommand>
  pr create                # Create pull request
    Options:
      --title <title>      # PR title
      --body <body>        # PR description
      --draft              # Create as draft
  pr list                  # List pull requests
  pr merge <number>        # Merge pull request
  issue create             # Create GitHub issue
    Options:
      --title <title>      # Issue title
      --body <body>        # Issue description
      --labels <labels>    # Comma-separated labels
  release create <tag>     # Create GitHub release
    Options:
      --title <title>      # Release title
      --notes <file>       # Release notes file

# Monitoring
apex metrics [component]    # Show performance metrics
  Options:
    --period <time>        # Time period
    --export <file>        # Export data

apex health                 # System health check
  Output:
    COMPONENT    STATUS    LATENCY    MEMORY    VERSION
    LMDB         ✓ OK      1ms        245MB     1.0.0
    Supervisor   ✓ OK      -          123MB     -
    Coder        ✓ OK      -          156MB     -
    Adversary    ✓ OK      -          134MB     -
    MCP Server   ✓ OK      2ms        45MB      1.0.0
    Transport    ✓ OK      <1ms       -         stdio

# MCP Management
apex mcp <subcommand>
  list                      # List configured MCP servers
  add <config>             # Add MCP server from config
  remove <name>            # Remove MCP server
  test <server>            # Test MCP server connectivity
  logs <server>            # View MCP server logs
    Options:
      --tail <n>           # Last n lines
      --follow             # Follow log output
  tools <server>           # List available tools
  validate                 # Run MCP compliance tests

apex report [session]       # Generate session report
  Options:
    --format <fmt>         # html|pdf|markdown
    --include <sections>   # Customize sections

# Interactive Mode
apex tui                    # Launch TUI interface
  Options:
    --layout <name>        # Preset layout
    --theme <name>         # Color theme
```

### TUI Layouts

#### Dashboard Layout (Default)
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
│ │ Tasks/hr: 12            │ │ ▶ Write API documentation  │ │
│ └─────────────────────────┘ └─────────────────────────────┘ │
│ ┌─ Activity Feed ────────────────────────────────────────┐   │
│ │ 14:23:01 [Coder] Implemented user model                │   │
│ │ 14:23:15 [Adversary] Found SQL injection in login      │   │
│ │ 14:23:18 [Coder] Fixing SQL injection issue            │   │
│ │ 14:23:45 [Supervisor] Committed: feat: add user model  │   │
│ │ 14:24:02 [Adversary] All tests passing                 │   │
│ └────────────────────────────────────────────────────────┘   │
│ [F1]Help [F2]Agents [F3]Memory [F4]Tasks [F5]Git [Q]Quit     │
└──────────────────────────────────────────────────────────────┘
```

#### Agent Focus Layout
```
┌─ APEX Agent View ────────────────────────────────────────────┐
│ Layout: Split-3 | Focus: Balanced | Auto-scroll: ON         │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Supervisor      │ Coder           │ Adversary              │
│ ────────────────┼─────────────────┼─────────────────────── │
│ Planning next   │ Working on:     │ Testing:               │
│ sprint tasks    │ auth/login.py   │ auth/login.py          │
│                 │                 │                        │
│ Tasks created:  │ def login(usr): │ Running: test_login    │
│ ✓ Auth system   │   # Validate    │ ✗ SQL injection found  │
│ ✓ User CRUD     │   usr = escape( │ ✓ XSS prevented        │
│ ⧗ API docs      │     usr)        │ ✓ Rate limit works     │
│                 │   pwd_hash =    │                        │
│ Git status:     │     hash(pwd)   │ Coverage: 84%          │
│ Ready to commit │   ...           │ 2 critical issues     │
├─────────────────┴─────────────────┴─────────────────────────┤
│ Shared Memory: /tasks/current: "Implement secure login"      │
│ Last Commit: 5 min ago | PR #23: In Progress                │
└──────────────────────────────────────────────────────────────┘
```

## Development Setup

### Complete Project Structure
```
apex/
├── pyproject.toml          # UV project configuration
├── uv.lock                 # Dependency lock file
├── README.md               # Project documentation
├── LICENSE                 # MIT License
├── .env.example            # Environment variables template
├── .github/
│   └── workflows/
│       ├── ci.yml          # Continuous integration
│       ├── release.yml     # Release automation
│       └── codeql.yml      # Security scanning
├── src/
│   └── apex/
│       ├── __init__.py
│       ├── __main__.py     # Entry point
│       ├── cli/            # CLI implementation
│       ├── tui/            # TUI implementation
│       ├── core/           # Core functionality
│       ├── agents/         # Agent management
│       ├── orchestration/  # Process orchestration
│       ├── vcs/            # Version control
│       └── utils/          # Utilities
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── fixtures/          # Test fixtures
├── scripts/
│   ├── setup_dev.py       # Development setup
│   ├── build_release.py   # Build script
│   └── run_benchmarks.py  # Performance tests
├── docs/
│   ├── api/               # API documentation
│   ├── guides/            # User guides
│   ├── architecture/      # Architecture docs
│   └── examples/          # Example projects
└── templates/             # Project templates
    ├── web_app/
    ├── api_service/
    └── cli_tool/
```

### Dependencies (pyproject.toml) - Complete
```toml
[project]
name = "apex"
version = "1.0.0"
description = "Adversarial Pair Execution - Orchestrate Claude agents for robust code generation"
authors = [{name = "APEX Team", email = "apex@example.com"}]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Code Generators",
    "Topic :: Software Development :: Testing",
]

dependencies = [
    # Core
    "lmdb>=1.4.0",               # Memory store
    "msgpack>=1.0.0",            # Efficient serialization
    "pydantic>=2.5.0",           # Data validation

    # CLI/TUI
    "typer[all]>=0.12.0",        # CLI framework
    "textual>=0.41.0",           # TUI framework
    "rich>=13.0.0",              # Rich text formatting
    "prompt-toolkit>=3.0.0",     # Interactive prompts

    # Async & Process Management
    "asyncio>=3.11",
    "aiofiles>=23.0.0",
    "psutil>=5.9.0",             # Process monitoring

    # Git Integration
    "gitpython>=3.1.0",          # Git operations
    "pygithub>=2.1.0",           # GitHub API

    # Monitoring & Logging
    "structlog>=23.0.0",         # Structured logging
    "prometheus-client>=0.19.0",  # Metrics
    "opentelemetry-api>=1.20.0", # Distributed tracing

    # Utilities
    "toml>=0.10.0",              # Config files
    "watchdog>=3.0.0",           # File watching
    "httpx>=0.25.0",             # HTTP client
    "python-dotenv>=1.0.0",      # Environment management
]

[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-benchmark>=4.0.0",

    # Code Quality
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "pre-commit>=3.5.0",

    # Development Tools
    "ipython>=8.18.0",
    "ipdb>=0.13.0",
    "pytest-xdist>=3.5.0",
]

docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
    "mkdocstrings[python]>=0.24.0",
]

[project.scripts]
apex = "apex.cli:main"

[project.urls]
Homepage = "https://github.com/nibzard/apex"
Documentation = "https://apex.readthedocs.io"
Repository = "https://github.com/nibzard/apex"
Issues = "https://github.com/nibzard/apex/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build]
include = [
    "src/apex/**/*.py",
    "src/apex/**/*.toml",
    "templates/**/*",
]

[tool.uv]
dev-dependencies = [
    "ipython>=8.18.0",
    "pytest-xdist>=3.5.0",
]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "B", "C90", "D"]
ignore = ["D100", "D104"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=apex --cov-report=html --cov-report=term-missing"

[tool.coverage.run]
source = ["src/apex"]
omit = ["*/tests/*", "*/__main__.py"]
```

### Installation & Development

#### Initial Setup
```bash
# Clone repository
git clone https://github.com/nibzard/apex
cd apex

# Create virtual environment with UV
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Install in development mode
uv pip install -e ".[dev,docs]"

# Setup pre-commit hooks
pre-commit install

# Run initial tests
uv run pytest

# Start development server
uv run python scripts/setup_dev.py
```

#### Development Workflow
```bash
# Start new feature
git checkout -b feature/new-feature

# Run tests continuously
uv run pytest-watch

# Format code
uv run black src tests
uv run ruff check --fix src tests

# Type checking
uv run mypy src

# Run benchmarks
uv run python scripts/run_benchmarks.py

# Build documentation
uv run mkdocs serve

# Create release
uv run python scripts/build_release.py
```

## Implementation Examples

### Process Manager Implementation
```python
class ProcessManager:
    """Manages Claude CLI processes"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.processes: Dict[str, AgentProcess] = {}
        self.lmdb = LMDBClient()

    async def start_agent(self, agent_type: str, task: Optional[str] = None):
        """Start a Claude agent process"""
        # Load project config
        config = await self.lmdb.read(f"/projects/{self.project_id}/config")

        # Generate prompt
        prompt_template = self.get_prompt_template(agent_type)
        prompt = prompt_template.format(
            project_name=config["name"],
            project_description=config["description"],
            tech_stack=", ".join(config["tech_stack"]),
            user_request=task or "Monitor for tasks"
        )

        # Create process
        process = AgentProcess(agent_type, self.project_id)
        process.prompt = prompt

        # Start process
        await process.start()

        # Store reference
        self.processes[agent_type] = process

        # Update agent state
        await self.lmdb.write(
            f"/agents/{agent_type}/state",
            {
                "status": "active",
                "started_at": datetime.now().isoformat(),
                "process_id": process.process.pid
            }
        )

        return process
```

### Event Processing Pipeline
```python
class EventProcessor:
    """Process streaming events from Claude CLI"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.handlers = self.setup_handlers()

    def setup_handlers(self) -> Dict[str, Callable]:
        """Setup event type handlers"""
        return {
            "system": self.handle_system,
            "assistant": self.handle_assistant,
            "user": self.handle_user,
            "result": self.handle_result,
        }

    async def process_event(self, event: dict):
        """Process a single event"""
        event_type = event.get("type")
        handler = self.handlers.get(event_type)

        if handler:
            await handler(event)

        # Store all events
        await self.store_event(event)

    async def handle_assistant(self, event: dict):
        """Handle assistant message events"""
        message = event.get("message", {})
        content = message.get("content", [])

        for item in content:
            if item.get("type") == "tool_use":
                await self.handle_tool_use(item)
            elif item.get("type") == "text":
                await self.handle_text_output(item)

    async def handle_tool_use(self, tool_use: dict):
        """Handle MCP tool calls"""
        tool_name = tool_use.get("name")
        tool_id = tool_use.get("id")
        params = tool_use.get("input", {})

        # Execute tool
        result = await self.execute_tool(tool_name, params)

        # Store result
        await self.lmdb.write(
            f"/tools/results/{tool_id}",
            {
                "tool_name": tool_name,
                "params": params,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        )
```

## Key Implementation Guidelines

1. **Process Isolation**: Each agent runs in its own Claude CLI process
2. **Streaming JSON**: All Claude output is parsed and stored in real-time
3. **MCP Integration**: All agent communication happens through LMDB via MCP
4. **State Persistence**: Every event and state change is persisted for continuation
5. **Error Recovery**: Automatic process restart with state restoration
6. **Performance**: Efficient streaming parser, minimal memory overhead
7. **Security**: Process sandboxing, secure credential management
8. **Modularity**: Clean separation between orchestration and agent logic

## Success Metrics

- **Developer Velocity**: 3x faster development through adversarial collaboration
- **Code Quality**: 90%+ test coverage with security validation
- **System Reliability**: 99.9% uptime with automatic recovery
- **Performance**: <100ms latency for agent communication
- **Scalability**: Support for 10+ concurrent agent processes
- **User Experience**: <5 second project setup, instant pause/resume

This specification provides a complete blueprint for building APEX with Claude CLI integration, streaming JSON parsing, and LMDB-based state management. The system is designed for maximum developer productivity through intelligent orchestration of adversarial AI agents.
