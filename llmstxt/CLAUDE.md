# LLMSTXT Documentation Folder

This folder contains comprehensive documentation for the key technologies used in the APEX project.

## Files Overview

### claude.txt
Complete Claude Code SDK documentation including:
- **CLI Usage**: Command-line flags, options, and modes
- **SDK Integration**: Programmatic usage with streaming JSON output
- **MCP Configuration**: Model Context Protocol setup and tool management
- **Output Formats**: Text, JSON, and stream-json formats
- **Session Management**: Continue, resume, and checkpoint functionality
- **Permission System**: Tool access control and security
- **Advanced Features**: Custom system prompts, multi-turn conversations

Key for APEX: Provides the foundation for spawning Claude CLI processes with MCP integration.

### lmdb.txt
Lightning Memory-Mapped Database (LMDB) source code and documentation:
- **Core Implementation**: Complete LMDB C source code
- **API Reference**: Functions for database operations
- **Configuration Options**: Environment settings and performance tuning
- **Utilities**: Command-line tools (mdb_copy, mdb_dump, mdb_stat, etc.)
- **Performance Characteristics**: ACID compliance, memory mapping, cursors

Key for APEX: LMDB serves as the high-performance shared memory system for agent communication.

### mcp.txt
Model Context Protocol specification and client implementations:
- **Architecture**: Client-server communication patterns
- **Protocol Specification**: JSON-RPC message formats and schemas
- **Tool System**: Tool discovery, invocation, and result handling
- **Resource Management**: File and data resource access patterns
- **Transport Layers**: stdio and SSE (Server-Sent Events) support
- **Client Examples**: Integration examples for various applications
- **Security**: Authentication, authorization, and sandboxing

Key for APEX: MCP enables structured communication between Claude agents and the LMDB backend.

## Technology Integration in APEX

1. **Claude CLI** spawns agent processes with streaming JSON output
2. **MCP Protocol** enables agents to communicate through standardized tools
3. **LMDB Database** provides fast, persistent shared memory for agent coordination
4. **Agent Architecture** uses these technologies for adversarial code generation

## Usage Notes

- Reference these files when implementing MCP servers
- Use Claude CLI documentation for process management
- Consult LMDB docs for performance optimization
- Follow MCP patterns for tool development
