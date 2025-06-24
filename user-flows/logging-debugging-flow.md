# Logging & Debugging Flow

## Purpose
Access, filter, analyze, and troubleshoot APEX system logs for debugging agent behavior, task execution, and system performance issues.

## Prerequisites
- APEX project with agents running or recently executed
- Understanding of APEX system architecture
- Access to CLI and memory tools

## Log System Overview

### Log Sources:
- **Agent Logs** - Individual agent activities and decisions
- **System Logs** - APEX orchestration and infrastructure
- **Memory Logs** - Database operations and state changes
- **Process Logs** - Claude CLI process outputs
- **Event Logs** - Task workflow and coordination events

### Log Levels:
- **ERROR** - Critical issues requiring immediate attention
- **WARN** - Warning conditions that should be monitored
- **INFO** - General information about system operation
- **DEBUG** - Detailed diagnostic information

## Accessing Logs

### 1. Agent-Specific Logs

#### View Recent Agent Logs:
```bash
# View supervisor agent logs
uv run apex agent logs supervisor

# View coder agent logs with more lines
uv run apex agent logs coder --lines 100

# View adversary agent logs with specific level
uv run apex agent logs adversary --level error
```

#### Follow Live Logs:
```bash
# Follow supervisor logs in real-time
uv run apex agent logs supervisor --follow

# Follow all agent logs with grep filter
uv run apex agent logs coder --follow --grep "task"
```

### 2. System-Wide Logs

#### APEX System Logs:
```bash
# View APEX orchestration logs
uv run apex memory query "/system/logs/*" --limit 50

# Search for specific error patterns
uv run apex memory query "*error*" --content
```

#### Process Logs:
```bash
# Monitor APEX processes
ps aux | grep -E "(apex|claude)"

# Check system logs for APEX
journalctl -u apex --lines 50 -f  # If running as service
```

### 3. Memory-Based Log Access

#### Query Logs via Memory:
```bash
# Agent communication logs
uv run apex memory query "/agents/*/messages/*"

# Task execution logs
uv run apex memory query "/tasks/*/logs/*"

# Session event logs
uv run apex memory query "/sessions/*/events/*"
```

## Log Filtering and Analysis

### 1. Filtering by Criteria

#### Time-Based Filtering:
```bash
# Logs from specific agent in last hour
uv run apex agent logs supervisor --grep "$(date +%Y-%m-%d\ %H)"

# Filter by timestamp pattern
uv run apex memory query "/logs/*" --content | grep "2025-01-08T1[4-5]"
```

#### Error Analysis:
```bash
# Find all error messages
uv run apex agent logs supervisor --level error -n 200

# Search for specific error types
uv run apex agent logs coder --grep "timeout|failed|exception"

# Memory errors and issues
uv run apex memory query "*error*" --content --limit 100
```

#### Performance Issues:
```bash
# Find slow operations
uv run apex agent logs supervisor --grep "slow|timeout|delay"

# Memory performance issues
uv run apex memory query "*performance*" --content

# Large task execution times
uv run apex agent logs coder --grep "completed.*[0-9][0-9][0-9]ms"
```

### 2. Log Correlation

#### Cross-Agent Analysis:
```bash
# Compare agent activities at same time
for agent in supervisor coder adversary; do
  echo "=== $agent ==="
  uv run apex agent logs $agent --grep "14:30" -n 10
done
```

#### Task-Specific Debugging:
```bash
# Find all logs related to specific task
task_id="task-uuid-123"
uv run apex memory query "*$task_id*" --content

# Agent logs for specific task
uv run apex agent logs coder --grep "$task_id"
```

## Debugging Workflows

### 1. Agent Behavior Debugging

#### Debug Agent Decision Making:
```bash
# Trace supervisor's task assignment logic
uv run apex agent logs supervisor --level debug --grep "assign|task|decision"

# Debug coder's implementation process
uv run apex agent logs coder --level debug --grep "implement|code|solution"

# Debug adversary's review process
uv run apex agent logs adversary --level debug --grep "review|test|security"
```

#### Agent Communication Issues:
```bash
# Check agent message exchange
uv run apex memory query "/coordination/*" --content

# Monitor agent notification system
uv run apex memory watch "/notifications/*" --timeout 60

# Agent status synchronization
uv run apex memory query "/agents/*/status" --content
```

### 2. Task Execution Debugging

#### Failed Task Analysis:
```bash
# Find failed tasks
uv run apex memory query "/tasks/failed/*" --content

# Analyze task failure patterns
uv run apex agent logs supervisor --grep "failed|error" -n 100 | grep -E "(task-[a-z0-9-]+)"

# Check task dependencies
uv run apex memory query "/tasks/pending/*" --content | grep "depends_on"
```

#### Task Performance Issues:
```bash
# Long-running tasks
uv run apex agent logs coder --grep "started.*ago"

# Task timeout issues
uv run apex agent logs supervisor --grep "timeout.*task"

# Resource contention
uv run apex memory query "*resource*" --content --grep "conflict|lock|wait"
```

### 3. System Performance Debugging

#### Memory Usage Issues:
```bash
# Monitor memory growth
watch -n 10 'du -sh apex.db && echo "Keys: $(uv run apex memory query "*" | wc -l)"'

# Find large memory entries
uv run apex memory scan / --limit 100 | sort -k2 -nr | head -20

# Memory access patterns
uv run apex memory watch "*" --timeout 300 | grep -c "READ\|WRITE"
```

#### Process Performance:
```bash
# Monitor APEX process resource usage
top -p $(pgrep -f apex | tr '\n' ',' | sed 's/,$//')

# Check for hung processes
ps aux | grep -E "(apex|claude)" | awk '{print $2, $8, $9, $11}'

# Process communication issues
netstat -an | grep ESTABLISHED | grep apex
```

## Advanced Debugging Techniques

### 1. Debug Mode Activation

#### Enable Debug Logging:
```bash
# Start APEX with debug mode
APEX_LOG_LEVEL=debug uv run apex start

# Enable MCP debug logging
APEX_MCP_DEBUG=1 uv run apex start

# Verbose mode for detailed output
uv run apex start --verbose
```

#### Debug Configuration:
```json
{
  "debug_config": {
    "log_level": "debug",
    "log_agents": true,
    "log_memory": true,
    "log_tasks": true,
    "trace_decisions": true
  }
}
```

### 2. Custom Debug Tools

#### Debug Script for Common Issues:
```bash
#!/bin/bash
# apex_debug.sh - Comprehensive debugging script

echo "=== APEX Debug Report $(date) ==="

# System status
echo "1. System Status:"
uv run apex status 2>&1 | head -20

# Agent health
echo "2. Agent Health:"
for agent in supervisor coder adversary; do
  echo "  === $agent ==="
  uv run apex agent logs $agent --level error -n 5 2>/dev/null || echo "  No error logs"
done

# Recent failures
echo "3. Recent Failures:"
uv run apex memory query "*error*" --content --limit 10 2>/dev/null

# Resource usage
echo "4. Resource Usage:"
ps aux | grep -E "(apex|claude)" | head -10

# Memory issues
echo "5. Memory Issues:"
uv run apex memory query "*" 2>/dev/null | wc -l | xargs echo "Total keys:"
du -sh apex.db 2>/dev/null | xargs echo "Database size:"

# Recent activity
echo "6. Recent Activity:"
uv run apex memory watch "*" --timeout 5 2>/dev/null | head -20
```

### 3. Performance Profiling

#### Profile Agent Performance:
```bash
# Time agent operations
time uv run apex agent logs supervisor -n 100 > /dev/null

# Profile memory operations
time uv run apex memory query "*" > /dev/null

# Monitor agent response times
uv run apex agent logs supervisor --grep "response_time\|duration" -n 50
```

#### Bottleneck Identification:
```bash
# Find slow memory operations
uv run apex memory query "*" | while read key; do
  time uv run apex memory show "$key" > /dev/null 2>&1
done 2>&1 | grep real | sort -k2 -nr | head -10

# Identify communication bottlenecks
uv run apex agent logs supervisor --grep "waiting\|blocked\|timeout" -n 100
```

## Log Management

### 1. Log Rotation and Cleanup

#### Manage Log Volume:
```bash
# Count log entries
uv run apex memory query "/logs/*" | wc -l

# Clean old logs
uv run apex memory query "/logs/*" | grep "2025-01-01" | \
  xargs -I {} uv run apex memory delete {}

# Archive important logs
uv run apex memory query "/logs/error/*" > critical_errors_$(date +%Y%m%d).log
```

### 2. Log Export and Analysis

#### Export Logs for Analysis:
```bash
# Export all agent logs
for agent in supervisor coder adversary; do
  uv run apex agent logs $agent -n 1000 > logs_${agent}_$(date +%Y%m%d_%H%M%S).log
done

# Export memory logs
uv run apex memory query "/logs/*" --content > memory_logs_$(date +%Y%m%d).json

# Create combined log file
{
  echo "=== APEX Combined Logs $(date) ==="
  echo ""
  echo "=== System Logs ==="
  uv run apex memory query "/system/logs/*" --content
  echo ""
  echo "=== Agent Logs ==="
  for agent in supervisor coder adversary; do
    echo "--- $agent ---"
    uv run apex agent logs $agent -n 100
  done
} > apex_combined_$(date +%Y%m%d_%H%M%S).log
```

## Troubleshooting Common Issues

### 1. Agent Communication Problems

#### Debug Agent Coordination:
```bash
# Check message queues
uv run apex memory query "/agents/*/inbox/*"

# Monitor coordination channel
uv run apex memory watch "/coordination/*" --timeout 60

# Verify agent registration
uv run apex memory show /agents/supervisor/status
uv run apex memory show /agents/coder/status
uv run apex memory show /agents/adversary/status
```

### 2. Task Processing Issues

#### Debug Task Stuck in Pending:
```bash
# Check task dependencies
task_id="stuck-task-id"
uv run apex memory show "/tasks/pending/$task_id"

# Verify agent assignment
uv run apex memory query "/agents/*/tasks/pending" | grep "$task_id"

# Check for blocking conditions
uv run apex agent logs supervisor --grep "$task_id" -n 50
```

### 3. Performance Degradation

#### Diagnose Slow Performance:
```bash
# Check memory growth
history_size=$(uv run apex memory query "*" | wc -l)
echo "Total memory keys: $history_size"

# Monitor operation timing
time uv run apex status
time uv run apex memory show /projects/config

# Check for memory leaks
watch -n 30 'ps aux | grep apex | awk "{sum+=\$6} END {print sum/1024 \"MB\"}"'
```

## Logging Integration

### 1. External Log Aggregation

#### Forward to Centralized Logging:
```bash
# Send logs to syslog
uv run apex agent logs supervisor --follow | logger -t apex-supervisor

# Export to ELK stack
uv run apex memory query "/logs/*" --content | \
  curl -X POST "localhost:9200/apex-logs/_doc" -H "Content-Type: application/json" -d @-
```

### 2. Monitoring Integration

#### Integration with Monitoring Systems:
```bash
# Generate metrics from logs
error_count=$(uv run apex agent logs supervisor --level error -n 1000 | wc -l)
echo "apex.errors.count $error_count $(date +%s)" | nc localhost 2003  # Graphite

# Health check based on logs
if uv run apex agent logs supervisor --level error -n 10 | grep -q "critical"; then
  echo "CRITICAL: APEX supervisor has critical errors"
  exit 2
fi
```

## Related Flows
- [Agent Management Flow](agent-management-flow.md) - Understanding agent behavior through logs
- [Status Monitoring Flow](status-monitoring-flow.md) - System monitoring and logging
- [Error Handling Flow](error-handling-flow.md) - Using logs for error recovery
- [Memory Management Flow](memory-management-flow.md) - Memory-based log storage
