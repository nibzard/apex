#!/bin/bash
set -e

echo "🚀 Setting up APEX development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv sync --dev

# Install APEX in development mode
echo "🔧 Installing APEX in development mode..."
uv pip install -e .

# Set up pre-commit hooks
echo "🎯 Setting up pre-commit hooks..."
uv run pre-commit install

# Create APEX directories
echo "📁 Creating APEX directories..."
mkdir -p .apex/{lmdb,logs,claude,config,shared/{tasks,code,issues,status}}

# Initialize LMDB database
echo "💾 Initializing LMDB database..."
python -c "
import lmdb
import os
db_path = '.apex/lmdb/apex.db'
os.makedirs(os.path.dirname(db_path), exist_ok=True)
env = lmdb.open(db_path, map_size=1024*1024*1024)  # 1GB
with env.begin(write=True) as txn:
    txn.put(b'/system/initialized', b'true')
    txn.put(b'/system/version', b'1.0.0')
env.close()
print('✅ LMDB database initialized')
"

# Create MCP configuration
echo "🔗 Creating MCP configuration..."
cat > .apex/mcp-config.json << 'EOF'
{
  "mcpServers": {
    "lmdb": {
      "command": "python",
      "args": ["-m", "apex.mcp.lmdb_server"],
      "env": {
        "APEX_LMDB_PATH": "/workspace/.apex/lmdb/apex.db",
        "APEX_LMDB_MAP_SIZE": "1073741824"
      }
    }
  }
}
EOF

# Test Claude Code installation
echo "🧪 Testing Claude Code installation..."
if command -v claude &> /dev/null; then
    echo "✅ Claude Code is installed: $(claude --version)"
else
    echo "❌ Claude Code is not installed. Installing..."
    npm install -g @anthropic-ai/claude-code
fi

# Test MCP server
echo "🧪 Testing LMDB MCP server..."
timeout 10 python -m apex.mcp.lmdb_server &
SERVER_PID=$!
sleep 2
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ LMDB MCP server starts successfully"
    kill $SERVER_PID
else
    echo "❌ LMDB MCP server failed to start"
fi

# Create sample project configuration
echo "📝 Creating sample project configuration..."
cat > .apex/config/sample-project.json << 'EOF'
{
  "project_id": "sample-project",
  "name": "Sample APEX Project",
  "description": "A sample project for testing APEX multi-agent orchestration",
  "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
  "features": ["API", "Database", "Authentication"],
  "created_at": "2024-01-01T00:00:00Z"
}
EOF

# Set up git hooks for APEX
echo "🔧 Setting up git hooks..."
mkdir -p .git/hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "🧪 Running APEX pre-commit checks..."
uv run pre-commit run --all-files
EOF
chmod +x .git/hooks/pre-commit

# Create development aliases
echo "⚡ Setting up development aliases..."
cat >> ~/.bashrc << 'EOF'

# APEX Development Aliases
alias apex="python -m apex.cli"
alias apex-test="uv run pytest"
alias apex-lint="uv run pre-commit run --all-files"
alias apex-logs="tail -f .apex/logs/*.log"
alias apex-lmdb="python -c 'import apex.core.memory; apex.core.memory.inspect_database()'"

# APEX Environment
export APEX_DEV=1
export APEX_LMDB_PATH="/workspace/.apex/lmdb/apex.db"
export CLAUDE_CONFIG_DIR="/workspace/.apex/claude"
EOF

echo "🎉 APEX development environment setup complete!"
echo ""
echo "Quick start commands:"
echo "  apex new myproject          # Create new project"
echo "  apex start                  # Start agents"
echo "  apex tui                    # Launch TUI"
echo "  apex memory show            # Browse LMDB memory"
echo ""
echo "Development commands:"
echo "  apex-test                   # Run tests"
echo "  apex-lint                   # Run linting"
echo "  apex-logs                   # View agent logs"
echo ""
echo "🚀 Ready for APEX development!"
