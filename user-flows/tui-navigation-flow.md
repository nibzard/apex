# TUI Navigation Flow

## Purpose
Navigate and use the APEX Terminal User Interface (TUI) for interactive monitoring, management, and control of agents, tasks, and system resources.

## Prerequisites
- APEX project initialized
- Terminal with adequate size (minimum 80x24 recommended)
- APEX TUI dependencies installed

## Starting the TUI

### Launch Command:
```bash
uv run apex tui
```

**Options:**
- `--layout <name>` - TUI layout (default: dashboard)
- `--theme <name>` - Color theme (default: dark)

### Startup Process:
1. APEX loads project configuration
2. Connects to LMDB database
3. Initializes TUI components
4. Displays main dashboard

## Screen Overview

### Main Interface Layout:
```
┌─ APEX Dashboard ────────────────────────────────────────────┐
│ Project: myapp | Session: abc-123 | Git: main (3 ahead)     │
├─────────────────────────────────────────────────────────────┤
│ ┌─ Agent Status ──────────┐ ┌─ Current Tasks ─────────────┐ │
│ │ Supervisor  ✓ Planning  │ │ ▶ Implement user auth       │ │
│ │ Coder       ✓ Coding    │ │   ├─ Create user model      │ │
│ │ Adversary   ✓ Testing   │ │   ├─ Add login endpoint     │ │
│ │                         │ │   └─ Setup JWT tokens       │ │
│ │ Memory: 2.1GB           │ │                             │ │
│ │ Uptime: 02:34:56        │ │ ▶ Add error handling        │ │
│ └─────────────────────────┘ └─────────────────────────────┘ │
│ [F1]Help [F2]Agents [F3]Memory [F4]Tasks [F5]Git [Q]Quit    │
└─────────────────────────────────────────────────────────────┘
```

## Screen Navigation

### Primary Screens:

#### 1. Dashboard Screen (Default)
**Access:** Launch TUI or press `Home`
**Features:**
- Agent status overview
- System metrics
- Recent activity log
- Quick action buttons

**Key Bindings:**
- `Q` - Quit application
- `A` - Go to Agents screen
- `M` - Go to Memory screen
- `R` - Refresh dashboard

#### 2. Agents Screen
**Access:** Press `F2` or `A` from dashboard
**Features:**
- Detailed agent management
- Start/stop individual agents
- Real-time log viewing
- Agent interaction panel

**Key Bindings:**
- `Q` - Back to dashboard
- `R` - Refresh agent status
- `S` - Start agent dialog
- `X` - Stop agent dialog

#### 3. Memory Screen
**Access:** Press `F3` or `M` from dashboard
**Features:**
- Browse LMDB memory structure
- Search memory contents
- View key-value data
- Real-time memory monitoring

**Key Bindings:**
- `Q` - Back to dashboard
- `R` - Refresh memory tree
- `/` - Search dialog

## Detailed Screen Workflows

### Dashboard Screen Operations

#### Quick Actions:
1. **Start All Agents**
   - Click "Start All" button
   - Or use keyboard shortcuts

2. **Stop All Agents**
   - Click "Stop All" button
   - Confirms before stopping

3. **Navigate to Screens**
   - "Agents Screen" button → Agent management
   - "Memory Browser" button → Memory exploration

#### Status Monitoring:
- **Agent Status Widget** - Shows running/stopped status
- **Metrics Widget** - System resource usage
- **Activity Log** - Recent system events

### Agents Screen Operations

#### Agent Control:
1. **Start Individual Agents**
   - "Start Supervisor" button
   - "Start Coder" button
   - "Start Adversary" button

2. **Stop All Agents**
   - "Stop All" button
   - Stops all running agents

#### Log Management:
1. **Apply Log Filters**
   - Enter agent name filter
   - Specify log level (error, warn, info, debug)
   - Add search pattern
   - Click "Apply" button

2. **View Agent Logs**
   - Left panel shows filtered logs
   - Real-time updates
   - Scrollable history

#### Agent Interaction:
- **Right panel** - Direct agent communication
- **Send messages** to specific agents
- **View responses** and status updates

### Memory Screen Operations

#### Memory Browser:
1. **Tree Navigation**
   - Expand/collapse memory sections
   - Navigate with arrow keys
   - Select items with Enter

2. **Memory Search**
   - Press `/` to open search
   - Enter search terms
   - Navigate results

3. **Data Viewing**
   - Select memory keys
   - View formatted content
   - JSON syntax highlighting

## Widget Interactions

### Agent Status Widget:
**Displays:**
- Agent names and current status
- Running/stopped indicators
- Memory usage per agent
- Uptime information

**Interactions:**
- Click to focus on specific agent
- Real-time status updates
- Color-coded status indicators

### Metrics Widget:
**Displays:**
- Total system memory usage
- CPU utilization
- Active process count
- Database size

### Log Viewer Widget:
**Features:**
- Scrollable log history
- Color-coded log levels
- Real-time streaming
- Search and filtering

**Controls:**
- Scroll up/down through logs
- Auto-scroll to latest entries
- Filter by log level or agent

### Memory Browser Widget:
**Features:**
- Hierarchical tree view
- Key-value pair display
- JSON formatting
- Search capabilities

**Navigation:**
- Arrow keys for tree navigation
- Enter to expand/view items
- Search with `/` key

## Keyboard Shortcuts

### Global Shortcuts:
- `Q` - Quit/Back
- `Ctrl+C` - Force quit
- `F1` - Help screen
- `Esc` - Cancel current action

### Dashboard Shortcuts:
- `A` - Agents screen
- `M` - Memory screen
- `R` - Refresh all
- `S` - Start all agents
- `X` - Stop all agents

### Navigation Shortcuts:
- `Tab` - Move between widgets
- `Shift+Tab` - Move backward
- `Enter` - Activate/select
- `Space` - Toggle items

### Screen-Specific Shortcuts:
**Agents Screen:**
- `S` - Start agent
- `X` - Stop agent
- `F` - Apply filters

**Memory Screen:**
- `/` - Search
- `R` - Refresh tree
- `E` - Edit value (if supported)

## Status Indicators

### Agent Status:
- 🟢 **Running** - Agent active and processing
- 🔴 **Stopped** - Agent not running
- 🟡 **Starting** - Agent initialization in progress
- 🟠 **Error** - Agent encountered error

### System Status:
- **Green** - Healthy operation
- **Yellow** - Warning conditions
- **Red** - Error states
- **Blue** - Information/neutral

### Memory Status:
- **📁 Folder** - Memory namespace
- **📄 File** - Individual memory key
- **🔍 Search** - Search results
- **⚠️ Warning** - Access issues

## Common Operations

### Monitor Agent Activity:
1. Launch TUI: `uv run apex tui`
2. Observe dashboard status
3. Press `F2` for detailed agent view
4. Use log filters to focus on specific events

### Investigate Issues:
1. Check dashboard for warnings
2. Navigate to Memory screen (`F3`)
3. Search for error patterns (`/`)
4. Review agent logs with filters

### Start Development Session:
1. Launch TUI
2. Use "Start All" quick action
3. Monitor agent startup in real-time
4. Switch to Agents screen for detailed monitoring

### Debug Memory Issues:
1. Open Memory screen
2. Browse to problem area
3. Search for specific keys
4. Monitor changes in real-time

## TUI Configuration

### Theme Options:
- **Dark** (default) - Dark background, light text
- **Light** - Light background, dark text
- **Custom** - User-defined color schemes

### Layout Options:
- **Dashboard** (default) - Overview layout
- **Compact** - Condensed information view
- **Debug** - Extended debugging information

## Error Handling

### Connection Issues:
- TUI displays connection status
- Automatic retry attempts
- Graceful fallback to read-only mode

### Display Problems:
- Minimum terminal size warnings
- Automatic layout adjustment
- Color compatibility detection

### Performance Optimization:
- Lazy loading of memory data
- Configurable refresh intervals
- Background data updates

## Related Flows
- [Agent Management Flow](agent-management-flow.md) - Managing agents via TUI
- [Status Monitoring Flow](status-monitoring-flow.md) - Using TUI for monitoring
- [Memory Management Flow](memory-management-flow.md) - Memory browser usage
- [CLI Operations Flow](cli-operations-flow.md) - Command-line alternative to TUI
