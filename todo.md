# APEX Development Task List

This roadmap derives from [`specs.md`](specs.md) and lists the concrete steps needed to build APEX. Tasks are organized by team and module to enable parallel development without merge conflicts.

## Style Guide
- `[ ]` task not started
- `[~]` task in progress (semaphore)
- `[x]` task complete
- **Owner**: Team member assigned to this area
- **Dependencies**: Other modules this depends on
- Priorities: **hi**, **mid**, **lo**

---

## 🏗️ Team Alpha: Core Infrastructure
**Owner**: TBD | **Priority**: **hi** | **Dependencies**: None

### Process Management (src/apex/core/process_manager.py)
- [x] **ProcessManager class** - Core Claude CLI process orchestration
  - [x] Agent process lifecycle (start, stop, restart, health check)
  - [~] Process spawning with command construction (`claude -p` with MCP config) - **NEEDS REAL CLAUDE CLI INTEGRATION**
  - [x] Process monitoring and automatic restart on failure
  - [x] Resource monitoring (memory, CPU per process)
  - [x] Clean shutdown and cleanup procedures

### Stream Parser (src/apex/core/stream_parser.py)
- [x] **StreamParser class** - Real-time JSON parsing from Claude CLI
  - [x] Typed event classes (SystemEvent, AssistantEvent, ToolCallEvent)
  - [x] Streaming JSON line-by-line parsing with error handling
  - [~] Event routing and storage in LMDB - **PARTIALLY IMPLEMENTED**
  - [x] Event filtering and pattern matching
  - [ ] Event replay system for session continuation

### LMDB MCP Server (src/apex/core/lmdb_mcp.py)
- [~] **LMDBMCP class** - MCP server for shared memory - **NEEDS REAL MCP SERVER IMPLEMENTATION**
  - [x] MCP tools: `mcp__lmdb__read`, `mcp__lmdb__write`, `mcp__lmdb__list`
  - [ ] `mcp__lmdb__watch` for real-time change notifications
  - [x] `mcp__lmdb__delete`, `mcp__lmdb__transaction` tools
  - [ ] Cursor operations for efficient range scanning
  - [ ] Transaction support for ACID compliance
  - [ ] Connection pooling and error handling
  - [ ] **CRITICAL**: Convert to actual MCP server with stdio transport

### Memory Management (src/apex/core/memory.py)
- [ ] **Memory structure schema** - LMDB organization
  - [ ] Memory access patterns for different data types
  - [ ] Memory indexing and efficient querying
  - [ ] Memory snapshots for checkpoints
  - [ ] Memory cleanup and garbage collection

---

## 🤖 Team Beta: Agent System
**Owner**: TBD | **Priority**: **hi** | **Dependencies**: Team Alpha (LMDB MCP)

### Agent Prompts (src/apex/agents/prompts.py)
- [x] **AgentPrompts class** - Dynamic prompt generation
  - [x] Supervisor agent prompt (task coordination, git operations)
  - [x] Coder agent prompt (implementation, code writing)
  - [x] Adversary agent prompt (testing, security, quality)
  - [x] Dynamic prompt generation based on project config
  - [x] Prompt versioning and templates

### Agent Coordinator (src/apex/agents/coordinator.py)
- [x] **AgentCoordinator class** - Inter-agent communication
  - [x] Task assignment and distribution logic
  - [x] Conflict resolution between agents
  - [x] Progress tracking and reporting
  - [x] Agent priority and scheduling system

### MCP Tools (src/apex/agents/tools.py)
- [ ] **Agent-specific MCP tools** - **FILE MISSING**
  - [ ] Progress reporting (`mcp__apex__progress`)
  - [ ] Decision sampling (`mcp__apex__sample`)
  - [ ] Task management tools
  - [ ] Agent communication tools

### Agent Lifecycle (src/apex/agents/lifecycle.py)
- [x] **Lifecycle management**
  - [x] Agent startup/shutdown procedures
  - [x] Health monitoring and status tracking
  - [x] Failover and recovery mechanisms
  - [x] Configuration hot-reloading

---

## 🔄 Team Gamma: Orchestration & Continuation
**Owner**: TBD | **Priority**: **mid** | **Dependencies**: Team Alpha, Team Beta

### Session Management (src/apex/orchestration/session.py)
- [x] **SessionManager class** - Session lifecycle
  - [x] Session creation, tracking, cleanup
  - [x] Session metadata and configuration
  - [x] Session sharing and collaboration
  - [x] Session templates and presets

### Continuation System (src/apex/orchestration/continuation.py)
- [x] **ContinuationManager class** - Pause/resume functionality
  - [x] Comprehensive checkpoint system
  - [x] State serialization/deserialization
  - [x] Incremental checkpoints for efficiency
  - [x] Checkpoint validation and integrity

### Orchestration Engine (src/apex/orchestration/engine.py)
- [x] **OrchestrationEngine class** - Main workflow control
  - [x] Workflow definition and execution
  - [x] Task scheduling and dependency management
  - [x] Load balancing across agents
  - [x] Error recovery and retry mechanisms

### State Management (src/apex/orchestration/state.py)
- [~] **State persistence** - LMDB backend state management - **NEEDS RUNTIME INTEGRATION**
  - [ ] State versioning and migration
  - [ ] State backup and recovery
  - [ ] State synchronization across processes

### Event Processing (src/apex/orchestration/events.py)
- [x] **Event system** - Event bus and processing
  - [x] Event publishing and routing
  - [x] Event persistence and replay
  - [x] Event-driven workflows

---

## 🖥️ Team Delta: CLI/TUI Interface
**Owner**: TBD | **Priority**: **mid** | **Dependencies**: Team Alpha, Team Beta

### CLI Commands Enhancement (src/apex/cli/commands.py)
- [~] **Project Management** - **STUBS ONLY, NEED IMPLEMENTATION**
  - [ ] `apex new` - Interactive project setup wizard with templates
  - [ ] `apex init` - Initialize APEX in existing project
  - [ ] `apex list` - List projects with status display

- [~] **Session Control** - **STUBS ONLY, NEED IMPLEMENTATION**
  - [ ] `apex start` - Start agents with selection and task options
  - [ ] `apex pause` - Pause with checkpoint creation
  - [ ] `apex resume` - Resume from checkpoint with state restoration
  - [ ] `apex stop` - Graceful shutdown

- [~] **Agent Management** - **STUBS ONLY, NEED IMPLEMENTATION**
  - [ ] `apex agent list` - Show detailed agent status
  - [ ] `apex agent logs` - Stream logs with filtering
  - [ ] `apex agent restart` - Restart with state preservation
  - [ ] `apex agent prompt` - View/edit agent prompts

- [~] **Memory Operations** - **STUBS ONLY, NEED IMPLEMENTATION**
  - [ ] `apex memory show` - Display memory with formats (json/yaml/table)
  - [ ] `apex memory query` - Query with pattern matching
  - [ ] `apex memory export/import` - Snapshot management
  - [ ] `apex memory watch` - Real-time monitoring

- [ ] **Git Integration**
  - [ ] `apex git status` - Enhanced git status with APEX annotations
  - [ ] `apex git log` - Show commits with task/agent info
  - [ ] `apex git auto-commit` - Intelligent commit messages

- [ ] **GitHub Integration**
  - [ ] `apex github pr create/list/merge` - PR management
  - [ ] `apex github issue create` - Issue creation with auto-labeling
  - [ ] `apex github release create` - Release automation

### TUI Interface (src/apex/tui/)
- [ ] **Dashboard (src/apex/tui/screens/dashboard.py)**
  - [ ] Main dashboard with agent status overview
  - [ ] Real-time task progress display
  - [ ] Activity feed with live updates
  - [ ] System metrics and performance indicators

- [ ] **Agent View (src/apex/tui/screens/agents.py)**
  - [ ] Split-view agent monitoring
  - [ ] Individual agent log streaming
  - [ ] Agent interaction panels
  - [ ] Agent performance visualizations

- [ ] **Memory View (src/apex/tui/screens/memory.py)**
  - [ ] Memory browser with hierarchical navigation
  - [ ] Memory search and filtering
  - [ ] Memory visualization and charts
  - [ ] Memory editing tools

- [ ] **Logs View (src/apex/tui/screens/logs.py)**
  - [ ] Unified log viewer with filtering
  - [ ] Log search and highlighting
  - [ ] Log export and sharing
  - [ ] Log analytics and insights

### TUI Widgets (src/apex/tui/widgets/)
- [ ] **Custom Widgets**
  - [ ] Agent status widgets with real-time updates
  - [ ] Progress bars and gauges
  - [ ] Interactive tables and lists
  - [ ] Charts and graphs for metrics
  - [ ] Notification and alert widgets

---

## 🧪 Testing & Quality
**Owner**: TBD | **Priority**: **hi** | **Dependencies**: All teams

### Unit Tests
- [x] **Core Infrastructure Tests (tests/unit/core/)**
  - [x] Process management functionality
  - [x] Stream parsing and event handling
  - [x] LMDB operations and MCP compliance
  - [ ] Memory management and persistence

- [x] **Agent System Tests (tests/unit/agents/)**
  - [x] Agent prompt generation
  - [x] Agent coordination and communication
  - [x] Agent lifecycle management
  - [ ] MCP tool functionality - **MISSING TOOLS FILE**

- [x] **Orchestration Tests (tests/unit/orchestration/)**
  - [x] Session management
  - [x] Continuation system
  - [x] State persistence
  - [x] Event processing

### Integration Tests
- [ ] **End-to-End Workflows (tests/integration/)**
  - [ ] Complete project setup to execution
  - [ ] Agent collaboration scenarios
  - [ ] Pause/resume functionality
  - [ ] Error recovery and failover

### MCP Compliance Tests
- [ ] **MCP Protocol Tests (tests/mcp/)**
  - [ ] MCP server compliance
  - [ ] Tool discovery and invocation
  - [ ] Error handling and responses
  - [ ] Security and authentication

---

## 📊 Monitoring & Analytics
**Owner**: TBD | **Priority**: **lo** | **Dependencies**: Core features

### Performance Monitoring
- [ ] **Metrics Collection**
  - [ ] System performance metrics
  - [ ] Agent performance tracking
  - [ ] Memory usage monitoring
  - [ ] Latency and throughput metrics

### Analytics & Insights
- [ ] **Analytics Engine**
  - [ ] Usage analytics
  - [ ] Performance insights
  - [ ] Predictive analytics
  - [ ] Optimization recommendations

---

## 🔒 Security & Compliance
**Owner**: TBD | **Priority**: **mid** | **Dependencies**: Core features

### Security Implementation
- [ ] **Authentication & Authorization**
  - [ ] OAuth 2.0 for remote MCP servers
  - [ ] TLS for SSE transport
  - [ ] API key management
  - [ ] Role-based access control

### Data Protection
- [ ] **Privacy & Encryption**
  - [ ] Data encryption at rest
  - [ ] Secure communication protocols
  - [ ] Data retention policies
  - [ ] GDPR compliance

---

## 🎯 Development Milestones

### Phase 1: Core Foundation (MVP) - **Priority: hi**
1. **Process Manager** - Basic Claude CLI spawning and management
2. **Stream Parser** - JSON event processing from Claude CLI
3. **Basic LMDB MCP Server** - Core read/write/list operations
4. **Simple CLI** - `new`, `start`, `status`, `version` commands
5. **Basic Agent Prompts** - Supervisor, Coder, Adversary templates

### Phase 2: Agent System - **Priority: hi**
1. **Agent Lifecycle Management** - Complete startup/shutdown/health
2. **Advanced MCP Tools** - Progress, sampling, communication tools
3. **Agent Coordination** - Task assignment and progress tracking
4. **Enhanced CLI** - Agent management commands
5. **Basic TUI Dashboard** - Real-time agent monitoring

### Phase 3: Advanced Features - **Priority: mid**
1. **Continuation System** - Pause/resume with checkpoints
2. **Complete CLI** - All memory, git, github commands
3. **Full TUI Interface** - All views (dashboard, agents, memory, logs)
4. **Git Integration** - Auto-commit and enhanced git operations
5. **Performance Monitoring** - Metrics and analytics

### Phase 4: Enterprise Features - **Priority: lo**
1. **Security & Auth** - OAuth, TLS, RBAC
2. **GitHub Integration** - Full PR/issue/release automation
3. **Advanced Analytics** - Insights and optimization
4. **Compliance Features** - Audit, data protection
5. **Scalability** - Distributed execution, clustering

---

## 🚨 CRITICAL IMPLEMENTATION GAPS

### **Phase 1 - BLOCKING ISSUES (Must Fix First)**
1. **[CRITICAL] Real MCP Server Implementation** - Current LMDBMCP is just a class, not an MCP server
   - Convert to actual MCP server with stdio transport
   - Implement missing tools: `mcp__lmdb__watch`, `mcp__lmdb__cursor_scan`, `mcp__lmdb__transaction`
   - Add MCP protocol compliance

2. **[CRITICAL] Claude CLI Integration** - ProcessManager doesn't spawn real Claude CLI processes
   - Update to spawn `claude -p <prompt> --output-format stream-json --mcp-config <config>`
   - Connect StreamParser to actual Claude CLI stdout
   - Implement agent prompt injection

3. **[CRITICAL] End-to-End Workflow** - No actual agent communication
   - Implement Supervisor → Coder task assignment via LMDB
   - Add real-time event routing from agents to LMDB
   - Create basic task execution loop

4. **[HIGH] CLI Functionality** - All commands are non-functional stubs
   - Implement `apex new` project setup
   - Make `apex start` actually spawn agents
   - Add `apex status` for monitoring

5. **[HIGH] Missing Agent Tools** - File `src/apex/agents/tools.py` doesn't exist
   - Create agent-specific MCP tools for progress reporting
   - Add decision sampling tools
   - Implement task management tools

### **Current Status Summary**
- ✅ **Architecture & Types**: Excellent foundation with comprehensive tests
- ✅ **Core Components**: Process manager, stream parser, sessions all implemented
- 🔴 **Runtime Integration**: No actual Claude CLI spawning or MCP server
- 🔴 **Agent Communication**: Components exist but not connected
- 🔴 **User Interface**: CLI commands are stubs only

**Next Priority**: Focus on making the MCP server functional and connecting Claude CLI processes.

---

## 📋 Task Assignment Template

When claiming a task, update with:
```markdown
- [~] **Task Name** - Brief description
  **Owner**: @username | **Started**: YYYY-MM-DD | **ETA**: YYYY-MM-DD
  **Dependencies**: List any blocking tasks
  **Notes**: Any implementation details or decisions
```

When completing:
```markdown
- [x] **Task Name** - Brief description
  **Owner**: @username | **Completed**: YYYY-MM-DD
  **PR**: #123 | **Tests**: Added/Updated
```

This comprehensive task breakdown covers all aspects specified in `specs.md` and provides clear ownership and dependency tracking for efficient parallel development.
