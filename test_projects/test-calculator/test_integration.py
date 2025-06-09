#!/usr/bin/env python3
"""Test the improved APEX + Claude Code integration."""

import sys
from pathlib import Path

# Add the apex source to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from apex.core.claude_integration import setup_project_mcp
from apex.types import ProjectConfig

def main():
    """Test the integration in this project directory."""
    print("🧪 Testing APEX + Claude Code Integration")
    print("=" * 50)
    
    # Create project config
    project_config = ProjectConfig(
        project_id="test-calc-123",
        name="test-calculator",
        description="A test calculator for APEX integration",
        tech_stack=["Python"],
        project_type="CLI Tool",
        features=["add", "subtract", "multiply", "divide"]
    )
    
    # Set up MCP configuration
    project_dir = Path(__file__).parent
    print(f"📁 Project directory: {project_dir}")
    
    try:
        integration = setup_project_mcp(project_dir, project_config)
        print("✅ MCP integration setup completed!")
        
        # Check if .mcp.json was created
        mcp_config = project_dir / ".mcp.json"
        if mcp_config.exists():
            print(f"✅ MCP configuration file created: {mcp_config}")
            
            # Show the configuration
            import json
            with open(mcp_config) as f:
                config = json.load(f)
            print("\n📋 MCP Configuration:")
            print(json.dumps(config, indent=2))
        
        # Show instructions for using Claude Code
        print("\n🚀 Next Steps:")
        print("1. cd to this directory:")
        print(f"   cd {project_dir}")
        print("\n2. Start Claude Code:")
        print("   claude")
        print("\n3. Claude Code will automatically load the APEX MCP server!")
        print("\n4. Try these commands in Claude Code:")
        print("   > apex_project_status test-calc-123")
        print("   > apex_lmdb_write /projects/test-calc-123/config '{\"name\": \"test-calculator\"}'")
        print("   > apex_lmdb_read /projects/test-calc-123/config")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()