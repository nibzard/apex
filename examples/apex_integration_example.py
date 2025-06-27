#!/usr/bin/env python3
"""Example of integrating the new plugin-based LMDB system with APEX."""

import asyncio
import tempfile
from pathlib import Path

from apex.core.lmdb_mcp import APEXDatabase
from apex.core.memory_compat import MemoryPatterns
from apex.types import AgentType


async def apex_integration_example():
    """Demonstrate APEX integration with plugin-based database."""
    print("🚀 APEX Plugin Integration Example")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "apex_workspace"
        project_id = "example_project"

        # Create APEX database
        async with APEXDatabase(
            workspace_path=workspace,
            project_id=project_id,
            map_size=50_000_000,  # 50MB
        ) as apex_db:
            print(f"✅ Created APEX database for project: {project_id}")

            # Create compatibility layer for existing code
            memory_patterns = MemoryPatterns(apex_db)
            print("✅ Created memory patterns compatibility layer")

            # Demonstrate APEX-specific workflows
            print("\n📋 Creating APEX tasks...")

            # Create tasks using the new API
            task1_id = await apex_db.create_task(
                {
                    "description": "Implement user authentication system",
                    "priority": "high",
                    "metadata": {
                        "complexity": "high",
                        "estimated_hours": 8,
                        "skills_required": ["python", "security", "jwt"],
                    },
                },
                assigned_to="coder",
            )
            print(f"   📝 Created task 1: {task1_id}")

            task2_id = await apex_db.create_task(
                {
                    "description": "Write comprehensive tests for auth system",
                    "priority": "medium",
                    "depends_on": [task1_id],
                    "metadata": {
                        "complexity": "medium",
                        "estimated_hours": 4,
                        "skills_required": ["python", "testing", "pytest"],
                    },
                },
                assigned_to="coder",
            )
            print(f"   📝 Created task 2: {task2_id}")

            # Create a task for the adversary
            task3_id = await apex_db.create_task(
                {
                    "description": "Security review of authentication implementation",
                    "priority": "high",
                    "depends_on": [task1_id],
                    "metadata": {
                        "complexity": "medium",
                        "estimated_hours": 3,
                        "skills_required": ["security", "code_review"],
                    },
                },
                assigned_to="adversary",
            )
            print(f"   🔍 Created adversary task: {task3_id}")

            # Store some code using APEX database
            print("\n💻 Storing code files...")

            auth_code = """
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

class AuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)
"""

            code_id = await apex_db.store_code(
                file_path="src/auth/manager.py",
                content=auth_code,
                task_id=task1_id,
                metadata={
                    "language": "python",
                    "lines": auth_code.count("\n"),
                    "complexity": "medium",
                },
            )
            print(f"   📄 Stored auth manager code: {code_id}")

            # Update agent statuses
            print("\n🤖 Updating agent statuses...")

            await apex_db.update_agent_status(
                "coder",
                {
                    "status": "working",
                    "current_task": task1_id,
                    "progress": "implementing_auth_core",
                    "metadata": {
                        "files_modified": ["src/auth/manager.py"],
                        "next_steps": [
                            "implement_jwt_tokens",
                            "add_password_validation",
                        ],
                    },
                },
            )
            print("   ✅ Updated coder status")

            await apex_db.update_agent_status(
                "adversary",
                {
                    "status": "waiting",
                    "current_task": task3_id,
                    "progress": "pending_coder_completion",
                    "metadata": {
                        "review_focus": ["security_vulnerabilities", "auth_bypass"],
                    },
                },
            )
            print("   ✅ Updated adversary status")

            await apex_db.update_agent_status(
                "supervisor",
                {
                    "status": "monitoring",
                    "current_task": None,
                    "progress": "orchestrating_agents",
                    "metadata": {
                        "active_tasks": [task1_id, task2_id, task3_id],
                        "coordination_notes": "coder working on core auth, adversary ready for review",
                    },
                },
            )
            print("   ✅ Updated supervisor status")

            # Report some issues
            print("\n🐛 Reporting issues...")

            issue1_id = await apex_db.report_issue(
                {
                    "description": "Potential timing attack in password comparison",
                    "file": "src/auth/manager.py",
                    "line": 12,
                    "type": "security",
                    "category": "vulnerability",
                    "suggested_fix": "Use constant-time comparison for password verification",
                },
                severity="high",
            )
            print(f"   🚨 Reported security issue: {issue1_id}")

            issue2_id = await apex_db.report_issue(
                {
                    "description": "Missing input validation for password length",
                    "file": "src/auth/manager.py",
                    "line": 15,
                    "type": "bug",
                    "category": "validation",
                    "suggested_fix": "Add minimum password length validation",
                },
                severity="medium",
            )
            print(f"   ⚠️  Reported validation issue: {issue2_id}")

            # Create a session
            print("\n📊 Creating APEX session...")

            session_id = await apex_db.create_session(
                {
                    "session_type": "coding_session",
                    "goal": "Implement secure user authentication",
                    "participants": ["coder", "adversary", "supervisor"],
                    "metadata": {
                        "started_by": "user",
                        "priority": "high",
                        "deadline": "2024-02-01",
                    },
                }
            )
            print(f"   📋 Created session: {session_id}")

            # Query data using APEX methods
            print("\n🔍 Querying APEX data...")

            # Get pending tasks
            pending_tasks = await apex_db.get_pending_tasks()
            print(f"   📝 Found {len(pending_tasks)} pending tasks:")
            for task in pending_tasks:
                print(
                    f"      - {task['description']} (assigned to {task['assigned_to']})"
                )

            # Get open issues
            open_issues = await apex_db.get_open_issues()
            print(f"   🐛 Found {len(open_issues)} open issues:")
            for issue in open_issues:
                print(f"      - {issue['description']} ({issue['severity']})")

            # Get agent statuses
            agent_statuses = await apex_db.get_all_agent_status()
            print("   🤖 Agent statuses:")
            for agent_type, status in agent_statuses.items():
                print(
                    f"      - {agent_type}: {status['status']} (task: {status.get('current_task', 'none')})"
                )

            # Show compatibility with existing APEX code
            print("\n🔄 Testing compatibility layer...")

            # Test using MemoryPatterns compatibility layer
            compat_task_id = await memory_patterns.create_task(
                project_id,
                {
                    "description": "Compatibility test task",
                    "priority": "low",
                },
                assigned_to="coder",
            )
            print(f"   ✅ Created task via compatibility layer: {compat_task_id}")

            # Test agent status via compatibility
            await memory_patterns.update_agent_status(
                project_id,
                AgentType.CODER,
                {
                    "status": "testing_compatibility",
                    "metadata": {"test": "successful"},
                },
            )
            print("   ✅ Updated agent status via compatibility layer")

            # Get stats
            print("\n📊 APEX Database Statistics:")
            stats = await apex_db.get_memory_stats()
            print(f"   Project ID: {stats['project_id']}")
            print(f"   Agent Type: {stats['agent_type']}")
            print(f"   Loaded Plugins: {stats['plugins']}")
            print(f"   Total Keys: {stats['stats']['total_keys']}")

            apex_stats = stats.get("apex_stats", {})
            print(f"   Total Tasks: {apex_stats.get('total_tasks', 0)}")
            print(f"   Pending Tasks: {apex_stats.get('pending_tasks', 0)}")
            print(f"   Total Issues: {apex_stats.get('total_issues', 0)}")
            print(f"   Open Issues: {apex_stats.get('open_issues', 0)}")


async def orchestrator_integration_example():
    """Show how to integrate with the ProcessOrchestrator pattern."""
    print("\n🎛️  Orchestrator Integration Example")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "orchestrator_workspace"
        project_id = "orchestrator_test"

        # Create APEX database
        async with APEXDatabase(
            workspace_path=workspace, project_id=project_id
        ) as apex_db:
            print(f"✅ Created orchestrator database for project: {project_id}")

            # Create memory patterns for orchestrator compatibility
            memory_patterns = MemoryPatterns(apex_db)

            # Simulate orchestrator operations
            print("\n🚀 Simulating orchestrator operations...")

            # Create a task briefing (like ProcessOrchestrator would)
            briefing_data = {
                "task_id": "briefing_001",
                "role": "coder",
                "description": "Implement feature X with tests",
                "context": {
                    "project_files": ["src/main.py", "tests/test_main.py"],
                    "requirements": ["implement", "test", "document"],
                },
                "constraints": {
                    "max_duration": "30m",
                    "tools_allowed": ["bash", "read", "write", "edit"],
                },
            }

            # Store briefing (like orchestrator does)
            briefing_key = f"/projects/{project_id}/briefings/briefing_001"

            # Use the plugin system to store briefing data
            memory_plugin = apex_db.get_plugin("memory_patterns")
            if memory_plugin:
                await memory_plugin.insert_record(
                    namespace=f"projects/{project_id}",
                    collection="briefings",
                    data=briefing_data,
                    id="briefing_001",
                )
                print("   📄 Stored task briefing")

            # Store process metrics (like orchestrator does)
            metrics_data = {
                "processes_started": 1,
                "processes_completed": 0,
                "processes_failed": 0,
                "last_updated": "2024-01-15T10:30:00Z",
            }

            if memory_plugin:
                await memory_plugin.insert_record(
                    namespace="supervisor",
                    collection="metrics",
                    data=metrics_data,
                    id="process_metrics",
                )
                print("   📊 Stored process metrics")

            # Simulate process history cleanup
            print("   🧹 Process cleanup simulation completed")

            print("✅ Orchestrator integration example completed")


async def main():
    """Run all integration examples."""
    await apex_integration_example()
    await orchestrator_integration_example()

    print("\n🎉 APEX Integration Examples Complete!")
    print("\n📚 Summary:")
    print("- ✅ APEXDatabase provides high-level APEX operations")
    print("- ✅ MemoryPatterns compatibility layer maintains existing API")
    print("- ✅ Plugin system provides structured data with schema validation")
    print("- ✅ Async support throughout for non-blocking operations")
    print("- ✅ APEX-specific collections (tasks, agents, issues, code, sessions)")
    print("- ✅ ProcessOrchestrator can be easily migrated to use new system")
    print("\n🚀 Ready for production integration!")


if __name__ == "__main__":
    asyncio.run(main())
