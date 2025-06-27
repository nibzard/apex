#!/usr/bin/env python3
"""Test APEX integration using local lmdb-mcp source."""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add lmdb-mcp source to path
sys.path.insert(0, str(Path(__file__).parent / "lmdb-mcp" / "src"))

from lmdb_mcp import AgentDatabase

from apex.core.lmdb_mcp import APEXDatabase


async def test_apex_integration():
    """Test APEX integration with local lmdb-mcp."""
    print("🧪 Testing APEX Integration with Local LMDB-MCP")
    print("=" * 55)

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "test_workspace"
        project_id = "test_project"

        try:
            # Test basic AgentDatabase first
            print("1️⃣ Testing basic AgentDatabase...")
            async with AgentDatabase(
                workspace_path=workspace / "agent_db",
                agent_type="coding",
                estimated_size=10_000_000,  # 10MB
            ) as agent_db:
                print("   ✅ AgentDatabase created successfully")

                # Test basic operations
                await agent_db.create_namespace("test")
                print("   ✅ Namespace created")

                record_id = await agent_db.store_structured_data(
                    "test", "items", {"name": "test_item", "value": 42}
                )
                print(f"   ✅ Stored record: {record_id}")

                retrieved = await agent_db.get_structured_data(
                    "test", "items", record_id
                )
                print(f"   ✅ Retrieved record: {retrieved['name']}")

            print("\n2️⃣ Testing APEXDatabase...")

            # Now test APEXDatabase
            async with APEXDatabase(
                workspace_path=workspace / "apex_db",
                project_id=project_id,
                map_size=20_000_000,  # 20MB
            ) as apex_db:
                print("   ✅ APEXDatabase created successfully")

                # Test APEX-specific operations
                task_id = await apex_db.create_task(
                    {
                        "description": "Test task creation",
                        "priority": "medium",
                    }
                )
                print(f"   ✅ Created task: {task_id}")

                agent_id = await apex_db.update_agent_status(
                    "coder",
                    {
                        "status": "working",
                        "current_task": task_id,
                    },
                )
                print(f"   ✅ Updated agent status: {agent_id}")

                issue_id = await apex_db.report_issue(
                    {
                        "description": "Test issue reporting",
                        "type": "bug",
                    }
                )
                print(f"   ✅ Reported issue: {issue_id}")

                # Test queries
                pending_tasks = await apex_db.get_pending_tasks()
                print(f"   ✅ Found {len(pending_tasks)} pending tasks")

                open_issues = await apex_db.get_open_issues()
                print(f"   ✅ Found {len(open_issues)} open issues")

                agent_statuses = await apex_db.get_all_agent_status()
                print(f"   ✅ Found {len(agent_statuses)} agent statuses")

                # Test stats
                stats = await apex_db.get_memory_stats()
                print(
                    f"   ✅ Memory stats: {stats['apex_stats']['total_tasks']} tasks, {stats['apex_stats']['total_issues']} issues"
                )

            print("\n✅ All tests passed! APEX integration is working.")
            return True

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(test_apex_integration())
    if success:
        print("\n🎉 APEX plugin integration is ready for production!")
    else:
        print("\n💥 Integration needs fixes before deployment.")
        sys.exit(1)
