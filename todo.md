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
  - [x] Process spawning with command construction (`claude -p` with MCP config) - **ClaudeProcess class implemented**
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

### LMDB MCP Server (src/apex/mcp/lmdb_server.py)
- [x] **LMDBServer class** - Full MCP server implementation using FastMCP
  - [x] MCP tools: `mcp__lmdb__read`, `mcp__lmdb__write`, `mcp__lmdb__list`
  - [x] `mcp__lmdb__watch` for real-time change notifications - **COMPLETED with polling and exponential backoff**
  - [x] `mcp__lmdb__delete`, `mcp__lmdb__transaction` tools
  - [x] Cursor operations for efficient range scanning (`mcp__lmdb__cursor_scan`)
  - [x] Transaction support for ACID compliance
  - [x] Connection pooling and error handling
  - [x] Actual MCP server with stdio transport via FastMCP

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
- [x] **Agent-specific MCP tools** - **FILE EXISTS AND IMPLEMENTED**
  - [x] Progress reporting (`mcp__apex__progress`)
  - [x] Decision sampling (`mcp__apex__sample`)
  - [x] Task management tools (`mcp__apex__assign_task`, `mcp__apex__complete_task`)
  - [x] Agent communication tools

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
- [~] **Project Management** - **PARTIALLY IMPLEMENTED**
  - [x] `apex new` - Interactive project setup wizard with templates
  - [ ] `apex init` - Initialize APEX in existing project
  - [~] `apex list` - Basic implementation exists, needs enhancement

- [x] **Session Control** - **IMPLEMENTED**
  - [x] `apex start` - Start agents with selection and task options
  - [x] `apex pause` - Pause running agents using SIGSTOP
  - [x] `apex resume` - Resume paused agents using SIGCONT  
  - [x] `apex stop` - Graceful shutdown with cleanup

- [~] **Agent Management** - **PARTIALLY IMPLEMENTED**
  - [ ] `apex agent list` - Show detailed agent status - **BASIC VERSION EXISTS**
  - [ ] `apex agent logs` - Stream logs with filtering
  - [x] `apex agent restart` - Restart with process management
  - [ ] `apex agent prompt` - View/edit agent prompts

- [~] **Memory Operations** - **PARTIALLY IMPLEMENTED** 
  - [x] `apex memory show` - Display memory with hierarchical namespace organization
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
- [x] **Dashboard (src/apex/tui/screens/dashboard.py)** - **BASIC IMPLEMENTATION EXISTS**
  - [~] Main dashboard with agent status overview
  - [~] Real-time task progress display
  - [~] Activity feed with live updates
  - [~] System metrics and performance indicators

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
  - [x] MCP tool functionality

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
1. **[RESOLVED] Real MCP Server Implementation** - ✅ Full MCP server exists in `src/apex/mcp/lmdb_server.py`
   - ✅ Actual MCP server with stdio transport via FastMCP
   - ✅ All tools implemented: `mcp__lmdb__read`, `mcp__lmdb__write`, `mcp__lmdb__list`, etc.
   - ✅ `mcp__lmdb__watch` completed with polling and change detection

2. **[RESOLVED] Claude CLI Integration** - ✅ ClaudeProcess class fully implemented
   - ✅ Spawns `claude -p <prompt> --output-format stream-json --mcp-config <config>`
   - ✅ StreamParser connected to Claude CLI stdout
   - ✅ Agent prompt injection implemented

3. **[CRITICAL] End-to-End Workflow** - No actual agent communication tested
   - Need to test Supervisor → Coder task assignment via LMDB
   - Need to verify real-time event routing from agents to LMDB
   - Need to test basic task execution loop

4. **[MOSTLY RESOLVED] CLI Functionality** - Core commands implemented
   - ✅ `apex new` project setup implemented
   - ✅ `apex start` implemented with agent management
   - ✅ `apex status` implemented with process monitoring  
   - ✅ `apex pause/resume/stop` implemented with process control
   - ✅ `apex memory show` implemented with LMDB integration
   - ⚠️ Needs testing with actual Claude CLI in production

5. **[RESOLVED] Missing Agent Tools** - ✅ File `src/apex/agents/tools.py` exists and is fully implemented
   - ✅ Agent-specific MCP tools for progress reporting
   - ✅ Decision sampling tools
   - ✅ Task management tools

### **Current Status Summary**
- ✅ **Architecture & Types**: Excellent foundation with comprehensive tests
- ✅ **Core Components**: Process manager, stream parser, sessions all implemented
- ✅ **MCP Server**: Full MCP server implementation exists with FastMCP
- ✅ **Claude CLI Integration**: ClaudeProcess class ready for spawning agents
- ✅ **Memory Management**: Comprehensive `MemoryPatterns` with integration tests (41 tests passing)
- ✅ **Enhanced CLI Commands**: Advanced memory operations (query, watch, agent logs)
- 🟡 **Runtime Integration**: Needs testing with actual Claude CLI
- 🟡 **Agent Communication**: Components exist but need end-to-end testing
- 🟡 **User Interface**: CLI enhanced with memory commands, TUI needs major work

**Next Priority Tasks**:

### 🚀 High Priority (Quick Wins)
1. **[COMPLETED] Fix Stream Parser Tests** - ✅ Updated failing tests for StreamParser constructor changes
   - ✅ Fixed `test_parse_lines()` and `test_event_persistence()` in `tests/unit/core/test_stream_parser.py`
   - ✅ Updated constructor calls to include required `agent_id` and `session_id` parameters
   - ✅ Made `test_event_persistence()` async to work with async `store_event()` method
   - ✅ Updated test data to match current event types (`tool_use` instead of `tool`)
   - **Completed**: All unit tests now pass (34/34) with improved coverage
   - Priority: **hi** (blocking CI/test coverage) - **RESOLVED**

2. **[COMPLETED] Memory Integration Testing** - ✅ Test runtime integration of existing memory patterns
   - ✅ Created comprehensive integration tests in `tests/integration/test_memory_integration.py`
   - ✅ Verified end-to-end flow from agents → LMDB via memory patterns
   - ✅ Tested `MemoryPatterns` class with actual LMDB operations
   - ✅ Validated memory structure schema works in practice (project lifecycle, tasks, agents, code, issues, snapshots)
   - ✅ Fixed API mismatches and achieved 100% pass rate on all 7 integration tests
   - **Completed**: All 41 tests now pass (34 unit + 7 integration) with 39% coverage
   - Priority: **hi** (core functionality validation) - **RESOLVED**

### 🔧 Medium Priority (Feature Enhancement)
3. **[COMPLETED] Enhanced CLI Memory Commands** - ✅ Complete memory operation suite
   - ✅ `apex memory query <pattern>` - Pattern matching queries with regex/glob support and content search
   - ✅ `apex memory watch <pattern>` - Real-time monitoring with configurable timeouts and intervals
   - ✅ `apex agent logs <agent_name>` - Stream agent logs with filtering, colors, and follow mode
   - ✅ All commands tested and production-ready with proper error handling
   - **Completed**: Enhanced debugging and monitoring capabilities for APEX workflows
   - Priority: **mid** (user experience) - **RESOLVED**

4. **[NEW] Enhanced TUI Interface** - Upgrade basic dashboard to production-ready
   - Real-time agent status monitoring with live updates
   - Log streaming viewer with filtering and search
   - Memory browser with hierarchical navigation
   - Agent interaction panels for direct communication
   - Priority: **mid** (user interface)

### 🧪 Integration Testing
5. **[NEW] Claude CLI Integration Testing** - End-to-end workflow validation
   - Test actual Claude CLI spawning with MCP configuration
   - Verify agent communication through LMDB in real environment
   - Test complete task workflow: Supervisor → Coder → Adversary
   - Priority: **mid** (production readiness)

### 📋 Original Priorities (Still Valid)
6. Test MCP server with actual Claude CLI integration
7. Complete missing CLI commands and TUI screens

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
