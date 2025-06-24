# APEX Zero-to-Hero Tutorial
*From Installation to Your First Multi-Agent Development Session in 10 Minutes*

## What You'll Build
By the end of this tutorial, you'll have created a simple calculator app where three AI agents work together:
- **Supervisor** plans the work and coordinates
- **Coder** implements the features
- **Adversary** finds bugs and improves quality

You'll see them collaborate, challenge each other, and deliver working code with tests.

## Choose Your Adventure

### 🐳 **Option A: DevContainer Setup (Recommended)**
*Complete isolated environment with VS Code integration*

### 💻 **Option B: Local Installation**
*Direct installation on your machine*

---

## Option A: DevContainer Setup (5 minutes)

### Prerequisites
- Docker Desktop installed and running
- VS Code with Dev Containers extension
- Git for cloning

### Step 1: Get APEX and Open in Container (2 minutes)

```bash
# Clone APEX repository
git clone https://github.com/your-org/apex.git
cd apex

# Open in VS Code
code .
```

**VS Code will prompt: "Reopen in Container"** - Click **"Reopen in Container"**

**What happens next:**
- Docker builds the development environment (first time: ~3-5 minutes)
- VS Code opens inside the container with APEX pre-installed
- All dependencies, Claude Code, and tools are ready

### Step 2: Create Your First Project (1 minute)

Inside the VS Code terminal (now running in container):

```bash
# Create a calculator project
apex new my-calculator

# Follow the prompts:
# Project description: "A simple calculator with error handling"
# Technology stack: Python
# Project type: CLI Tool
# Key features: arithmetic, testing, error-handling

cd my-calculator
```

### Step 3: Start the Multi-Agent System (1 minute)

```bash
# Start the LMDB server and all agents
docker-compose up -d lmdb-server supervisor-agent coder-agent adversary-agent

# Give them a task
apex start --task "Create a calculator that handles basic arithmetic with proper error handling"
```

**Container Magic:** ✨
- Each agent runs in its own isolated container
- Shared LMDB database coordinates their work
- VS Code connects to monitor everything

### Step 4: Monitor the Agents (1 minute)

Open new VS Code terminals and watch the agents work:

```bash
# Watch agent logs in real-time
docker-compose logs -f supervisor-agent
docker-compose logs -f coder-agent
docker-compose logs -f adversary-agent

# Or use APEX monitoring
apex status
apex tui
```

**Pro tip:** Use VS Code's split terminal feature to watch all three agents simultaneously!

---

## Option B: Local Installation (3 minutes)

### Prerequisites
- Python 3.11+ installed
- Claude CLI installed ([claude.ai/code](https://claude.ai/code))
- Basic terminal familiarity

### Step 1: Install APEX (1 minute)

```bash
# Install APEX
pip install git+https://github.com/your-org/apex.git

# Verify installation
apex --version
```

### Step 2: Create Your First Project (1 minute)

```bash
# Create a calculator project
apex new my-calculator

# Follow the prompts:
# Project description: "A simple calculator with error handling"
# Technology stack: Python
# Project type: CLI Tool
# Key features: arithmetic, testing, error-handling

cd my-calculator
```

### Step 3: Start Your AI Development Team (1 minute)

```bash
# Start all three agents with your first task
apex start --task "Create a calculator that handles basic arithmetic with proper error handling"
```

---

## Watch the Magic Happen (2 minutes)
*Same for both options*

### Monitor Agent Status

```bash
cd my-calculator
apex status
```

**You'll see something like:**
```
Agent Status:
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Agent      ┃ Status      ┃ Current Task                    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ supervisor │ 🟢 Planning  │ Breaking down calculator requirements │
│ coder      │ 🟢 Ready     │ Waiting for task assignment          │
│ adversary  │ 🟢 Ready     │ Ready to review implementations      │
└────────────┴─────────────┴─────────────────────────────────────┘

Recent Activity:
• Supervisor created task: "Design calculator structure"
• Supervisor assigned task to Coder
• Coder started implementation
```

### Watch Real-Time Collaboration

**DevContainer users:**
```bash
# In VS Code terminal tabs
docker-compose logs -f supervisor-agent
docker-compose logs -f coder-agent
docker-compose logs -f adversary-agent
```

**Local installation users:**
```bash
# In separate terminal windows
apex agent logs supervisor --follow
apex agent logs coder --follow
apex agent logs adversary --follow
```

## Interactive Monitoring (1 minute)

Launch the interactive dashboard:

```bash
apex tui
```

**Navigate the interface:**
- `F2` - See detailed agent status
- `F3` - Browse the shared memory where agents coordinate
- `F4` - View task progress
- `Q` - Quit back to terminal

**DevContainer bonus:** VS Code port forwarding automatically makes the TUI accessible at `localhost:8001`

## See the Results (2 minutes)

Check what the agents built:

```bash
# See what files were created
ls -la

# Look at the implementation
cat src/calculator.py

# Check the tests
cat tests/test_calculator.py

# Run the calculator
python src/calculator.py
```

Run the tests to see the Adversary's quality work:
```bash
python -m pytest tests/ -v
```

## DevContainer Advantages in Action

### Container Isolation Benefits

**View agent containers:**
```bash
# See all running containers
docker-compose ps

# Check resource usage
docker stats
```

**Independent agent processes:**
- Each agent runs in isolation
- Automatic restart if an agent crashes
- Clear resource allocation per agent
- Network isolation and security

### VS Code Integration Features

**Built-in tools:**
- Python debugging with breakpoints
- Integrated terminal for each container
- Git integration with container-aware operations
- Extensions pre-installed and configured

**Access individual agents:**
```bash
# Connect to specific agent containers
docker-compose exec supervisor-agent bash
docker-compose exec coder-agent bash
docker-compose exec adversary-agent bash
```

## Advanced DevContainer Features (1 minute)

### Multi-Container Development

```bash
# Scale agents for heavy workloads
docker-compose up --scale coder-agent=2

# Monitor LMDB server
docker-compose logs -f lmdb-server

# Access shared volumes
ls -la .apex/lmdb/  # Shared database
ls -la .apex/logs/  # Agent logs
```

### Development Workflow

```bash
# Make code changes in VS Code (auto-synced to containers)
# Restart specific agent to pick up changes
docker-compose restart coder-agent

# Full environment reset
docker-compose down
docker-compose up -d
```

## See the Adversarial Process

Look for the back-and-forth between agents:

```bash
# DevContainer: Check agent coordination
docker-compose logs supervisor-agent | grep -i "task"
docker-compose logs adversary-agent | grep -i "issue\|security"

# Local: Same investigation
apex memory query "*security*" --content
apex memory query "*issue*" --content

# Check the git history to see their collaboration
git log --oneline
```

## Try Advanced Features

### Persistent Development Sessions

**DevContainer advantage:** Your development environment persists across restarts

```bash
# Stop containers but keep data
docker-compose stop

# Resume later - all data preserved
docker-compose start
```

### Add a New Feature

```bash
# Give the team a new challenge
apex start --task "Add support for scientific operations like square root and power"

# Watch the containers handle the new work
docker-compose logs -f --tail=20 coder-agent
```

### Use Claude Code Integration

**DevContainer setup:**
```bash
# Claude Code is pre-configured with MCP tools
claude

# In Claude Code, try:
# > Can you show me the current project status using APEX tools?
# > What tasks are currently pending?
# > Show me the calculator implementation
```

**Local setup:**
```bash
# Start Claude Code with APEX tools loaded
claude

# Same commands work with local MCP setup
```

## What Just Happened? The APEX Advantage

### 🐳 **Container Orchestration** (DevContainer users)
- Isolated agent execution environments
- Automatic service discovery and networking
- Persistent data volumes
- Professional deployment patterns

### 🤖 **True Multi-Agent Development**
- Three specialized AI agents with distinct roles
- Automatic task breakdown and assignment
- Collaborative problem-solving

### 🔄 **Adversarial Quality Improvement**
- The Adversary actively found issues the Coder missed
- Iterative improvement through systematic challenge
- Higher code quality through constructive conflict

### 🧠 **Persistent Memory**
- Agents share knowledge through LMDB database
- Context preserved across sessions
- Coordination without complex message passing

## DevContainer vs Local: Which Should You Choose?

### Choose **DevContainer** if you want:
- ✅ Isolated, reproducible environment
- ✅ Professional development setup
- ✅ Easy team collaboration
- ✅ VS Code integration
- ✅ Container orchestration experience
- ✅ No local environment pollution

### Choose **Local Installation** if you prefer:
- ✅ Direct system integration
- ✅ Faster startup times
- ✅ Simpler debugging
- ✅ No Docker dependency
- ✅ Custom system configuration

## Next Steps: Level Up Your APEX Skills

### Immediate Next Steps (5 minutes each):

**DevContainer Users:**
1. **Container Management**: `docker-compose scale coder-agent=2`
2. **Volume Inspection**: Explore persistent data in `.apex/`
3. **Multi-Container Debugging**: Debug across agent containers
4. **Resource Monitoring**: Use `docker stats` to monitor agents

**All Users:**
1. **Try Different Project Types**: `apex new web-app --template api-service`
2. **Explore Templates**: `apex templates list`
3. **Monitor Performance**: `apex memory watch "*"`
4. **Experiment with Claude Code**: Direct agent interaction

### Intermediate Challenges (15-30 minutes each):
1. **Custom Agent Behaviors**: Modify agent configurations
2. **Complex Workflows**: Multi-feature development
3. **Team Collaboration**: Share APEX sessions
4. **CI/CD Integration**: Automate APEX in pipelines

### Advanced Mastery (1+ hours):
1. **Container Customization**: Modify Dockerfiles for your needs
2. **Create Custom Templates**: For your specific tech stack
3. **Extend APEX**: Add custom MCP tools
4. **Production Deployment**: Scale APEX with Kubernetes

## Troubleshooting Your First Session

**DevContainer Issues:**
```bash
# Container won't start
docker-compose logs lmdb-server
docker-compose build --no-cache

# VS Code connection issues
# Restart VS Code and reopen in container

# Agent containers failing
docker-compose restart supervisor-agent
docker system prune  # Clean up if needed
```

**Local Installation Issues:**
```bash
# Agents aren't starting
claude --version  # Check Claude CLI
apex config validate  # Verify APEX configuration

# No tasks appearing
apex stop && apex start --task "Create a simple hello world program"
```

**Universal Fixes:**
```bash
# TUI not working
watch -n 5 'apex status'  # Use CLI monitoring instead

# LMDB issues
rm -rf .apex/lmdb && apex init  # Reset database
```

## What Makes APEX Different?

Unlike single-agent coding assistants, APEX gives you:

- **Systematic Quality**: Adversary agent finds issues humans miss
- **Professional Infrastructure**: Container orchestration and isolation
- **Continuous Coordination**: Agents work together, not just respond to prompts
- **Persistent Context**: Knowledge preserved across sessions
- **Production Workflows**: Git integration, testing, documentation
- **Scalable Architecture**: Handles complex, multi-component projects

---

**Congratulations!** 🎉 You've just experienced the future of AI-assisted development. You went from zero to having three AI agents collaboratively building, testing, and improving code for you.

**DevContainer users:** You now have a complete professional development environment that you can share with your team, version control, and deploy anywhere Docker runs.

**Local users:** You have APEX running directly on your system with full integration into your existing workflow.

Welcome to APEX development!

### Quick Reference

**DevContainer Commands:**
```bash
docker-compose up -d          # Start all services
docker-compose logs -f        # View all logs
docker-compose restart        # Restart services
docker-compose down           # Stop everything
apex tui                      # Monitor via TUI
```

**Local Commands:**
```bash
apex start                    # Start agents
apex status                   # Check status
apex tui                      # Launch TUI
apex stop                     # Stop agents
```

Ready to build something amazing? 🚀
