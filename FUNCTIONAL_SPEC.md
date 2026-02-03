# APEX System - Functional Specification v2.0

## 1. Overview

APEX (Adversarial Pair EXecution) is a production-ready orchestration platform that coordinates multiple Claude Code instances to accomplish complex software development tasks. Rather than traditional multi-agent conversation systems, APEX uses a centralized supervisor that orchestrates ephemeral workers through shared memory, enabling unprecedented reliability and scalability in AI-assisted development.

The system transforms user goals into structured task sequences, assigns specialized roles to Claude Code workers, and manages execution through sophisticated state management and process orchestration.

## 2. Core Concepts

### 2.1. System Architecture

*   **Supervisor**: The central orchestrator that analyzes goals, creates task plans, and coordinates worker execution. Acts as a persistent "project manager" for the entire development process.

*   **Workers**: Ephemeral Claude Code processes that execute discrete tasks. Each worker is specialized for a specific role (Coder, Adversary) and terminates after completing its assigned task.

*   **TaskBriefing**: A structured specification that defines exactly what a worker should accomplish, including deliverables, context pointers, and success criteria.

*   **Shared Memory**: An LMDB database that serves as the communication hub, storing project state, task specifications, code artifacts, and execution results.

*   **MCP Integration**: Model Context Protocol tools that enable Claude Code instances to interact with APEX's shared memory seamlessly.

### 2.2. Worker Specialization

*   **Coder**: Specializes in implementation tasks - writing code, creating features, refactoring, and building functionality.

*   **Adversary**: Focuses on quality assurance - testing code, finding vulnerabilities, reviewing implementations, and ensuring security.

*   **Supervisor**: Handles orchestration - planning tasks, managing git operations, creating documentation, and coordinating overall project flow.

### 2.3. Project Management

*   **Project**: A complete development context with its own configuration, shared memory database, and git repository.

*   **Session**: A specific orchestration instance within a project, with checkpointing capabilities for pause/resume functionality.

*   **Utilities**: Built-in tools for testing, linting, security scanning, documentation generation, and deployment automation.

## 3. System Capabilities & Features

### 3.1. Orchestration Engine

*   **Goal Analysis**: Automatically categorizes user goals (implementation, bug fix, analysis, deployment) and selects appropriate workflow templates.

*   **Task Planning**: Breaks down complex goals into 3-5 discrete tasks with clear dependencies and success criteria.

*   **Worker Management**: Spawns, monitors, and terminates Claude Code worker processes with role-specific prompts and tool permissions.

*   **Progress Tracking**: Real-time monitoring of task execution with detailed progress reporting and error handling.

### 3.2. State Management

*   **Persistent Memory**: All project state, task specifications, and execution results are stored in LMDB for reliability and performance.

*   **Session Continuity**: Complete checkpoint and resume capabilities - pause orchestration at any point and resume with full context restoration.

*   **Process Recovery**: Automatic restart of failed workers with full state restoration and error recovery.

### 3.3. Claude Code Integration

*   **Native MCP Tools**: Provides `apex_lmdb_read`, `apex_lmdb_write`, `apex_project_status`, and other tools for seamless integration.

*   **Automatic Configuration**: Creates `.mcp.json` files automatically when initializing projects.

*   **Transparent Operation**: Users can interact with APEX through familiar Claude Code interfaces while benefiting from orchestration.

### 3.4. Advanced Interfaces

*   **Live TUI Dashboard**: Real-time visualization of task progress, worker status, and system resources with interactive controls.

*   **Advanced CLI**: Complete command suite for orchestration control, project management, and resource monitoring.

*   **Supervisor Chat**: Direct communication interface for real-time orchestration control and status queries.

### 3.5. Enterprise Features

*   **Multi-Project Support**: Manage multiple projects with isolated state and resources.

*   **Resource Monitoring**: Track worker CPU, memory usage, and task completion metrics.

*   **Security Integration**: Built-in security scanning and validation throughout the development process.

*   **Git Integration**: Automatic version control with commit generation and PR management.

## 4. User Interaction Flows

### 4.1. Basic Project Creation and Orchestration

1. **Project Initialization**
   ```bash
   uv run apex new calculator --tech "Python"
   cd calculator
   ```

2. **Goal-Based Orchestration**
   ```bash
   uv run apex orchestrate "Create a calculator with add, subtract, multiply, and divide functions"
   ```

3. **System Response**
   - Supervisor analyzes goal as "implementation task"
   - Creates task sequence: Research → Implement → Test → Document
   - Spawns Coder worker for implementation
   - Spawns Adversary worker for testing
   - Integrates results and reports completion

### 4.2. Claude Code Integration Workflow

1. **Automatic MCP Setup**
   ```bash
   uv run apex new todo-api --tech "Python,FastAPI"
   cd todo-api
   claude  # Automatically loads APEX MCP server
   ```

2. **Multi-Agent Coordination**
   ```
   # In Claude Code session
   > apex_lmdb_write /projects/todo-123/tasks/implement-auth '{"role": "Coder", "task": "Implement JWT authentication", "priority": "high"}'

   > apex_lmdb_write /projects/todo-123/tasks/test-auth '{"role": "Adversary", "task": "Test authentication security", "priority": "high"}'

   > apex_project_status todo-123
   ```

3. **Coordinated Execution**
   - Multiple Claude Code instances can work on the same project
   - Tasks are coordinated through shared memory
   - Real-time progress tracking and result integration

### 4.3. Advanced Monitoring and Control

1. **Live TUI Interface**
   ```bash
   uv run apex tui
   ```
   - Real-time task graph visualization
   - Worker status monitoring
   - Interactive orchestration control
   - Direct supervisor communication

2. **Resource Management**
   ```bash
   uv run apex workers status --detailed
   uv run apex utilities list --running
   uv run apex projects list --detailed
   ```

3. **Session Management**
   ```bash
   uv run apex pause    # Checkpoint current state
   uv run apex resume   # Resume from checkpoint
   ```

### 4.4. Enterprise Deployment

1. **Multi-Project Orchestration**
   ```bash
   uv run apex orchestrate "Deploy microservices to production" \
     --workers 5 \
     --strategy quality \
     --mode supervised
   ```

2. **Plan Management**
   ```bash
   uv run apex plan create "Security audit" --template security
   uv run apex plan show --format tree --detailed
   ```

3. **Resource Scaling**
   ```bash
   uv run apex workers scale --count 10
   uv run apex utilities run SecurityScanner --parallel
   ```

## 5. Input and Output Specifications

### 5.1. System Inputs

*   **User Goals**: Natural language descriptions of development objectives
   - "Implement user authentication system"
   - "Fix the database connection timeout issue"
   - "Add API documentation and deploy to staging"

*   **Project Configuration**: JSON configuration files defining project metadata
   ```json
   {
     "project_id": "unique-id",
     "tech_stack": ["Python", "FastAPI", "SQLAlchemy"],
     "project_type": "Web API",
     "features": ["auth", "database", "api"]
   }
   ```

*   **Workspace Files**: Existing codebase and project files that workers can analyze and modify

### 5.2. System Outputs

*   **Code Artifacts**: New or modified source code files, configuration files, and documentation
   - Implementation files with clean, tested code
   - Test suites with comprehensive coverage
   - Documentation with API specifications

*   **Execution Reports**: Detailed logs and summaries of orchestration progress
   - Task completion status and timelines
   - Worker performance metrics
   - Error reports and resolution steps

*   **Project State**: Persistent project information stored in LMDB
   - Task specifications and results
   - Code artifacts and versions
   - Session history and checkpoints

*   **Git Integration**: Automatic version control with meaningful commit messages
   - Structured commits for each task completion
   - Pull request generation for feature branches
   - Issue tracking integration

## 6. Technical Implementation

### 6.1. Architecture Patterns

*   **Orchestration over Conversation**: Centralized coordination rather than peer-to-peer agent communication
*   **Ephemeral Workers**: Stateless, task-focused processes that terminate after completion
*   **Context-as-a-Service**: Shared memory provides context to workers rather than maintaining conversation history
*   **Template-Based Planning**: Proven workflow templates rather than emergent AI planning

### 6.2. Performance Characteristics

*   **Sub-100ms Agent Communication**: LMDB enables ultra-fast inter-process communication
*   **Concurrent Execution**: Multiple workers can execute tasks in parallel
*   **Minimal Memory Footprint**: Ephemeral workers prevent memory accumulation
*   **Automatic Recovery**: Failed workers are automatically restarted with full context

### 6.3. Integration Capabilities

*   **Claude Code Native**: Deep integration through MCP with automatic configuration
*   **Git Operations**: Direct git and GitHub CLI integration for version control
*   **Development Tools**: Built-in integration with testing, linting, and security tools
*   **Extensible Architecture**: Plugin system for custom utilities and worker types

## 7. Success Metrics and Validation

### 7.1. Task Completion Metrics

*   **Success Rate**: Percentage of tasks completed successfully
*   **Quality Score**: Code quality metrics from integrated linting and testing
*   **Security Score**: Security validation results from built-in scanning
*   **Performance Metrics**: Task completion time and resource utilization

### 7.2. System Health Indicators

*   **Worker Availability**: Percentage of workers successfully spawned and executing
*   **Memory Health**: LMDB database performance and integrity
*   **Process Stability**: Worker crash rate and recovery success
*   **Integration Status**: MCP tool availability and Claude Code connectivity

## 8. Future Capabilities

### 8.1. Planned Enhancements

*   **Distributed Orchestration**: Multi-machine worker deployment
*   **AI-Powered Planning**: Dynamic task generation based on project analysis
*   **Enterprise SSO**: Role-based access control and team collaboration
*   **Advanced Analytics**: ML-powered performance optimization and predictive planning

### 8.2. Ecosystem Integration

*   **IDE Plugins**: Direct integration with VS Code, JetBrains, and other development environments
*   **CI/CD Integration**: Native pipeline integration for automated deployment
*   **Cloud Deployment**: Managed APEX instances for enterprise teams
*   **Custom Worker Types**: Domain-specific workers for specialized development tasks

## Conclusion

APEX v2.0 represents a paradigm shift in AI-assisted development, moving beyond experimental multi-agent systems to deliver a production-ready orchestration platform. By combining sophisticated task planning, ephemeral worker management, and native Claude Code integration, APEX provides unprecedented reliability and scalability for complex software development projects.

The system's architecture demonstrates a mature understanding of both AI capabilities and software development workflows, resulting in a platform that amplifies human productivity while maintaining the reliability and control required for professional software development.
