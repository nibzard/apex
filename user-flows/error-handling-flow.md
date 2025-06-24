# Error Handling Flow

## Purpose
Handle errors, failures, and recovery scenarios in APEX multi-agent systems including agent crashes, task failures, communication errors, and system recovery procedures.

## Prerequisites
- Understanding of APEX system architecture
- Access to logging and monitoring tools
- Knowledge of agent coordination mechanisms

## Error Categories

### 1. Agent-Level Errors
- **Agent Crash** - Agent process terminates unexpectedly
- **Agent Timeout** - Agent becomes unresponsive
- **Agent Resource Exhaustion** - Memory or CPU limits exceeded
- **Agent Configuration Error** - Invalid agent settings

### 2. Task-Level Errors
- **Task Execution Failure** - Task cannot be completed
- **Task Timeout** - Task exceeds time limits
- **Task Dependency Failure** - Required tasks fail
- **Task Resource Conflict** - Multiple agents accessing same resource

### 3. System-Level Errors
- **Database Corruption** - LMDB database issues
- **Memory Exhaustion** - System running out of memory
- **Network Connectivity** - MCP communication failures
- **Configuration Errors** - Invalid system configuration

### 4. Communication Errors
- **Message Delivery Failure** - Inter-agent communication fails
- **Protocol Errors** - Invalid MCP messages
- **Coordination Failures** - Agent synchronization issues

## Error Detection

### 1. Automatic Error Detection

#### Health Check System:
```bash
# Monitor agent health
uv run apex status
# Check for error indicators: stopped agents, high memory usage

# Monitor task failures
uv run apex memory query "/tasks/failed/*" --limit 10

# Check system logs for errors
uv run apex agent logs supervisor --level error -n 50
```

#### Error Detection in Memory:
```json
{
  "error_detection": {
    "agent_health_check": {
      "frequency": "60 seconds",
      "indicators": ["process_status", "memory_usage", "response_time"],
      "thresholds": {
        "memory_limit": "500MB",
        "response_timeout": "30 seconds",
        "cpu_usage": "90%"
      }
    },
    "task_monitoring": {
      "timeout_detection": true,
      "dependency_checking": true,
      "resource_conflict_detection": true
    }
  }
}
```

### 2. Agent Self-Reporting

#### Agent Error Reporting:
```
Coder> I encountered an error during task execution that I cannot resolve.

> apex_lmdb_write /errors/agent-errors/coder-001 '{
  "error_id": "coder-error-001",
  "agent": "coder",
  "error_type": "task_execution_failure",
  "task_id": "implement-auth-system",
  "error_details": {
    "description": "Unable to import required cryptography library",
    "exception": "ModuleNotFoundError: No module named cryptography",
    "context": "Attempting to implement password hashing"
  },
  "impact": "Cannot complete authentication implementation",
  "recovery_attempted": false,
  "escalation_needed": true
}'
```

## Error Response Procedures

### 1. Agent Crash Recovery

#### Automatic Agent Restart:
```bash
# Detect agent crash
if ! ps aux | grep -q "claude.*supervisor"; then
  echo "Supervisor agent crashed - initiating recovery"

  # Store crash information
  uv run apex memory write /errors/crashes/supervisor-$(date +%s) '{
    "crashed_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "agent": "supervisor",
    "last_task": "planning-user-dashboard",
    "memory_usage": "150MB",
    "uptime": "2h 30m"
  }'

  # Restart agent with previous context
  uv run apex agent restart supervisor
fi
```

#### Manual Recovery Process:
```bash
# 1. Assess crash impact
uv run apex memory show /agents/supervisor/status
uv run apex memory query "/tasks/pending/*" | grep supervisor

# 2. Save current state
uv run apex memory write /recovery/supervisor-state "$(date)" '{
  "pending_tasks": ["task-001", "task-002"],
  "last_coordination": "dashboard-planning",
  "recovery_timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'

# 3. Restart with state recovery
uv run apex start --agents supervisor --continue last
```

### 2. Task Failure Recovery

#### Task Failure Analysis:
```
Supervisor> Analyzing failed task and determining recovery strategy.

> apex_lmdb_write /errors/task-failures/analysis-001 '{
  "analyzer": "supervisor",
  "failed_task": "implement-payment-processing",
  "failure_reason": "External API dependency unavailable",
  "impact_assessment": {
    "blocked_tasks": ["payment-testing", "integration-testing"],
    "affected_agents": ["coder", "adversary"],
    "timeline_impact": "2-day delay"
  },
  "recovery_options": [
    {
      "option": "retry_with_fallback",
      "description": "Implement mock payment service for development",
      "effort": "4 hours",
      "risk": "low"
    },
    {
      "option": "wait_for_service",
      "description": "Wait for external API to be restored",
      "effort": "0 hours",
      "risk": "high - unknown timeline"
    }
  ],
  "recommended_action": "retry_with_fallback"
}'
```

#### Task Recovery Implementation:
```
Supervisor> Implementing task recovery plan for payment processing failure.

> apex_lmdb_write /tasks/recovery/payment-processing-recovery '{
  "recovery_plan": "implement_mock_service",
  "original_task": "implement-payment-processing",
  "recovery_tasks": [
    {
      "task_id": "mock-payment-service",
      "assigned_to": "coder",
      "description": "Create mock payment service for development",
      "priority": "high"
    },
    {
      "task_id": "payment-integration-testing",
      "assigned_to": "adversary",
      "description": "Test payment integration with mock service",
      "dependencies": ["mock-payment-service"]
    }
  ],
  "rollback_plan": "Replace mock with real service when API available"
}'
```

### 3. Communication Error Recovery

#### MCP Connection Recovery:
```bash
# Detect MCP communication failure
if ! claude mcp list | grep -q apex; then
  echo "MCP connection lost - attempting recovery"

  # 1. Restart MCP server
  claude mcp restart

  # 2. Test connection
  if claude mcp list | grep -q apex; then
    echo "MCP connection restored"
    uv run apex memory write /recovery/mcp-reconnect "$(date)" '{
      "event": "mcp_connection_restored",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "downtime": "calculated from last successful operation"
    }'
  else
    echo "MCP recovery failed - manual intervention required"
  fi
fi
```

#### Agent Communication Recovery:
```
Supervisor> Detecting communication failure between agents. Implementing recovery.

> apex_lmdb_write /errors/communication/recovery-001 '{
  "error": "agent_communication_failure",
  "affected_agents": ["coder", "adversary"],
  "symptoms": [
    "Messages not being delivered",
    "Task assignments not acknowledged",
    "Status updates missing"
  ],
  "recovery_actions": [
    "Clear message queues",
    "Reset agent communication channels",
    "Re-establish coordination protocols"
  ]
}'

# Clear stuck messages
> apex_lmdb_delete /coordination/messages/coder-to-adversary-pending
> apex_lmdb_delete /coordination/messages/adversary-to-coder-pending

# Reset communication channels
> apex_lmdb_write /coordination/reset '{
  "reset_timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "action": "communication_channel_reset",
  "affected_agents": ["coder", "adversary"]
}'
```

## Recovery Strategies

### 1. Graceful Degradation

#### Reduced Functionality Mode:
```json
{
  "degradation_strategy": {
    "agent_failures": {
      "supervisor_down": "Coder and Adversary continue with last assigned tasks",
      "coder_down": "Supervisor assigns implementation tasks to available agents",
      "adversary_down": "Reduce security review requirements, document for later review"
    },
    "system_resource_limits": {
      "memory_exhaustion": "Reduce memory-intensive operations, compress old data",
      "cpu_overload": "Increase task intervals, reduce parallel processing"
    }
  }
}
```

### 2. Checkpoint-Based Recovery

#### System State Checkpoints:
```bash
# Create recovery checkpoint
uv run apex checkpoint create "Before high-risk operation"

# Recovery from checkpoint after failure
uv run apex start --continue checkpoint-uuid

# Verify recovery success
uv run apex status
uv run apex memory show /projects/{id}/config
```

### 3. Partial Recovery

#### Selective Component Recovery:
```bash
# Recover specific agent without affecting others
uv run apex agent restart coder --preserve-state

# Recover specific task workflow
uv run apex memory write /tasks/recovery/selective '{
  "scope": "authentication_tasks_only",
  "preserve": ["dashboard_tasks", "api_tasks"],
  "recovery_method": "replay_from_checkpoint"
}'
```

## Error Prevention

### 1. Proactive Monitoring

#### Early Warning System:
```json
{
  "warning_indicators": {
    "memory_usage": {
      "warning_threshold": "70%",
      "critical_threshold": "90%",
      "action": "start_cleanup_procedures"
    },
    "task_timeout_rate": {
      "warning_threshold": "10%",
      "critical_threshold": "25%",
      "action": "investigate_performance_issues"
    },
    "communication_latency": {
      "warning_threshold": "5 seconds",
      "critical_threshold": "15 seconds",
      "action": "check_network_connectivity"
    }
  }
}
```

### 2. Input Validation

#### Validate Agent Inputs:
```
Supervisor> Implementing input validation to prevent task assignment errors.

> apex_lmdb_write /error-prevention/input-validation '{
  "validation_rules": [
    {
      "field": "task_description",
      "rules": ["not_empty", "max_length_1000", "valid_utf8"]
    },
    {
      "field": "assigned_to",
      "rules": ["valid_agent_name", "agent_available"]
    },
    {
      "field": "task_dependencies",
      "rules": ["valid_task_ids", "no_circular_dependencies"]
    }
  ],
  "on_validation_failure": "reject_task_and_notify_creator"
}'
```

### 3. Resource Management

#### Prevent Resource Exhaustion:
```bash
# Implement resource limits
export APEX_MAX_MEMORY="1GB"
export APEX_MAX_TASKS_PER_AGENT="10"
export APEX_MAX_CONCURRENT_OPERATIONS="5"

# Monitor and enforce limits
check_resource_limits() {
  memory_usage=$(ps aux | grep apex | awk '{sum+=$6} END {print sum/1024}')
  if (( $(echo "$memory_usage > 1000" | bc -l) )); then
    echo "ALERT: Memory usage exceeding limits: ${memory_usage}MB"
    # Trigger cleanup or agent restart
  fi
}
```

## Error Recovery Testing

### 1. Chaos Engineering

#### Simulate Failures:
```bash
# Simulate agent crash
kill -9 $(pgrep -f "claude.*supervisor")

# Simulate task failure
uv run apex memory write /tasks/pending/test-task '{
  "description": "Task designed to fail for testing",
  "assigned_to": "coder",
  "failure_mode": "timeout_after_30_seconds"
}'

# Simulate communication failure
iptables -A OUTPUT -p tcp --dport 8080 -j DROP  # Block MCP port

# Test recovery procedures
uv run apex agent restart supervisor
uv run apex status
```

### 2. Recovery Validation

#### Verify Recovery Success:
```bash
# Recovery validation script
validate_recovery() {
  echo "=== Recovery Validation ==="

  # Check agent status
  if uv run apex status | grep -q "Running"; then
    echo "✓ Agents recovered successfully"
  else
    echo "✗ Agent recovery failed"
  fi

  # Check task processing
  before_count=$(uv run apex memory query "/tasks/pending/*" | wc -l)
  sleep 60
  after_count=$(uv run apex memory query "/tasks/pending/*" | wc -l)

  if [ "$after_count" -lt "$before_count" ]; then
    echo "✓ Task processing resumed"
  else
    echo "✗ Task processing not working"
  fi

  # Check communication
  uv run apex memory write /test/communication "test-message"
  if uv run apex memory show /test/communication | grep -q "test-message"; then
    echo "✓ Communication working"
    uv run apex memory delete /test/communication
  else
    echo "✗ Communication issues persist"
  fi
}
```

## Error Documentation

### 1. Error Catalog

#### Common Error Patterns:
```json
{
  "error_catalog": {
    "agent_startup_failure": {
      "symptoms": ["Agent process exits immediately", "Configuration errors in logs"],
      "causes": ["Invalid configuration", "Missing dependencies", "Port conflicts"],
      "solutions": ["Validate config", "Install dependencies", "Change ports"]
    },
    "task_timeout": {
      "symptoms": ["Tasks stuck in pending", "No progress updates"],
      "causes": ["Complex task", "Agent overload", "Resource constraints"],
      "solutions": ["Break down task", "Restart agent", "Increase resources"]
    }
  }
}
```

### 2. Incident Reports

#### Post-Incident Analysis:
```json
{
  "incident_report": {
    "incident_id": "APEX-2025-001",
    "date": "2025-01-08T14:30:00Z",
    "severity": "high",
    "description": "All agents crashed due to memory exhaustion",
    "timeline": [
      "14:00 - Memory usage began climbing rapidly",
      "14:25 - First agent (Adversary) crashed",
      "14:30 - All agents down, system unresponsive"
    ],
    "root_cause": "Memory leak in task cleanup process",
    "resolution": "Restart agents, implement proper memory cleanup",
    "prevention": "Add memory monitoring, fix cleanup bug",
    "lessons_learned": "Need better resource monitoring and limits"
  }
}
```

## Related Flows
- [Agent Management Flow](agent-management-flow.md) - Managing agents during errors
- [Session Management Flow](session-management-flow.md) - Recovery using sessions
- [Logging & Debugging Flow](logging-debugging-flow.md) - Diagnosing errors
- [Status Monitoring Flow](status-monitoring-flow.md) - Error detection and monitoring
