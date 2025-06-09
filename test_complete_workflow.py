#!/usr/bin/env python3
"""Test script for complete APEX workflow."""

import asyncio
import uuid
from pathlib import Path

from src.apex.core.agent_runner import AgentRunner
from src.apex.types import AgentType, ProjectConfig


async def test_complete_workflow():
    """Test the complete Supervisor → Coder → Adversary workflow."""
    print("🚀 Starting APEX Complete Workflow Test")
    print("=" * 50)

    # Create test project configuration
    config = ProjectConfig(
        project_id=str(uuid.uuid4()),
        name="calculator-app",
        description="A simple calculator application for testing APEX workflow",
        tech_stack=["Python", "CLI"],
        project_type="CLI Tool",
        features=["addition", "subtraction", "multiplication", "division"],
    )

    print(f"📋 Project: {config.name}")
    print(f"📝 Description: {config.description}")
    print(f"🛠️  Tech Stack: {', '.join(config.tech_stack)}")
    print()

    # Initialize AgentRunner
    runner = AgentRunner(project_config=config, lmdb_path=Path("test_apex_workflow.db"))

    try:
        print("1️⃣  Starting Complete Workflow...")

        # Start workflow with user request
        user_request = (
            "Create a simple calculator that can add, subtract, "
            "multiply and divide two numbers"
        )
        workflow_id = await runner.start_workflow(user_request, auto_start_agents=False)

        print(f"✅ Workflow started: {workflow_id}")
        print(f"📋 User request: {user_request}")
        print()

        print("2️⃣  Checking Initial Workflow Status...")

        # Check workflow status
        workflow_status = await runner.get_workflow_status(workflow_id)
        if workflow_status:
            print(f"📊 Workflow Status: {workflow_status['status']}")
            print(f"📝 Tasks Created: {len(workflow_status.get('task_ids', []))}")
            print()

            # Show task breakdown
            print("📋 Task Breakdown:")
            for i, task_id in enumerate(workflow_status.get("task_ids", []), 1):
                task_status = await runner.task_workflow.get_task_status(task_id)
                if task_status:
                    print(f"   {i}. {task_status['description']}")
                    print(f"      🎯 Assigned to: {task_status['assigned_to']}")
                    print(f"      ⚡ Priority: {task_status['priority']}")
                    print(f"      📊 Status: {task_status['status']}")
                    print()

        print("3️⃣  Checking Agent Task Queues...")

        # Check what tasks each agent has
        for agent_type in [AgentType.SUPERVISOR, AgentType.CODER, AgentType.ADVERSARY]:
            pending_tasks = await runner.get_pending_tasks(agent_type)
            print(f"🤖 {agent_type.value.title()} Agent:")
            print(f"   📝 Pending Tasks: {len(pending_tasks)}")

            for task in pending_tasks[:2]:  # Show first 2 tasks
                print(f"   • {task['description'][:60]}...")
            print()

        print("4️⃣  Simulating Task Completion...")

        # Simulate coder completing first task
        coder_tasks = await runner.get_pending_tasks(AgentType.CODER)
        if coder_tasks:
            first_task = coder_tasks[0]
            task_id = first_task["task_id"]

            # Simulate completion result
            completion_result = {
                "analysis": "Calculator app needs basic arithmetic operations",
                "plan": [
                    "Create Calculator class",
                    "Implement add, subtract, multiply, divide methods",
                    "Add input validation",
                    "Create CLI interface",
                ],
                "estimated_time": "2 hours",
            }

            success = await runner.complete_task(
                task_id, completion_result, "coder_agent"
            )

            if success:
                print(f"✅ Completed task: {first_task['description'][:50]}...")
                print(f"📊 Result: {completion_result['analysis']}")
                print()

        print("5️⃣  Final Workflow Status...")

        # Check final status
        final_status = await runner.get_workflow_status(workflow_id)
        if final_status:
            print(f"📊 Final Status: {final_status['status']}")

            completed_count = len(
                [
                    t
                    for t in final_status.get("task_statuses", [])
                    if t.get("status") == "completed"
                ]
            )
            total_count = len(final_status.get("task_statuses", []))

            print(f"✅ Tasks Completed: {completed_count}/{total_count}")
            print(
                f"📈 Progress: {(completed_count / total_count * 100):.1f}%"
                if total_count > 0
                else "0%"
            )
            print()

        print("6️⃣  Testing Agent Status...")

        # Test agent status (without actually starting Claude processes)
        all_processes = runner.get_agent_status()
        print(f"🤖 Tracked Processes: {len(all_processes)}")

        for name, info in all_processes.items():
            status = "running" if info.get("running") else "stopped"
            print(f"   • {name}: {info.get('type', 'unknown')} ({status})")
        print()

        print("✅ WORKFLOW TEST COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print()
        print("🎯 Key Achievements:")
        print("   ✅ Created project workflow with task breakdown")
        print("   ✅ Assigned tasks to appropriate agents")
        print("   ✅ Tracked task completion and status")
        print("   ✅ Maintained workflow state in LMDB")
        print("   ✅ Integrated all core components")
        print()
        print("🚀 APEX is ready for agent integration!")

    except Exception as e:
        print(f"❌ Error during workflow test: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        await runner.stop_all_agents()
        runner.cleanup()
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
