#!/usr/bin/env python3
"""Development environment setup script."""

import os
import sys
from pathlib import Path

def setup_development():
    """Setup development environment."""
    print("🚀 Setting up APEX development environment...")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    
    print(f"📁 Project root: {project_root}")
    print(f"📦 Source path: {src_path}")
    
    # Add src to Python path
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print("✅ Added src to Python path")
    
    # Test imports
    try:
        import apex
        print(f"✅ Successfully imported apex v{apex.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import apex: {e}")
        return False
    
    # Create .env file if it doesn't exist
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✅ Created .env file from template")
    
    # Create test database directory
    test_db_dir = project_root / "test_data"
    test_db_dir.mkdir(exist_ok=True)
    print("✅ Created test database directory")
    
    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure API keys")
    print("2. Run tests with: PYTHONPATH=./src uv run pytest")
    print("3. Start development with: PYTHONPATH=./src uv run apex --help")
    
    return True

if __name__ == "__main__":
    setup_development()