# Status Monitoring Flow

## Purpose
Monitor APEX system health, agent performance, task progress, and resource usage in real-time through CLI, TUI, and memory inspection tools.

## Prerequisites
- APEX project with running or recently run agents
- Access to CLI and TUI interfaces
- LMDB database with system data

## Monitoring Overview

### Key Metrics to Monitor:
- **Agent Status** - Running/stopped/error states
- **Task Progress** - Pending/active/completed tasks
- **Resource Usage** - Memory, CPU, uptime
- **System Health** - Database status, connectivity
- **Performance** - Response times, throughput

## CLI Status Monitoring

### Basic Status Check:
```bash
uv run apex status
```

**Output Example:**
```
Agent Status:
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Agent      ┃ Status      ┃ Memory  ┃ Uptime   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ supervisor │ 🟢 Running  │ 45 MB   │ 2m 15s   │
│ coder      │ 🟢 Running  │ 52 MB   │ 2m 10s   │
│ adversary  │ 🟢 Running  │ 38 MB   │ 2m 8s    │
└────────────┴─────────────┴─────────┴──────────┘

Task Summary:
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Agent      ┃ Pending Tasks ┃ Next Task                               ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Supervisor │ 1             │ Plan authentication system architecture │
│ Coder      │ 2             │ Implement user registration endpoint... │
│ Adversary  │ 1             │ Review registration security vulnera... │
└────────────┴───────────────┴─────────────────────────────────────────┘

Resource Usage:
Total Memory: 135 MB
Active Processes: 3
```

### Continuous Monitoring:
```bash
# Monitor status every 5 seconds
watch -n 5 'uv run apex status'

# Monitor with timestamp
while true; do
  echo "=== $(date) ==="
  uv run apex status
  sleep 10
done
```

## TUI Real-Time Monitoring

### Launch Interactive Dashboard:
```bash
uv run apex tui
```

### Dashboard Features:
- **Real-time agent status updates**
- **Live memory usage graphs**
- **Task progress tracking**
- **System health indicators**
- **Activity log streaming**

### TUI Navigation for Monitoring:
- `F1` - Help and key bindings
- `F2` - Detailed agent monitoring
- `F3` - Memory browser and analysis
- `R` - Manual refresh all widgets
- `Q` - Quit monitoring

## Memory-Based Monitoring

### Agent Health Checks:
```bash
# Check individual agent status
uv run apex memory show /agents/supervisor/status
uv run apex memory show /agents/coder/status
uv run apex memory show /agents/adversary/status
```

### System Health Overview:
```bash
# Project status
uv run apex memory show /projects/{project_id}/config

# Overall system health
uv run apex memory query "/system/health/*"

# Database statistics
uv run apex memory query "/stats/*"
```

### Task Progress Monitoring:
```bash
# Active tasks across all agents
uv run apex memory query "/tasks/pending/*" --limit 20

# Completed tasks today
uv run apex memory query "/tasks/completed/*" | head -10

# Failed tasks requiring attention
uv run apex memory query "/tasks/failed/*"
```

## Performance Monitoring

### Response Time Monitoring:
```bash
# Time CLI operations
time uv run apex status
time uv run apex memory show /projects/{id}/config

# Monitor agent response times
uv run apex agent logs supervisor --grep "response_time"
```

### Resource Usage Tracking:
```bash
# Monitor APEX processes
ps aux | grep -E "(apex|claude)"

# Memory usage over time
while true; do
  echo "$(date): $(ps aux | grep apex | awk '{sum+=$6} END {print sum "KB"}')"
  sleep 30
done

# Database size monitoring
watch -n 60 'du -sh apex.db && echo "Keys: $(uv run apex memory query "*" | wc -l)"'
```

### Throughput Metrics:
```bash
# Tasks completed per hour
uv run apex memory query "/tasks/completed/*" | \
  grep "$(date +%Y-%m-%d)" | wc -l

# Agent activity frequency
uv run apex memory watch "/agents/*/activity" --timeout 300 | \
  grep -c "MODIFIED"
```

## Health Check Workflows

### Daily Health Check:
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== APEX Daily Health Check $(date) ==="

# System status
echo "1. System Status:"
uv run apex status || echo "ERROR: Status check failed"

# Agent health
echo "2. Agent Health:"
for agent in supervisor coder adversary; do
  status=$(uv run apex memory show /agents/$agent/status 2>/dev/null || echo "ERROR")
  echo "  $agent: $status"
done

# Task summary
echo "3. Task Summary:"
pending=$(uv run apex memory query "/tasks/pending/*" | wc -l)
completed=$(uv run apex memory query "/tasks/completed/*" | wc -l)
echo "  Pending: $pending, Completed: $completed"

# Resource usage
echo "4. Resource Usage:"
memory=$(ps aux | grep -E "(apex|claude)" | awk '{sum+=$6} END {print sum/1024 "MB"}')
echo "  Memory: $memory"

# Database health
echo "5. Database Health:"
db_size=$(du -sh apex.db 2>/dev/null || echo "No database")
key_count=$(uv run apex memory query "*" 2>/dev/null | wc -l)
echo "  Size: $db_size, Keys: $key_count"
```

### Alert Conditions:
```bash
# Check for critical conditions
check_alerts() {
  # High memory usage (>500MB)
  memory_mb=$(ps aux | grep -E "(apex|claude)" | awk '{sum+=$6} END {print sum/1024}')
  if (( $(echo "$memory_mb > 500" | bc -l) )); then
    echo "ALERT: High memory usage: ${memory_mb}MB"
  fi

  # No agents running
  agent_count=$(uv run apex status 2>/dev/null | grep "Running" | wc -l)
  if [ "$agent_count" -eq 0 ]; then
    echo "ALERT: No agents running"
  fi

  # Many failed tasks
  failed_count=$(uv run apex memory query "/tasks/failed/*" 2>/dev/null | wc -l)
  if [ "$failed_count" -gt 5 ]; then
    echo "ALERT: $failed_count failed tasks"
  fi
}
```

## Advanced Monitoring

### Custom Metrics Collection:
```bash
# Store custom metrics in memory
store_metric() {
  local metric_name="$1"
  local value="$2"
  local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  uv run apex memory write "/metrics/$metric_name" "{
    \"value\": $value,
    \"timestamp\": \"$timestamp\",
    \"collected_by\": \"monitoring_script\"
  }"
}

# Collect and store metrics
store_metric "memory_usage_mb" "$(ps aux | grep apex | awk '{sum+=$6} END {print sum/1024}')"
store_metric "active_agents" "$(uv run apex status | grep Running | wc -l)"
store_metric "pending_tasks" "$(uv run apex memory query '/tasks/pending/*' | wc -l)"
```

### Historical Analysis:
```bash
# Analyze trends over time
analyze_trends() {
  echo "=== Trend Analysis ==="

  # Memory usage trend
  echo "Memory Usage (Last 24h):"
  uv run apex memory query "/metrics/memory_usage_mb" | \
    tail -24 | grep -o '"timestamp":"[^"]*","value":[0-9]*' | \
    sed 's/"timestamp":"\([^"]*\)","value":\([0-9]*\)/\1 \2MB/'

  # Task completion rate
  echo "Task Completion (Last 24h):"
  uv run apex memory query "/tasks/completed/*" | \
    grep "$(date +%Y-%m-%d)" | wc -l
}
```

### Performance Benchmarking:
```bash
# Benchmark APEX operations
benchmark_operations() {
  echo "=== Performance Benchmark ==="

  # Status check speed
  echo -n "Status check: "
  time (uv run apex status > /dev/null 2>&1)

  # Memory read speed
  echo -n "Memory read: "
  time (uv run apex memory show /projects/test > /dev/null 2>&1)

  # Memory write speed
  echo -n "Memory write: "
  time (uv run apex memory write /test/benchmark "test" > /dev/null 2>&1)

  # Cleanup
  uv run apex memory delete /test/benchmark > /dev/null 2>&1
}
```

## Monitoring Integration

### Prometheus Metrics (Example):
```bash
# Export metrics for Prometheus
export_prometheus_metrics() {
  cat << EOF > apex_metrics.prom
# HELP apex_agents_running Number of running APEX agents
# TYPE apex_agents_running gauge
apex_agents_running $(uv run apex status | grep -c "Running")

# HELP apex_memory_usage_bytes APEX memory usage in bytes
# TYPE apex_memory_usage_bytes gauge
apex_memory_usage_bytes $(ps aux | grep apex | awk '{sum+=$6*1024} END {print sum}')

# HELP apex_tasks_pending Number of pending tasks
# TYPE apex_tasks_pending gauge
apex_tasks_pending $(uv run apex memory query "/tasks/pending/*" | wc -l)

# HELP apex_tasks_completed_total Total completed tasks
# TYPE apex_tasks_completed_total counter
apex_tasks_completed_total $(uv run apex memory query "/tasks/completed/*" | wc -l)
EOF
}
```

### Log Aggregation:
```bash
# Aggregate logs from all agents
aggregate_logs() {
  local output_file="apex_aggregated_$(date +%Y%m%d_%H%M%S).log"

  echo "=== APEX Aggregated Logs $(date) ===" > "$output_file"

  for agent in supervisor coder adversary; do
    echo "--- $agent Agent Logs ---" >> "$output_file"
    uv run apex agent logs "$agent" -n 100 >> "$output_file" 2>/dev/null || echo "No logs for $agent"
    echo "" >> "$output_file"
  done

  echo "Logs aggregated to: $output_file"
}
```

## Monitoring Automation

### Automated Monitoring Script:
```bash
#!/bin/bash
# apex_monitor.sh - Continuous monitoring script

MONITOR_INTERVAL=30
LOG_FILE="apex_monitor.log"

monitor_loop() {
  while true; do
    timestamp=$(date)

    # Collect metrics
    status_output=$(uv run apex status 2>&1)
    agents_running=$(echo "$status_output" | grep -c "Running" || echo "0")
    memory_usage=$(ps aux | grep apex | awk '{sum+=$6} END {print sum/1024}' || echo "0")

    # Log metrics
    echo "[$timestamp] Agents: $agents_running, Memory: ${memory_usage}MB" >> "$LOG_FILE"

    # Check alerts
    if [ "$agents_running" -eq 0 ]; then
      echo "[$timestamp] ALERT: No agents running!" >> "$LOG_FILE"
    fi

    sleep $MONITOR_INTERVAL
  done
}

# Start monitoring
echo "Starting APEX monitoring (interval: ${MONITOR_INTERVAL}s)"
monitor_loop
```

## Troubleshooting Monitoring

### Common Issues:

**"Status command hangs"**
```bash
# Check if LMDB is accessible
uv run apex memory show /projects 2>&1 | head -5

# Check for locked processes
ps aux | grep -E "(apex|claude)" | grep -v grep
```

**"Memory queries slow"**
```bash
# Check database size
du -sh apex.db

# Monitor query performance
time uv run apex memory query "*" | head -10

# Check for memory fragmentation
uv run apex memory query "*" | wc -l
```

**"TUI not updating"**
```bash
# Check TUI refresh settings
# Restart TUI with debug mode
APEX_DEBUG=1 uv run apex tui
```

## Related Flows
- [Agent Management Flow](agent-management-flow.md) - Managing monitored agents
- [TUI Navigation Flow](tui-navigation-flow.md) - Interactive monitoring interface
- [Memory Management Flow](memory-management-flow.md) - Memory-based monitoring
- [Logging & Debugging Flow](logging-debugging-flow.md) - Detailed troubleshooting
