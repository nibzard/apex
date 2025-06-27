"""Built-in utilities for the APEX framework."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from .base import (
    BaseUtility,
    CommandUtility,
    UtilityCategory,
    UtilityConfig,
    UtilityResult,
)


class CodeLinterUtility(CommandUtility):
    """Utility for running code linters."""

    def __init__(self, config: UtilityConfig):
        # Default to ruff for Python projects
        command = config.parameters.get("command", "ruff check {project_dir}")
        super().__init__(config, command, shell=True)

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Run code linting and style checks",
            parameters={
                "command": "ruff check {project_dir} --output-format=json",
                "include_fix": False,
            },
            timeout_seconds=120,
            required_tools=["ruff"],
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute linting with enhanced result processing."""
        result = await super().execute(context)

        # Parse linting output
        if result.status.value == "completed":
            stdout = result.output.get("stdout", "")
            stderr = result.output.get("stderr", "")

            # Try to parse JSON output
            try:
                if stdout.strip():
                    lint_results = json.loads(stdout)
                    result.metadata["lint_issues"] = len(lint_results)
                    result.metadata["issues"] = lint_results

                    # Categorize issues
                    issue_counts = {}
                    for issue in lint_results:
                        rule = issue.get("code", "unknown")
                        issue_counts[rule] = issue_counts.get(rule, 0) + 1

                    result.metadata["issue_counts"] = issue_counts
                else:
                    result.metadata["lint_issues"] = 0
                    result.metadata["clean"] = True

            except json.JSONDecodeError:
                # Fallback to stderr parsing
                if stderr:
                    result.add_warning(f"Could not parse linter output: {stderr}")

        return result


class TestRunnerUtility(BaseUtility):
    """Utility for running tests."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Run automated tests",
            parameters={
                "test_framework": "pytest",
                "test_path": "tests/",
                "coverage": True,
                "fail_fast": False,
            },
            timeout_seconds=300,
            required_tools=["pytest"],
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute tests."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            test_framework = self.config.parameters.get("test_framework", "pytest")
            test_path = self.config.parameters.get("test_path", "tests/")
            coverage = self.config.parameters.get("coverage", True)
            fail_fast = self.config.parameters.get("fail_fast", False)

            # Build test command
            if test_framework == "pytest":
                cmd = ["pytest", test_path]

                if coverage:
                    cmd.extend(["--cov", project_dir, "--cov-report", "json"])

                if fail_fast:
                    cmd.append("-x")

                cmd.extend(
                    [
                        "--tb=short",
                        "--json-report",
                        "--json-report-file=test_results.json",
                    ]
                )

            else:
                result.add_error(f"Unsupported test framework: {test_framework}")
                result.set_completed(False)
                return result

            # Execute tests
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            result.output = {
                "command": " ".join(cmd),
                "return_code": process.returncode,
                "stdout": stdout.decode("utf-8") if stdout else "",
                "stderr": stderr.decode("utf-8") if stderr else "",
            }

            # Parse test results
            await self._parse_test_results(result, project_dir)

            # Tests pass if return code is 0
            result.set_completed(process.returncode == 0)

        except Exception as e:
            result.add_error(f"Test execution failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _parse_test_results(self, result: UtilityResult, project_dir: str):
        """Parse test results from output files."""
        try:
            # Parse pytest JSON report
            report_path = Path(project_dir) / "test_results.json"
            if report_path.exists():
                with open(report_path) as f:
                    test_data = json.load(f)

                summary = test_data.get("summary", {})
                result.metadata["tests"] = {
                    "total": summary.get("total", 0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0),
                    "duration": test_data.get("duration", 0),
                }

                # Store failed test details
                if "failed" in test_data.get("tests", {}):
                    failed_tests = []
                    for test in test_data["tests"]:
                        if test.get("outcome") == "failed":
                            failed_tests.append(
                                {
                                    "name": test.get("nodeid", ""),
                                    "message": test.get("call", {}).get("longrepr", ""),
                                }
                            )
                    result.metadata["failed_tests"] = failed_tests

            # Parse coverage report
            coverage_path = Path(project_dir) / "coverage.json"
            if coverage_path.exists():
                with open(coverage_path) as f:
                    coverage_data = json.load(f)

                result.metadata["coverage"] = {
                    "total_statements": coverage_data.get("totals", {}).get(
                        "num_statements", 0
                    ),
                    "covered_statements": coverage_data.get("totals", {}).get(
                        "covered_lines", 0
                    ),
                    "coverage_percent": coverage_data.get("totals", {}).get(
                        "percent_covered", 0
                    ),
                }

        except Exception as e:
            result.add_warning(f"Could not parse test results: {str(e)}")

    def validate_config(self) -> List[str]:
        """Validate test runner configuration."""
        errors = []

        framework = self.config.parameters.get("test_framework")
        if framework and framework not in ["pytest", "unittest"]:
            errors.append(f"Unsupported test framework: {framework}")

        return errors


class ArchivistUtility(BaseUtility):
    """Utility for content summarization using direct API calls."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Summarize and archive project content using Claude API",
            parameters={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "temperature": 0.1,
                "include_patterns": [
                    "*.py",
                    "*.md",
                    "*.txt",
                    "*.json",
                    "*.yaml",
                    "*.yml",
                ],
                "exclude_patterns": [
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    "node_modules",
                    "venv",
                    ".env",
                ],
                "summary_types": [
                    "code_overview",
                    "documentation",
                    "changes",
                    "architecture",
                ],
                "chunk_size": 100000,  # characters per chunk
            },
            timeout_seconds=300,
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute content summarization."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            summary_types = self.config.parameters.get(
                "summary_types", ["code_overview"]
            )

            # Collect project content
            content = await self._collect_project_content(project_dir)

            if not content:
                result.add_warning("No content found to summarize")
                result.set_completed(True)
                return result

            # Generate summaries for each requested type
            summaries = {}

            for summary_type in summary_types:
                try:
                    summary = await self._generate_summary(content, summary_type)
                    summaries[summary_type] = summary
                except Exception as e:
                    result.add_error(
                        f"Failed to generate {summary_type} summary: {str(e)}"
                    )

            result.output["summaries"] = summaries
            result.metadata["content_size"] = len(str(content))
            result.metadata["summary_count"] = len(summaries)

            # Store summaries as artifacts
            await self._store_summaries(summaries, project_dir, result)

            result.set_completed(len(summaries) > 0)

        except Exception as e:
            result.add_error(f"Content summarization failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _collect_project_content(self, project_dir: str) -> Dict[str, Any]:
        """Collect relevant project content."""
        project_path = Path(project_dir)
        include_patterns = self.config.parameters.get("include_patterns", ["*.py"])
        exclude_patterns = self.config.parameters.get("exclude_patterns", [])

        content = {
            "files": {},
            "structure": [],
            "metadata": {
                "project_name": project_path.name,
                "total_files": 0,
                "total_size": 0,
            },
        }

        def should_include(file_path: Path) -> bool:
            """Check if file should be included."""
            # Check exclude patterns first
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    return False

            # Check include patterns
            for pattern in include_patterns:
                if file_path.match(pattern):
                    return True

            return False

        # Collect file content and structure
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and should_include(file_path):
                try:
                    relative_path = file_path.relative_to(project_path)

                    # Read file content
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()

                    content["files"][str(relative_path)] = {
                        "content": file_content,
                        "size": len(file_content),
                        "lines": len(file_content.splitlines()),
                    }

                    content["structure"].append(
                        {
                            "path": str(relative_path),
                            "size": len(file_content),
                            "type": file_path.suffix,
                        }
                    )

                    content["metadata"]["total_files"] += 1
                    content["metadata"]["total_size"] += len(file_content)

                except Exception:
                    # Skip files that can't be read
                    continue

        return content

    async def _generate_summary(
        self, content: Dict[str, Any], summary_type: str
    ) -> str:
        """Generate summary using Claude API via CLI."""
        model = self.config.parameters.get("model", "claude-3-5-sonnet-20241022")
        max_tokens = self.config.parameters.get("max_tokens", 4000)
        temperature = self.config.parameters.get("temperature", 0.1)

        # Create prompt based on summary type
        prompts = {
            "code_overview": """
Analyze this codebase and provide a comprehensive code overview. Include:
1. Main components and their purposes
2. Architecture patterns used
3. Key classes and functions
4. Dependencies and integrations
5. Code quality observations
6. Suggested improvements

Be concise but thorough. Focus on the most important aspects.
""",
            "documentation": """
Generate comprehensive documentation for this codebase. Include:
1. Project purpose and overview
2. Setup and installation instructions
3. Usage examples
4. API documentation for key components
5. Configuration options
6. Troubleshooting guide

Structure it as proper documentation with clear sections.
""",
            "changes": """
Analyze this codebase and summarize recent changes and evolution. Include:
1. Major architectural changes
2. New features added
3. Improvements and optimizations
4. Bug fixes and stability improvements
5. Deprecated or removed functionality
6. Migration notes if applicable

Focus on what has changed and why.
""",
            "architecture": """
Provide a detailed architectural analysis of this codebase. Include:
1. Overall system architecture
2. Component relationships and data flow
3. Design patterns employed
4. Scalability considerations
5. Security architecture
6. Performance characteristics
7. Areas for architectural improvement

Be technical and specific about architectural decisions.
""",
        }

        prompt = prompts.get(summary_type, prompts["code_overview"])

        # Prepare content for API
        content_text = self._format_content_for_api(content)

        # Create temporary file with content
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{prompt}\n\n--- PROJECT CONTENT ---\n\n{content_text}")
            temp_file = f.name

        try:
            # Use Claude CLI to generate summary
            cmd = [
                "claude",
                "--model",
                model,
                "--max-tokens",
                str(max_tokens),
                "--temperature",
                str(temperature),
                "--file",
                temp_file,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0 and stdout:
                summary = stdout.decode("utf-8").strip()
                return summary
            else:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise Exception(f"Claude API call failed: {error_msg}")

        finally:
            # Clean up temporary file
            try:
                Path(temp_file).unlink()
            except:
                pass

    def _format_content_for_api(self, content: Dict[str, Any]) -> str:
        """Format content for API consumption."""
        chunk_size = self.config.parameters.get("chunk_size", 100000)

        formatted_parts = []

        # Add project metadata
        metadata = content.get("metadata", {})
        formatted_parts.append(f"PROJECT: {metadata.get('project_name', 'Unknown')}")
        formatted_parts.append(f"Files: {metadata.get('total_files', 0)}")
        formatted_parts.append(
            f"Total Size: {metadata.get('total_size', 0)} characters"
        )
        formatted_parts.append("")

        # Add project structure
        structure = content.get("structure", [])
        if structure:
            formatted_parts.append("PROJECT STRUCTURE:")
            for item in structure[:50]:  # Limit structure items
                formatted_parts.append(f"  {item['path']} ({item['size']} chars)")
            formatted_parts.append("")

        # Add file contents (chunked if necessary)
        files = content.get("files", {})
        current_size = len("\n".join(formatted_parts))

        formatted_parts.append("FILE CONTENTS:")
        for file_path, file_info in files.items():
            file_content = file_info["content"]

            # Check if adding this file would exceed chunk size
            if current_size + len(file_content) > chunk_size:
                formatted_parts.append(
                    "\n[Content truncated - too large for single API call]"
                )
                break

            formatted_parts.append(f"\n--- {file_path} ---")
            formatted_parts.append(file_content)
            current_size += len(file_content) + len(file_path) + 10

        return "\n".join(formatted_parts)

    async def _store_summaries(
        self, summaries: Dict[str, str], project_dir: str, result: UtilityResult
    ):
        """Store generated summaries as artifacts."""
        project_path = Path(project_dir)
        summaries_dir = project_path / ".apex" / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)

        for summary_type, summary_content in summaries.items():
            summary_file = summaries_dir / f"{summary_type}_summary.md"

            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"# {summary_type.replace('_', ' ').title()} Summary\n\n")
                f.write("Generated by APEX Archivist Utility\n")
                f.write(f"Date: {result.started_at}\n\n")
                f.write("---\n\n")
                f.write(summary_content)

            result.add_artifact(str(summary_file))

    def validate_config(self) -> List[str]:
        """Validate archivist utility configuration."""
        errors = []

        model = self.config.parameters.get("model")
        if model and not model.startswith("claude-"):
            errors.append(f"Unsupported model: {model}")

        summary_types = self.config.parameters.get("summary_types", [])
        valid_types = ["code_overview", "documentation", "changes", "architecture"]

        for summary_type in summary_types:
            if summary_type not in valid_types:
                errors.append(f"Unsupported summary type: {summary_type}")

        max_tokens = self.config.parameters.get("max_tokens", 4000)
        if max_tokens > 8192:
            errors.append("max_tokens cannot exceed 8192")

        return errors


class GitManagerUtility(BaseUtility):
    """Utility for intelligent Git operations and commit generation."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Intelligent Git operations with AI-generated commit messages",
            parameters={
                "auto_stage": True,
                "generate_commit_message": True,
                "commit_message_style": "conventional",  # conventional, descriptive, concise
                "max_diff_size": 50000,  # characters
                "include_file_changes": True,
                "branch_strategy": "feature",  # feature, hotfix, release
                "push_after_commit": False,
            },
            timeout_seconds=120,
            required_tools=["git"],
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute Git operations."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            operation = context.get(
                "operation", "commit"
            )  # commit, status, branch, push

            # Check if we're in a Git repository
            if not await self._is_git_repo(project_dir):
                result.add_error("Not a Git repository")
                result.set_completed(False)
                return result

            if operation == "commit":
                success = await self._handle_commit(project_dir, result)
            elif operation == "status":
                success = await self._handle_status(project_dir, result)
            elif operation == "branch":
                success = await self._handle_branch(project_dir, result, context)
            elif operation == "push":
                success = await self._handle_push(project_dir, result)
            else:
                result.add_error(f"Unsupported Git operation: {operation}")
                success = False

            result.set_completed(success)

        except Exception as e:
            result.add_error(f"Git operation failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _is_git_repo(self, project_dir: str) -> bool:
        """Check if directory is a Git repository."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "--git-dir",
                cwd=project_dir,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False

    async def _handle_commit(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git commit with intelligent message generation."""
        try:
            # Get current status
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )

            if not status_output.strip():
                result.add_warning("No changes to commit")
                return True

            # Stage files if auto_stage is enabled
            if self.config.parameters.get("auto_stage", True):
                await self._run_git_command(["git", "add", "."], project_dir)

            # Get diff for commit message generation
            diff_output = await self._run_git_command(
                ["git", "diff", "--cached"], project_dir
            )

            if not diff_output.strip():
                result.add_warning("No staged changes to commit")
                return True

            # Generate commit message
            commit_message = await self._generate_commit_message(
                diff_output, status_output
            )

            # Commit changes
            commit_output = await self._run_git_command(
                ["git", "commit", "-m", commit_message], project_dir
            )

            result.output["commit"] = {
                "message": commit_message,
                "output": commit_output,
                "files_changed": len(
                    [line for line in status_output.split("\n") if line.strip()]
                ),
            }

            # Get commit hash
            commit_hash = await self._run_git_command(
                ["git", "rev-parse", "HEAD"], project_dir
            )
            result.metadata["commit_hash"] = commit_hash.strip()

            # Push if configured
            if self.config.parameters.get("push_after_commit", False):
                push_output = await self._run_git_command(["git", "push"], project_dir)
                result.output["push"] = push_output

            return True

        except Exception as e:
            result.add_error(f"Commit failed: {str(e)}")
            return False

    async def _handle_status(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git status check."""
        try:
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )
            branch_output = await self._run_git_command(
                ["git", "branch", "--show-current"], project_dir
            )

            result.output["status"] = {
                "porcelain": status_output,
                "current_branch": branch_output.strip(),
                "clean": not status_output.strip(),
            }

            # Parse status
            modified_files = []
            staged_files = []
            untracked_files = []

            for line in status_output.split("\n"):
                if line.strip():
                    status_code = line[:2]
                    filename = line[3:]

                    if status_code[0] in ["M", "A", "D", "R", "C"]:
                        staged_files.append(filename)
                    if status_code[1] in ["M", "D"]:
                        modified_files.append(filename)
                    if status_code == "??":
                        untracked_files.append(filename)

            result.metadata["files"] = {
                "staged": len(staged_files),
                "modified": len(modified_files),
                "untracked": len(untracked_files),
            }

            return True

        except Exception as e:
            result.add_error(f"Status check failed: {str(e)}")
            return False

    async def _handle_branch(
        self, project_dir: str, result: UtilityResult, context: Dict[str, Any]
    ) -> bool:
        """Handle Git branch operations."""
        try:
            branch_operation = context.get(
                "branch_operation", "list"
            )  # list, create, switch, delete
            branch_name = context.get("branch_name")

            if branch_operation == "list":
                branches_output = await self._run_git_command(
                    ["git", "branch", "-a"], project_dir
                )
                result.output["branches"] = branches_output

            elif branch_operation == "create" and branch_name:
                create_output = await self._run_git_command(
                    ["git", "branch", branch_name], project_dir
                )
                result.output["branch_create"] = create_output

            elif branch_operation == "switch" and branch_name:
                switch_output = await self._run_git_command(
                    ["git", "checkout", branch_name], project_dir
                )
                result.output["branch_switch"] = switch_output

            elif branch_operation == "delete" and branch_name:
                delete_output = await self._run_git_command(
                    ["git", "branch", "-d", branch_name], project_dir
                )
                result.output["branch_delete"] = delete_output

            else:
                result.add_error(f"Invalid branch operation: {branch_operation}")
                return False

            return True

        except Exception as e:
            result.add_error(f"Branch operation failed: {str(e)}")
            return False

    async def _handle_push(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git push operation."""
        try:
            push_output = await self._run_git_command(["git", "push"], project_dir)
            result.output["push"] = push_output
            return True

        except Exception as e:
            result.add_error(f"Push failed: {str(e)}")
            return False

    async def _run_git_command(self, cmd: List[str], project_dir: str) -> str:
        """Run a Git command and return output."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            raise Exception(f"Git command failed: {' '.join(cmd)} - {error_msg}")

        return stdout.decode("utf-8")

    async def _generate_commit_message(
        self, diff_output: str, status_output: str
    ) -> str:
        """Generate intelligent commit message using Claude API."""
        try:
            max_diff_size = self.config.parameters.get("max_diff_size", 50000)
            style = self.config.parameters.get("commit_message_style", "conventional")

            # Truncate diff if too large
            if len(diff_output) > max_diff_size:
                diff_output = diff_output[:max_diff_size] + "\n[... diff truncated ...]"

            # Create prompt for commit message generation
            prompt = f"""
Generate a {style} commit message for the following changes.

Style guidelines:
- conventional: Use conventional commit format (type(scope): description)
- descriptive: Clear, descriptive message explaining what changed
- concise: Brief but informative message

Git status:
{status_output}

Git diff:
{diff_output}

Generate only the commit message, no additional text or explanation.
"""

            # Use Claude CLI to generate commit message
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(prompt)
                temp_file = f.name

            try:
                cmd = [
                    "claude",
                    "--model",
                    "claude-3-5-sonnet-20241022",
                    "--max-tokens",
                    "200",
                    "--temperature",
                    "0.1",
                    "--file",
                    temp_file,
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0 and stdout:
                    commit_message = stdout.decode("utf-8").strip()
                    # Clean up any unwanted formatting
                    commit_message = commit_message.replace('"', "").replace("\n", " ")
                    return commit_message
                else:
                    # Fallback to simple message
                    return self._generate_fallback_commit_message(status_output)

            finally:
                try:
                    Path(temp_file).unlink()
                except:
                    pass

        except Exception:
            # Fallback to simple message generation
            return self._generate_fallback_commit_message(status_output)

    def _generate_fallback_commit_message(self, status_output: str) -> str:
        """Generate fallback commit message without API."""
        lines = [line for line in status_output.split("\n") if line.strip()]

        if not lines:
            return "Update project files"

        # Count different types of changes
        added = len([line for line in lines if line.startswith("A")])
        modified = len(
            [line for line in lines if line.startswith("M") or line.startswith(" M")]
        )
        deleted = len([line for line in lines if line.startswith("D")])

        # Generate message based on changes
        if added and not modified and not deleted:
            return f"Add {added} new file{'s' if added > 1 else ''}"
        elif modified and not added and not deleted:
            return f"Update {modified} file{'s' if modified > 1 else ''}"
        elif deleted and not added and not modified:
            return f"Remove {deleted} file{'s' if deleted > 1 else ''}"
        else:
            total = added + modified + deleted
            return f"Update project: {total} file{'s' if total > 1 else ''} changed"

    def validate_config(self) -> List[str]:
        """Validate Git manager configuration."""
        errors = []

        style = self.config.parameters.get("commit_message_style")
        if style and style not in ["conventional", "descriptive", "concise"]:
            errors.append(f"Unsupported commit message style: {style}")

        branch_strategy = self.config.parameters.get("branch_strategy")
        if branch_strategy and branch_strategy not in [
            "feature",
            "hotfix",
            "release",
            "main",
        ]:
            errors.append(f"Unsupported branch strategy: {branch_strategy}")

        return errors


class DocumentationGeneratorUtility(BaseUtility):
    """Utility for generating documentation."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Generate project documentation",
            parameters={
                "tool": "mkdocs",
                "config_file": "mkdocs.yml",
                "output_dir": "docs/",
                "auto_generate": True,
            },
            timeout_seconds=180,
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Generate documentation."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            tool = self.config.parameters.get("tool", "mkdocs")
            auto_generate = self.config.parameters.get("auto_generate", True)

            if tool == "mkdocs":
                await self._generate_mkdocs(result, project_dir, auto_generate)
            else:
                result.add_error(f"Unsupported documentation tool: {tool}")
                result.set_completed(False)

        except Exception as e:
            result.add_error(f"Documentation generation failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _generate_mkdocs(
        self, result: UtilityResult, project_dir: str, auto_generate: bool
    ):
        """Generate MkDocs documentation."""
        project_path = Path(project_dir)
        config_file = project_path / self.config.parameters.get(
            "config_file", "mkdocs.yml"
        )

        if auto_generate and not config_file.exists():
            # Auto-generate basic mkdocs.yml
            mkdocs_config = {
                "site_name": project_path.name,
                "theme": {"name": "material"},
                "nav": [
                    {"Home": "index.md"},
                    {"API": "api.md"},
                ],
            }

            with open(config_file, "w") as f:
                import yaml

                yaml.dump(mkdocs_config, f)

            result.add_artifact(str(config_file))

            # Create basic documentation files
            docs_dir = project_path / "docs"
            docs_dir.mkdir(exist_ok=True)

            # Create index.md
            index_path = docs_dir / "index.md"
            if not index_path.exists():
                with open(index_path, "w") as f:
                    f.write(f"# {project_path.name}\n\nProject documentation.\n")
                result.add_artifact(str(index_path))

        # Build documentation
        cmd = ["mkdocs", "build"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        result.output = {
            "command": " ".join(cmd),
            "return_code": process.returncode,
            "stdout": stdout.decode("utf-8") if stdout else "",
            "stderr": stderr.decode("utf-8") if stderr else "",
        }

        if process.returncode == 0:
            # Count generated files
            site_dir = project_path / "site"
            if site_dir.exists():
                html_files = list(site_dir.rglob("*.html"))
                result.metadata["generated_pages"] = len(html_files)
                result.add_artifact(str(site_dir))

            result.set_completed(True)
        else:
            result.add_error(
                f"MkDocs build failed: {stderr.decode('utf-8') if stderr else 'Unknown error'}"
            )
            result.set_completed(False)

    def validate_config(self) -> List[str]:
        """Validate documentation generator configuration."""
        errors = []

        tool = self.config.parameters.get("tool")
        if tool and tool not in ["mkdocs", "sphinx"]:
            errors.append(f"Unsupported documentation tool: {tool}")

        return errors


class ArchivistUtility(BaseUtility):
    """Utility for content summarization using direct API calls."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Summarize and archive project content using Claude API",
            parameters={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "temperature": 0.1,
                "include_patterns": [
                    "*.py",
                    "*.md",
                    "*.txt",
                    "*.json",
                    "*.yaml",
                    "*.yml",
                ],
                "exclude_patterns": [
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    "node_modules",
                    "venv",
                    ".env",
                ],
                "summary_types": [
                    "code_overview",
                    "documentation",
                    "changes",
                    "architecture",
                ],
                "chunk_size": 100000,  # characters per chunk
            },
            timeout_seconds=300,
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute content summarization."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            summary_types = self.config.parameters.get(
                "summary_types", ["code_overview"]
            )

            # Collect project content
            content = await self._collect_project_content(project_dir)

            if not content:
                result.add_warning("No content found to summarize")
                result.set_completed(True)
                return result

            # Generate summaries for each requested type
            summaries = {}

            for summary_type in summary_types:
                try:
                    summary = await self._generate_summary(content, summary_type)
                    summaries[summary_type] = summary
                except Exception as e:
                    result.add_error(
                        f"Failed to generate {summary_type} summary: {str(e)}"
                    )

            result.output["summaries"] = summaries
            result.metadata["content_size"] = len(str(content))
            result.metadata["summary_count"] = len(summaries)

            # Store summaries as artifacts
            await self._store_summaries(summaries, project_dir, result)

            result.set_completed(len(summaries) > 0)

        except Exception as e:
            result.add_error(f"Content summarization failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _collect_project_content(self, project_dir: str) -> Dict[str, Any]:
        """Collect relevant project content."""
        project_path = Path(project_dir)
        include_patterns = self.config.parameters.get("include_patterns", ["*.py"])
        exclude_patterns = self.config.parameters.get("exclude_patterns", [])

        content = {
            "files": {},
            "structure": [],
            "metadata": {
                "project_name": project_path.name,
                "total_files": 0,
                "total_size": 0,
            },
        }

        def should_include(file_path: Path) -> bool:
            """Check if file should be included."""
            # Check exclude patterns first
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    return False

            # Check include patterns
            for pattern in include_patterns:
                if file_path.match(pattern):
                    return True

            return False

        # Collect file content and structure
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and should_include(file_path):
                try:
                    relative_path = file_path.relative_to(project_path)

                    # Read file content
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()

                    content["files"][str(relative_path)] = {
                        "content": file_content,
                        "size": len(file_content),
                        "lines": len(file_content.splitlines()),
                    }

                    content["structure"].append(
                        {
                            "path": str(relative_path),
                            "size": len(file_content),
                            "type": file_path.suffix,
                        }
                    )

                    content["metadata"]["total_files"] += 1
                    content["metadata"]["total_size"] += len(file_content)

                except Exception:
                    # Skip files that can't be read
                    continue

        return content

    async def _generate_summary(
        self, content: Dict[str, Any], summary_type: str
    ) -> str:
        """Generate summary using Claude API via CLI."""
        model = self.config.parameters.get("model", "claude-3-5-sonnet-20241022")
        max_tokens = self.config.parameters.get("max_tokens", 4000)
        temperature = self.config.parameters.get("temperature", 0.1)

        # Create prompt based on summary type
        prompts = {
            "code_overview": """
Analyze this codebase and provide a comprehensive code overview. Include:
1. Main components and their purposes
2. Architecture patterns used
3. Key classes and functions
4. Dependencies and integrations
5. Code quality observations
6. Suggested improvements

Be concise but thorough. Focus on the most important aspects.
""",
            "documentation": """
Generate comprehensive documentation for this codebase. Include:
1. Project purpose and overview
2. Setup and installation instructions
3. Usage examples
4. API documentation for key components
5. Configuration options
6. Troubleshooting guide

Structure it as proper documentation with clear sections.
""",
            "changes": """
Analyze this codebase and summarize recent changes and evolution. Include:
1. Major architectural changes
2. New features added
3. Improvements and optimizations
4. Bug fixes and stability improvements
5. Deprecated or removed functionality
6. Migration notes if applicable

Focus on what has changed and why.
""",
            "architecture": """
Provide a detailed architectural analysis of this codebase. Include:
1. Overall system architecture
2. Component relationships and data flow
3. Design patterns employed
4. Scalability considerations
5. Security architecture
6. Performance characteristics
7. Areas for architectural improvement

Be technical and specific about architectural decisions.
""",
        }

        prompt = prompts.get(summary_type, prompts["code_overview"])

        # Prepare content for API
        content_text = self._format_content_for_api(content)

        # Create temporary file with content
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{prompt}\n\n--- PROJECT CONTENT ---\n\n{content_text}")
            temp_file = f.name

        try:
            # Use Claude CLI to generate summary
            cmd = [
                "claude",
                "--model",
                model,
                "--max-tokens",
                str(max_tokens),
                "--temperature",
                str(temperature),
                "--file",
                temp_file,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0 and stdout:
                summary = stdout.decode("utf-8").strip()
                return summary
            else:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise Exception(f"Claude API call failed: {error_msg}")

        finally:
            # Clean up temporary file
            try:
                Path(temp_file).unlink()
            except:
                pass

    def _format_content_for_api(self, content: Dict[str, Any]) -> str:
        """Format content for API consumption."""
        chunk_size = self.config.parameters.get("chunk_size", 100000)

        formatted_parts = []

        # Add project metadata
        metadata = content.get("metadata", {})
        formatted_parts.append(f"PROJECT: {metadata.get('project_name', 'Unknown')}")
        formatted_parts.append(f"Files: {metadata.get('total_files', 0)}")
        formatted_parts.append(
            f"Total Size: {metadata.get('total_size', 0)} characters"
        )
        formatted_parts.append("")

        # Add project structure
        structure = content.get("structure", [])
        if structure:
            formatted_parts.append("PROJECT STRUCTURE:")
            for item in structure[:50]:  # Limit structure items
                formatted_parts.append(f"  {item['path']} ({item['size']} chars)")
            formatted_parts.append("")

        # Add file contents (chunked if necessary)
        files = content.get("files", {})
        current_size = len("\n".join(formatted_parts))

        formatted_parts.append("FILE CONTENTS:")
        for file_path, file_info in files.items():
            file_content = file_info["content"]

            # Check if adding this file would exceed chunk size
            if current_size + len(file_content) > chunk_size:
                formatted_parts.append(
                    "\n[Content truncated - too large for single API call]"
                )
                break

            formatted_parts.append(f"\n--- {file_path} ---")
            formatted_parts.append(file_content)
            current_size += len(file_content) + len(file_path) + 10

        return "\n".join(formatted_parts)

    async def _store_summaries(
        self, summaries: Dict[str, str], project_dir: str, result: UtilityResult
    ):
        """Store generated summaries as artifacts."""
        project_path = Path(project_dir)
        summaries_dir = project_path / ".apex" / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)

        for summary_type, summary_content in summaries.items():
            summary_file = summaries_dir / f"{summary_type}_summary.md"

            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"# {summary_type.replace('_', ' ').title()} Summary\n\n")
                f.write("Generated by APEX Archivist Utility\n")
                f.write(f"Date: {result.started_at}\n\n")
                f.write("---\n\n")
                f.write(summary_content)

            result.add_artifact(str(summary_file))

    def validate_config(self) -> List[str]:
        """Validate archivist utility configuration."""
        errors = []

        model = self.config.parameters.get("model")
        if model and not model.startswith("claude-"):
            errors.append(f"Unsupported model: {model}")

        summary_types = self.config.parameters.get("summary_types", [])
        valid_types = ["code_overview", "documentation", "changes", "architecture"]

        for summary_type in summary_types:
            if summary_type not in valid_types:
                errors.append(f"Unsupported summary type: {summary_type}")

        max_tokens = self.config.parameters.get("max_tokens", 4000)
        if max_tokens > 8192:
            errors.append("max_tokens cannot exceed 8192")

        return errors


class GitManagerUtility(BaseUtility):
    """Utility for intelligent Git operations and commit generation."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Intelligent Git operations with AI-generated commit messages",
            parameters={
                "auto_stage": True,
                "generate_commit_message": True,
                "commit_message_style": "conventional",  # conventional, descriptive, concise
                "max_diff_size": 50000,  # characters
                "include_file_changes": True,
                "branch_strategy": "feature",  # feature, hotfix, release
                "push_after_commit": False,
            },
            timeout_seconds=120,
            required_tools=["git"],
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute Git operations."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            operation = context.get(
                "operation", "commit"
            )  # commit, status, branch, push

            # Check if we're in a Git repository
            if not await self._is_git_repo(project_dir):
                result.add_error("Not a Git repository")
                result.set_completed(False)
                return result

            if operation == "commit":
                success = await self._handle_commit(project_dir, result)
            elif operation == "status":
                success = await self._handle_status(project_dir, result)
            elif operation == "branch":
                success = await self._handle_branch(project_dir, result, context)
            elif operation == "push":
                success = await self._handle_push(project_dir, result)
            else:
                result.add_error(f"Unsupported Git operation: {operation}")
                success = False

            result.set_completed(success)

        except Exception as e:
            result.add_error(f"Git operation failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _is_git_repo(self, project_dir: str) -> bool:
        """Check if directory is a Git repository."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "--git-dir",
                cwd=project_dir,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False

    async def _handle_commit(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git commit with intelligent message generation."""
        try:
            # Get current status
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )

            if not status_output.strip():
                result.add_warning("No changes to commit")
                return True

            # Stage files if auto_stage is enabled
            if self.config.parameters.get("auto_stage", True):
                await self._run_git_command(["git", "add", "."], project_dir)

            # Get diff for commit message generation
            diff_output = await self._run_git_command(
                ["git", "diff", "--cached"], project_dir
            )

            if not diff_output.strip():
                result.add_warning("No staged changes to commit")
                return True

            # Generate commit message
            commit_message = await self._generate_commit_message(
                diff_output, status_output
            )

            # Commit changes
            commit_output = await self._run_git_command(
                ["git", "commit", "-m", commit_message], project_dir
            )

            result.output["commit"] = {
                "message": commit_message,
                "output": commit_output,
                "files_changed": len(
                    [line for line in status_output.split("\n") if line.strip()]
                ),
            }

            # Get commit hash
            commit_hash = await self._run_git_command(
                ["git", "rev-parse", "HEAD"], project_dir
            )
            result.metadata["commit_hash"] = commit_hash.strip()

            # Push if configured
            if self.config.parameters.get("push_after_commit", False):
                push_output = await self._run_git_command(["git", "push"], project_dir)
                result.output["push"] = push_output

            return True

        except Exception as e:
            result.add_error(f"Commit failed: {str(e)}")
            return False

    async def _handle_status(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git status check."""
        try:
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )
            branch_output = await self._run_git_command(
                ["git", "branch", "--show-current"], project_dir
            )

            result.output["status"] = {
                "porcelain": status_output,
                "current_branch": branch_output.strip(),
                "clean": not status_output.strip(),
            }

            # Parse status
            modified_files = []
            staged_files = []
            untracked_files = []

            for line in status_output.split("\n"):
                if line.strip():
                    status_code = line[:2]
                    filename = line[3:]

                    if status_code[0] in ["M", "A", "D", "R", "C"]:
                        staged_files.append(filename)
                    if status_code[1] in ["M", "D"]:
                        modified_files.append(filename)
                    if status_code == "??":
                        untracked_files.append(filename)

            result.metadata["files"] = {
                "staged": len(staged_files),
                "modified": len(modified_files),
                "untracked": len(untracked_files),
            }

            return True

        except Exception as e:
            result.add_error(f"Status check failed: {str(e)}")
            return False

    async def _handle_branch(
        self, project_dir: str, result: UtilityResult, context: Dict[str, Any]
    ) -> bool:
        """Handle Git branch operations."""
        try:
            branch_operation = context.get(
                "branch_operation", "list"
            )  # list, create, switch, delete
            branch_name = context.get("branch_name")

            if branch_operation == "list":
                branches_output = await self._run_git_command(
                    ["git", "branch", "-a"], project_dir
                )
                result.output["branches"] = branches_output

            elif branch_operation == "create" and branch_name:
                create_output = await self._run_git_command(
                    ["git", "branch", branch_name], project_dir
                )
                result.output["branch_create"] = create_output

            elif branch_operation == "switch" and branch_name:
                switch_output = await self._run_git_command(
                    ["git", "checkout", branch_name], project_dir
                )
                result.output["branch_switch"] = switch_output

            elif branch_operation == "delete" and branch_name:
                delete_output = await self._run_git_command(
                    ["git", "branch", "-d", branch_name], project_dir
                )
                result.output["branch_delete"] = delete_output

            else:
                result.add_error(f"Invalid branch operation: {branch_operation}")
                return False

            return True

        except Exception as e:
            result.add_error(f"Branch operation failed: {str(e)}")
            return False

    async def _handle_push(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git push operation."""
        try:
            push_output = await self._run_git_command(["git", "push"], project_dir)
            result.output["push"] = push_output
            return True

        except Exception as e:
            result.add_error(f"Push failed: {str(e)}")
            return False

    async def _run_git_command(self, cmd: List[str], project_dir: str) -> str:
        """Run a Git command and return output."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            raise Exception(f"Git command failed: {' '.join(cmd)} - {error_msg}")

        return stdout.decode("utf-8")

    async def _generate_commit_message(
        self, diff_output: str, status_output: str
    ) -> str:
        """Generate intelligent commit message using Claude API."""
        try:
            max_diff_size = self.config.parameters.get("max_diff_size", 50000)
            style = self.config.parameters.get("commit_message_style", "conventional")

            # Truncate diff if too large
            if len(diff_output) > max_diff_size:
                diff_output = diff_output[:max_diff_size] + "\n[... diff truncated ...]"

            # Create prompt for commit message generation
            prompt = f"""
Generate a {style} commit message for the following changes.

Style guidelines:
- conventional: Use conventional commit format (type(scope): description)
- descriptive: Clear, descriptive message explaining what changed
- concise: Brief but informative message

Git status:
{status_output}

Git diff:
{diff_output}

Generate only the commit message, no additional text or explanation.
"""

            # Use Claude CLI to generate commit message
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(prompt)
                temp_file = f.name

            try:
                cmd = [
                    "claude",
                    "--model",
                    "claude-3-5-sonnet-20241022",
                    "--max-tokens",
                    "200",
                    "--temperature",
                    "0.1",
                    "--file",
                    temp_file,
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0 and stdout:
                    commit_message = stdout.decode("utf-8").strip()
                    # Clean up any unwanted formatting
                    commit_message = commit_message.replace('"', "").replace("\n", " ")
                    return commit_message
                else:
                    # Fallback to simple message
                    return self._generate_fallback_commit_message(status_output)

            finally:
                try:
                    Path(temp_file).unlink()
                except:
                    pass

        except Exception:
            # Fallback to simple message generation
            return self._generate_fallback_commit_message(status_output)

    def _generate_fallback_commit_message(self, status_output: str) -> str:
        """Generate fallback commit message without API."""
        lines = [line for line in status_output.split("\n") if line.strip()]

        if not lines:
            return "Update project files"

        # Count different types of changes
        added = len([line for line in lines if line.startswith("A")])
        modified = len(
            [line for line in lines if line.startswith("M") or line.startswith(" M")]
        )
        deleted = len([line for line in lines if line.startswith("D")])

        # Generate message based on changes
        if added and not modified and not deleted:
            return f"Add {added} new file{'s' if added > 1 else ''}"
        elif modified and not added and not deleted:
            return f"Update {modified} file{'s' if modified > 1 else ''}"
        elif deleted and not added and not modified:
            return f"Remove {deleted} file{'s' if deleted > 1 else ''}"
        else:
            total = added + modified + deleted
            return f"Update project: {total} file{'s' if total > 1 else ''} changed"

    def validate_config(self) -> List[str]:
        """Validate Git manager configuration."""
        errors = []

        style = self.config.parameters.get("commit_message_style")
        if style and style not in ["conventional", "descriptive", "concise"]:
            errors.append(f"Unsupported commit message style: {style}")

        branch_strategy = self.config.parameters.get("branch_strategy")
        if branch_strategy and branch_strategy not in [
            "feature",
            "hotfix",
            "release",
            "main",
        ]:
            errors.append(f"Unsupported branch strategy: {branch_strategy}")

        return errors


class SecurityScannerUtility(BaseUtility):
    """Utility for security scanning."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Scan for security vulnerabilities",
            parameters={
                "tools": ["bandit", "safety"],
                "include_dependencies": True,
                "severity_threshold": "medium",
            },
            timeout_seconds=240,
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute security scan."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            tools = self.config.parameters.get("tools", ["bandit"])

            scan_results = {}

            for tool in tools:
                if tool == "bandit":
                    tool_result = await self._run_bandit(project_dir)
                elif tool == "safety":
                    tool_result = await self._run_safety(project_dir)
                else:
                    tool_result = {"error": f"Unknown security tool: {tool}"}

                scan_results[tool] = tool_result

            result.output["scan_results"] = scan_results

            # Aggregate results
            total_issues = 0
            high_severity = 0

            for tool, tool_result in scan_results.items():
                if "issues" in tool_result:
                    issues = tool_result["issues"]
                    total_issues += len(issues)

                    for issue in issues:
                        if issue.get("severity", "").lower() in ["high", "critical"]:
                            high_severity += 1

            result.metadata["total_issues"] = total_issues
            result.metadata["high_severity_issues"] = high_severity

            # Set completion status
            threshold = self.config.parameters.get("severity_threshold", "medium")
            if threshold == "high" and high_severity == 0:
                result.set_completed(True)
            elif threshold == "medium" and total_issues == 0:
                result.set_completed(True)
            else:
                result.set_completed(total_issues == 0)

        except Exception as e:
            result.add_error(f"Security scan failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _run_bandit(self, project_dir: str) -> Dict[str, Any]:
        """Run Bandit security scanner."""
        try:
            cmd = ["bandit", "-r", project_dir, "-f", "json"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if stdout:
                bandit_data = json.loads(stdout.decode("utf-8"))
                issues = bandit_data.get("results", [])

                return {
                    "tool": "bandit",
                    "issues": issues,
                    "summary": bandit_data.get("metrics", {}),
                }
            else:
                return {
                    "tool": "bandit",
                    "issues": [],
                    "error": stderr.decode("utf-8") if stderr else "No output",
                }

        except Exception as e:
            return {"tool": "bandit", "error": str(e)}

    async def _run_safety(self, project_dir: str) -> Dict[str, Any]:
        """Run Safety dependency scanner."""
        try:
            cmd = ["safety", "check", "--json"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if stdout:
                safety_data = json.loads(stdout.decode("utf-8"))

                return {
                    "tool": "safety",
                    "issues": safety_data,
                    "summary": {"vulnerable_packages": len(safety_data)},
                }
            else:
                return {
                    "tool": "safety",
                    "issues": [],
                    "message": "No vulnerabilities found",
                }

        except Exception as e:
            return {"tool": "safety", "error": str(e)}

    def validate_config(self) -> List[str]:
        """Validate security scanner configuration."""
        errors = []

        tools = self.config.parameters.get("tools", [])
        supported_tools = ["bandit", "safety", "semgrep"]

        for tool in tools:
            if tool not in supported_tools:
                errors.append(f"Unsupported security tool: {tool}")

        return errors


class ArchivistUtility(BaseUtility):
    """Utility for content summarization using direct API calls."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Summarize and archive project content using Claude API",
            parameters={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "temperature": 0.1,
                "include_patterns": [
                    "*.py",
                    "*.md",
                    "*.txt",
                    "*.json",
                    "*.yaml",
                    "*.yml",
                ],
                "exclude_patterns": [
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    "node_modules",
                    "venv",
                    ".env",
                ],
                "summary_types": [
                    "code_overview",
                    "documentation",
                    "changes",
                    "architecture",
                ],
                "chunk_size": 100000,  # characters per chunk
            },
            timeout_seconds=300,
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute content summarization."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            summary_types = self.config.parameters.get(
                "summary_types", ["code_overview"]
            )

            # Collect project content
            content = await self._collect_project_content(project_dir)

            if not content:
                result.add_warning("No content found to summarize")
                result.set_completed(True)
                return result

            # Generate summaries for each requested type
            summaries = {}

            for summary_type in summary_types:
                try:
                    summary = await self._generate_summary(content, summary_type)
                    summaries[summary_type] = summary
                except Exception as e:
                    result.add_error(
                        f"Failed to generate {summary_type} summary: {str(e)}"
                    )

            result.output["summaries"] = summaries
            result.metadata["content_size"] = len(str(content))
            result.metadata["summary_count"] = len(summaries)

            # Store summaries as artifacts
            await self._store_summaries(summaries, project_dir, result)

            result.set_completed(len(summaries) > 0)

        except Exception as e:
            result.add_error(f"Content summarization failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _collect_project_content(self, project_dir: str) -> Dict[str, Any]:
        """Collect relevant project content."""
        project_path = Path(project_dir)
        include_patterns = self.config.parameters.get("include_patterns", ["*.py"])
        exclude_patterns = self.config.parameters.get("exclude_patterns", [])

        content = {
            "files": {},
            "structure": [],
            "metadata": {
                "project_name": project_path.name,
                "total_files": 0,
                "total_size": 0,
            },
        }

        def should_include(file_path: Path) -> bool:
            """Check if file should be included."""
            # Check exclude patterns first
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    return False

            # Check include patterns
            for pattern in include_patterns:
                if file_path.match(pattern):
                    return True

            return False

        # Collect file content and structure
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and should_include(file_path):
                try:
                    relative_path = file_path.relative_to(project_path)

                    # Read file content
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()

                    content["files"][str(relative_path)] = {
                        "content": file_content,
                        "size": len(file_content),
                        "lines": len(file_content.splitlines()),
                    }

                    content["structure"].append(
                        {
                            "path": str(relative_path),
                            "size": len(file_content),
                            "type": file_path.suffix,
                        }
                    )

                    content["metadata"]["total_files"] += 1
                    content["metadata"]["total_size"] += len(file_content)

                except Exception:
                    # Skip files that can't be read
                    continue

        return content

    async def _generate_summary(
        self, content: Dict[str, Any], summary_type: str
    ) -> str:
        """Generate summary using Claude API via CLI."""
        model = self.config.parameters.get("model", "claude-3-5-sonnet-20241022")
        max_tokens = self.config.parameters.get("max_tokens", 4000)
        temperature = self.config.parameters.get("temperature", 0.1)

        # Create prompt based on summary type
        prompts = {
            "code_overview": """
Analyze this codebase and provide a comprehensive code overview. Include:
1. Main components and their purposes
2. Architecture patterns used
3. Key classes and functions
4. Dependencies and integrations
5. Code quality observations
6. Suggested improvements

Be concise but thorough. Focus on the most important aspects.
""",
            "documentation": """
Generate comprehensive documentation for this codebase. Include:
1. Project purpose and overview
2. Setup and installation instructions
3. Usage examples
4. API documentation for key components
5. Configuration options
6. Troubleshooting guide

Structure it as proper documentation with clear sections.
""",
            "changes": """
Analyze this codebase and summarize recent changes and evolution. Include:
1. Major architectural changes
2. New features added
3. Improvements and optimizations
4. Bug fixes and stability improvements
5. Deprecated or removed functionality
6. Migration notes if applicable

Focus on what has changed and why.
""",
            "architecture": """
Provide a detailed architectural analysis of this codebase. Include:
1. Overall system architecture
2. Component relationships and data flow
3. Design patterns employed
4. Scalability considerations
5. Security architecture
6. Performance characteristics
7. Areas for architectural improvement

Be technical and specific about architectural decisions.
""",
        }

        prompt = prompts.get(summary_type, prompts["code_overview"])

        # Prepare content for API
        content_text = self._format_content_for_api(content)

        # Create temporary file with content
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{prompt}\n\n--- PROJECT CONTENT ---\n\n{content_text}")
            temp_file = f.name

        try:
            # Use Claude CLI to generate summary
            cmd = [
                "claude",
                "--model",
                model,
                "--max-tokens",
                str(max_tokens),
                "--temperature",
                str(temperature),
                "--file",
                temp_file,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0 and stdout:
                summary = stdout.decode("utf-8").strip()
                return summary
            else:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise Exception(f"Claude API call failed: {error_msg}")

        finally:
            # Clean up temporary file
            try:
                Path(temp_file).unlink()
            except:
                pass

    def _format_content_for_api(self, content: Dict[str, Any]) -> str:
        """Format content for API consumption."""
        chunk_size = self.config.parameters.get("chunk_size", 100000)

        formatted_parts = []

        # Add project metadata
        metadata = content.get("metadata", {})
        formatted_parts.append(f"PROJECT: {metadata.get('project_name', 'Unknown')}")
        formatted_parts.append(f"Files: {metadata.get('total_files', 0)}")
        formatted_parts.append(
            f"Total Size: {metadata.get('total_size', 0)} characters"
        )
        formatted_parts.append("")

        # Add project structure
        structure = content.get("structure", [])
        if structure:
            formatted_parts.append("PROJECT STRUCTURE:")
            for item in structure[:50]:  # Limit structure items
                formatted_parts.append(f"  {item['path']} ({item['size']} chars)")
            formatted_parts.append("")

        # Add file contents (chunked if necessary)
        files = content.get("files", {})
        current_size = len("\n".join(formatted_parts))

        formatted_parts.append("FILE CONTENTS:")
        for file_path, file_info in files.items():
            file_content = file_info["content"]

            # Check if adding this file would exceed chunk size
            if current_size + len(file_content) > chunk_size:
                formatted_parts.append(
                    "\n[Content truncated - too large for single API call]"
                )
                break

            formatted_parts.append(f"\n--- {file_path} ---")
            formatted_parts.append(file_content)
            current_size += len(file_content) + len(file_path) + 10

        return "\n".join(formatted_parts)

    async def _store_summaries(
        self, summaries: Dict[str, str], project_dir: str, result: UtilityResult
    ):
        """Store generated summaries as artifacts."""
        project_path = Path(project_dir)
        summaries_dir = project_path / ".apex" / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)

        for summary_type, summary_content in summaries.items():
            summary_file = summaries_dir / f"{summary_type}_summary.md"

            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"# {summary_type.replace('_', ' ').title()} Summary\n\n")
                f.write("Generated by APEX Archivist Utility\n")
                f.write(f"Date: {result.started_at}\n\n")
                f.write("---\n\n")
                f.write(summary_content)

            result.add_artifact(str(summary_file))

    def validate_config(self) -> List[str]:
        """Validate archivist utility configuration."""
        errors = []

        model = self.config.parameters.get("model")
        if model and not model.startswith("claude-"):
            errors.append(f"Unsupported model: {model}")

        summary_types = self.config.parameters.get("summary_types", [])
        valid_types = ["code_overview", "documentation", "changes", "architecture"]

        for summary_type in summary_types:
            if summary_type not in valid_types:
                errors.append(f"Unsupported summary type: {summary_type}")

        max_tokens = self.config.parameters.get("max_tokens", 4000)
        if max_tokens > 8192:
            errors.append("max_tokens cannot exceed 8192")

        return errors


class GitManagerUtility(BaseUtility):
    """Utility for intelligent Git operations and commit generation."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Intelligent Git operations with AI-generated commit messages",
            parameters={
                "auto_stage": True,
                "generate_commit_message": True,
                "commit_message_style": "conventional",  # conventional, descriptive, concise
                "max_diff_size": 50000,  # characters
                "include_file_changes": True,
                "branch_strategy": "feature",  # feature, hotfix, release
                "push_after_commit": False,
            },
            timeout_seconds=120,
            required_tools=["git"],
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute Git operations."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            operation = context.get(
                "operation", "commit"
            )  # commit, status, branch, push

            # Check if we're in a Git repository
            if not await self._is_git_repo(project_dir):
                result.add_error("Not a Git repository")
                result.set_completed(False)
                return result

            if operation == "commit":
                success = await self._handle_commit(project_dir, result)
            elif operation == "status":
                success = await self._handle_status(project_dir, result)
            elif operation == "branch":
                success = await self._handle_branch(project_dir, result, context)
            elif operation == "push":
                success = await self._handle_push(project_dir, result)
            else:
                result.add_error(f"Unsupported Git operation: {operation}")
                success = False

            result.set_completed(success)

        except Exception as e:
            result.add_error(f"Git operation failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _is_git_repo(self, project_dir: str) -> bool:
        """Check if directory is a Git repository."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "--git-dir",
                cwd=project_dir,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False

    async def _handle_commit(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git commit with intelligent message generation."""
        try:
            # Get current status
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )

            if not status_output.strip():
                result.add_warning("No changes to commit")
                return True

            # Stage files if auto_stage is enabled
            if self.config.parameters.get("auto_stage", True):
                await self._run_git_command(["git", "add", "."], project_dir)

            # Get diff for commit message generation
            diff_output = await self._run_git_command(
                ["git", "diff", "--cached"], project_dir
            )

            if not diff_output.strip():
                result.add_warning("No staged changes to commit")
                return True

            # Generate commit message
            commit_message = await self._generate_commit_message(
                diff_output, status_output
            )

            # Commit changes
            commit_output = await self._run_git_command(
                ["git", "commit", "-m", commit_message], project_dir
            )

            result.output["commit"] = {
                "message": commit_message,
                "output": commit_output,
                "files_changed": len(
                    [line for line in status_output.split("\n") if line.strip()]
                ),
            }

            # Get commit hash
            commit_hash = await self._run_git_command(
                ["git", "rev-parse", "HEAD"], project_dir
            )
            result.metadata["commit_hash"] = commit_hash.strip()

            # Push if configured
            if self.config.parameters.get("push_after_commit", False):
                push_output = await self._run_git_command(["git", "push"], project_dir)
                result.output["push"] = push_output

            return True

        except Exception as e:
            result.add_error(f"Commit failed: {str(e)}")
            return False

    async def _handle_status(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git status check."""
        try:
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )
            branch_output = await self._run_git_command(
                ["git", "branch", "--show-current"], project_dir
            )

            result.output["status"] = {
                "porcelain": status_output,
                "current_branch": branch_output.strip(),
                "clean": not status_output.strip(),
            }

            # Parse status
            modified_files = []
            staged_files = []
            untracked_files = []

            for line in status_output.split("\n"):
                if line.strip():
                    status_code = line[:2]
                    filename = line[3:]

                    if status_code[0] in ["M", "A", "D", "R", "C"]:
                        staged_files.append(filename)
                    if status_code[1] in ["M", "D"]:
                        modified_files.append(filename)
                    if status_code == "??":
                        untracked_files.append(filename)

            result.metadata["files"] = {
                "staged": len(staged_files),
                "modified": len(modified_files),
                "untracked": len(untracked_files),
            }

            return True

        except Exception as e:
            result.add_error(f"Status check failed: {str(e)}")
            return False

    async def _handle_branch(
        self, project_dir: str, result: UtilityResult, context: Dict[str, Any]
    ) -> bool:
        """Handle Git branch operations."""
        try:
            branch_operation = context.get(
                "branch_operation", "list"
            )  # list, create, switch, delete
            branch_name = context.get("branch_name")

            if branch_operation == "list":
                branches_output = await self._run_git_command(
                    ["git", "branch", "-a"], project_dir
                )
                result.output["branches"] = branches_output

            elif branch_operation == "create" and branch_name:
                create_output = await self._run_git_command(
                    ["git", "branch", branch_name], project_dir
                )
                result.output["branch_create"] = create_output

            elif branch_operation == "switch" and branch_name:
                switch_output = await self._run_git_command(
                    ["git", "checkout", branch_name], project_dir
                )
                result.output["branch_switch"] = switch_output

            elif branch_operation == "delete" and branch_name:
                delete_output = await self._run_git_command(
                    ["git", "branch", "-d", branch_name], project_dir
                )
                result.output["branch_delete"] = delete_output

            else:
                result.add_error(f"Invalid branch operation: {branch_operation}")
                return False

            return True

        except Exception as e:
            result.add_error(f"Branch operation failed: {str(e)}")
            return False

    async def _handle_push(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git push operation."""
        try:
            push_output = await self._run_git_command(["git", "push"], project_dir)
            result.output["push"] = push_output
            return True

        except Exception as e:
            result.add_error(f"Push failed: {str(e)}")
            return False

    async def _run_git_command(self, cmd: List[str], project_dir: str) -> str:
        """Run a Git command and return output."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            raise Exception(f"Git command failed: {' '.join(cmd)} - {error_msg}")

        return stdout.decode("utf-8")

    async def _generate_commit_message(
        self, diff_output: str, status_output: str
    ) -> str:
        """Generate intelligent commit message using Claude API."""
        try:
            max_diff_size = self.config.parameters.get("max_diff_size", 50000)
            style = self.config.parameters.get("commit_message_style", "conventional")

            # Truncate diff if too large
            if len(diff_output) > max_diff_size:
                diff_output = diff_output[:max_diff_size] + "\n[... diff truncated ...]"

            # Create prompt for commit message generation
            prompt = f"""
Generate a {style} commit message for the following changes.

Style guidelines:
- conventional: Use conventional commit format (type(scope): description)
- descriptive: Clear, descriptive message explaining what changed
- concise: Brief but informative message

Git status:
{status_output}

Git diff:
{diff_output}

Generate only the commit message, no additional text or explanation.
"""

            # Use Claude CLI to generate commit message
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(prompt)
                temp_file = f.name

            try:
                cmd = [
                    "claude",
                    "--model",
                    "claude-3-5-sonnet-20241022",
                    "--max-tokens",
                    "200",
                    "--temperature",
                    "0.1",
                    "--file",
                    temp_file,
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0 and stdout:
                    commit_message = stdout.decode("utf-8").strip()
                    # Clean up any unwanted formatting
                    commit_message = commit_message.replace('"', "").replace("\n", " ")
                    return commit_message
                else:
                    # Fallback to simple message
                    return self._generate_fallback_commit_message(status_output)

            finally:
                try:
                    Path(temp_file).unlink()
                except:
                    pass

        except Exception:
            # Fallback to simple message generation
            return self._generate_fallback_commit_message(status_output)

    def _generate_fallback_commit_message(self, status_output: str) -> str:
        """Generate fallback commit message without API."""
        lines = [line for line in status_output.split("\n") if line.strip()]

        if not lines:
            return "Update project files"

        # Count different types of changes
        added = len([line for line in lines if line.startswith("A")])
        modified = len(
            [line for line in lines if line.startswith("M") or line.startswith(" M")]
        )
        deleted = len([line for line in lines if line.startswith("D")])

        # Generate message based on changes
        if added and not modified and not deleted:
            return f"Add {added} new file{'s' if added > 1 else ''}"
        elif modified and not added and not deleted:
            return f"Update {modified} file{'s' if modified > 1 else ''}"
        elif deleted and not added and not modified:
            return f"Remove {deleted} file{'s' if deleted > 1 else ''}"
        else:
            total = added + modified + deleted
            return f"Update project: {total} file{'s' if total > 1 else ''} changed"

    def validate_config(self) -> List[str]:
        """Validate Git manager configuration."""
        errors = []

        style = self.config.parameters.get("commit_message_style")
        if style and style not in ["conventional", "descriptive", "concise"]:
            errors.append(f"Unsupported commit message style: {style}")

        branch_strategy = self.config.parameters.get("branch_strategy")
        if branch_strategy and branch_strategy not in [
            "feature",
            "hotfix",
            "release",
            "main",
        ]:
            errors.append(f"Unsupported branch strategy: {branch_strategy}")

        return errors


class BuildUtility(CommandUtility):
    """Utility for building projects."""

    def __init__(self, config: UtilityConfig):
        command = config.parameters.get("command", "uv build")
        super().__init__(config, command, shell=True)

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Build project artifacts",
            parameters={
                "command": "uv build",
                "output_dir": "dist/",
                "clean_first": True,
            },
            timeout_seconds=300,
        )

    def validate_config(self) -> List[str]:
        """Validate build utility configuration."""
        errors = []

        if not self.config.parameters.get("command"):
            errors.append("Build command is required")

        return errors


class ArchivistUtility(BaseUtility):
    """Utility for content summarization using direct API calls."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Summarize and archive project content using Claude API",
            parameters={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "temperature": 0.1,
                "include_patterns": [
                    "*.py",
                    "*.md",
                    "*.txt",
                    "*.json",
                    "*.yaml",
                    "*.yml",
                ],
                "exclude_patterns": [
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    "node_modules",
                    "venv",
                    ".env",
                ],
                "summary_types": [
                    "code_overview",
                    "documentation",
                    "changes",
                    "architecture",
                ],
                "chunk_size": 100000,  # characters per chunk
            },
            timeout_seconds=300,
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute content summarization."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            summary_types = self.config.parameters.get(
                "summary_types", ["code_overview"]
            )

            # Collect project content
            content = await self._collect_project_content(project_dir)

            if not content:
                result.add_warning("No content found to summarize")
                result.set_completed(True)
                return result

            # Generate summaries for each requested type
            summaries = {}

            for summary_type in summary_types:
                try:
                    summary = await self._generate_summary(content, summary_type)
                    summaries[summary_type] = summary
                except Exception as e:
                    result.add_error(
                        f"Failed to generate {summary_type} summary: {str(e)}"
                    )

            result.output["summaries"] = summaries
            result.metadata["content_size"] = len(str(content))
            result.metadata["summary_count"] = len(summaries)

            # Store summaries as artifacts
            await self._store_summaries(summaries, project_dir, result)

            result.set_completed(len(summaries) > 0)

        except Exception as e:
            result.add_error(f"Content summarization failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _collect_project_content(self, project_dir: str) -> Dict[str, Any]:
        """Collect relevant project content."""
        project_path = Path(project_dir)
        include_patterns = self.config.parameters.get("include_patterns", ["*.py"])
        exclude_patterns = self.config.parameters.get("exclude_patterns", [])

        content = {
            "files": {},
            "structure": [],
            "metadata": {
                "project_name": project_path.name,
                "total_files": 0,
                "total_size": 0,
            },
        }

        def should_include(file_path: Path) -> bool:
            """Check if file should be included."""
            # Check exclude patterns first
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    return False

            # Check include patterns
            for pattern in include_patterns:
                if file_path.match(pattern):
                    return True

            return False

        # Collect file content and structure
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and should_include(file_path):
                try:
                    relative_path = file_path.relative_to(project_path)

                    # Read file content
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()

                    content["files"][str(relative_path)] = {
                        "content": file_content,
                        "size": len(file_content),
                        "lines": len(file_content.splitlines()),
                    }

                    content["structure"].append(
                        {
                            "path": str(relative_path),
                            "size": len(file_content),
                            "type": file_path.suffix,
                        }
                    )

                    content["metadata"]["total_files"] += 1
                    content["metadata"]["total_size"] += len(file_content)

                except Exception:
                    # Skip files that can't be read
                    continue

        return content

    async def _generate_summary(
        self, content: Dict[str, Any], summary_type: str
    ) -> str:
        """Generate summary using Claude API via CLI."""
        model = self.config.parameters.get("model", "claude-3-5-sonnet-20241022")
        max_tokens = self.config.parameters.get("max_tokens", 4000)
        temperature = self.config.parameters.get("temperature", 0.1)

        # Create prompt based on summary type
        prompts = {
            "code_overview": """
Analyze this codebase and provide a comprehensive code overview. Include:
1. Main components and their purposes
2. Architecture patterns used
3. Key classes and functions
4. Dependencies and integrations
5. Code quality observations
6. Suggested improvements

Be concise but thorough. Focus on the most important aspects.
""",
            "documentation": """
Generate comprehensive documentation for this codebase. Include:
1. Project purpose and overview
2. Setup and installation instructions
3. Usage examples
4. API documentation for key components
5. Configuration options
6. Troubleshooting guide

Structure it as proper documentation with clear sections.
""",
            "changes": """
Analyze this codebase and summarize recent changes and evolution. Include:
1. Major architectural changes
2. New features added
3. Improvements and optimizations
4. Bug fixes and stability improvements
5. Deprecated or removed functionality
6. Migration notes if applicable

Focus on what has changed and why.
""",
            "architecture": """
Provide a detailed architectural analysis of this codebase. Include:
1. Overall system architecture
2. Component relationships and data flow
3. Design patterns employed
4. Scalability considerations
5. Security architecture
6. Performance characteristics
7. Areas for architectural improvement

Be technical and specific about architectural decisions.
""",
        }

        prompt = prompts.get(summary_type, prompts["code_overview"])

        # Prepare content for API
        content_text = self._format_content_for_api(content)

        # Create temporary file with content
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{prompt}\n\n--- PROJECT CONTENT ---\n\n{content_text}")
            temp_file = f.name

        try:
            # Use Claude CLI to generate summary
            cmd = [
                "claude",
                "--model",
                model,
                "--max-tokens",
                str(max_tokens),
                "--temperature",
                str(temperature),
                "--file",
                temp_file,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0 and stdout:
                summary = stdout.decode("utf-8").strip()
                return summary
            else:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise Exception(f"Claude API call failed: {error_msg}")

        finally:
            # Clean up temporary file
            try:
                Path(temp_file).unlink()
            except:
                pass

    def _format_content_for_api(self, content: Dict[str, Any]) -> str:
        """Format content for API consumption."""
        chunk_size = self.config.parameters.get("chunk_size", 100000)

        formatted_parts = []

        # Add project metadata
        metadata = content.get("metadata", {})
        formatted_parts.append(f"PROJECT: {metadata.get('project_name', 'Unknown')}")
        formatted_parts.append(f"Files: {metadata.get('total_files', 0)}")
        formatted_parts.append(
            f"Total Size: {metadata.get('total_size', 0)} characters"
        )
        formatted_parts.append("")

        # Add project structure
        structure = content.get("structure", [])
        if structure:
            formatted_parts.append("PROJECT STRUCTURE:")
            for item in structure[:50]:  # Limit structure items
                formatted_parts.append(f"  {item['path']} ({item['size']} chars)")
            formatted_parts.append("")

        # Add file contents (chunked if necessary)
        files = content.get("files", {})
        current_size = len("\n".join(formatted_parts))

        formatted_parts.append("FILE CONTENTS:")
        for file_path, file_info in files.items():
            file_content = file_info["content"]

            # Check if adding this file would exceed chunk size
            if current_size + len(file_content) > chunk_size:
                formatted_parts.append(
                    "\n[Content truncated - too large for single API call]"
                )
                break

            formatted_parts.append(f"\n--- {file_path} ---")
            formatted_parts.append(file_content)
            current_size += len(file_content) + len(file_path) + 10

        return "\n".join(formatted_parts)

    async def _store_summaries(
        self, summaries: Dict[str, str], project_dir: str, result: UtilityResult
    ):
        """Store generated summaries as artifacts."""
        project_path = Path(project_dir)
        summaries_dir = project_path / ".apex" / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)

        for summary_type, summary_content in summaries.items():
            summary_file = summaries_dir / f"{summary_type}_summary.md"

            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"# {summary_type.replace('_', ' ').title()} Summary\n\n")
                f.write("Generated by APEX Archivist Utility\n")
                f.write(f"Date: {result.started_at}\n\n")
                f.write("---\n\n")
                f.write(summary_content)

            result.add_artifact(str(summary_file))

    def validate_config(self) -> List[str]:
        """Validate archivist utility configuration."""
        errors = []

        model = self.config.parameters.get("model")
        if model and not model.startswith("claude-"):
            errors.append(f"Unsupported model: {model}")

        summary_types = self.config.parameters.get("summary_types", [])
        valid_types = ["code_overview", "documentation", "changes", "architecture"]

        for summary_type in summary_types:
            if summary_type not in valid_types:
                errors.append(f"Unsupported summary type: {summary_type}")

        max_tokens = self.config.parameters.get("max_tokens", 4000)
        if max_tokens > 8192:
            errors.append("max_tokens cannot exceed 8192")

        return errors


class GitManagerUtility(BaseUtility):
    """Utility for intelligent Git operations and commit generation."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Intelligent Git operations with AI-generated commit messages",
            parameters={
                "auto_stage": True,
                "generate_commit_message": True,
                "commit_message_style": "conventional",  # conventional, descriptive, concise
                "max_diff_size": 50000,  # characters
                "include_file_changes": True,
                "branch_strategy": "feature",  # feature, hotfix, release
                "push_after_commit": False,
            },
            timeout_seconds=120,
            required_tools=["git"],
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute Git operations."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            operation = context.get(
                "operation", "commit"
            )  # commit, status, branch, push

            # Check if we're in a Git repository
            if not await self._is_git_repo(project_dir):
                result.add_error("Not a Git repository")
                result.set_completed(False)
                return result

            if operation == "commit":
                success = await self._handle_commit(project_dir, result)
            elif operation == "status":
                success = await self._handle_status(project_dir, result)
            elif operation == "branch":
                success = await self._handle_branch(project_dir, result, context)
            elif operation == "push":
                success = await self._handle_push(project_dir, result)
            else:
                result.add_error(f"Unsupported Git operation: {operation}")
                success = False

            result.set_completed(success)

        except Exception as e:
            result.add_error(f"Git operation failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _is_git_repo(self, project_dir: str) -> bool:
        """Check if directory is a Git repository."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "--git-dir",
                cwd=project_dir,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False

    async def _handle_commit(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git commit with intelligent message generation."""
        try:
            # Get current status
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )

            if not status_output.strip():
                result.add_warning("No changes to commit")
                return True

            # Stage files if auto_stage is enabled
            if self.config.parameters.get("auto_stage", True):
                await self._run_git_command(["git", "add", "."], project_dir)

            # Get diff for commit message generation
            diff_output = await self._run_git_command(
                ["git", "diff", "--cached"], project_dir
            )

            if not diff_output.strip():
                result.add_warning("No staged changes to commit")
                return True

            # Generate commit message
            commit_message = await self._generate_commit_message(
                diff_output, status_output
            )

            # Commit changes
            commit_output = await self._run_git_command(
                ["git", "commit", "-m", commit_message], project_dir
            )

            result.output["commit"] = {
                "message": commit_message,
                "output": commit_output,
                "files_changed": len(
                    [line for line in status_output.split("\n") if line.strip()]
                ),
            }

            # Get commit hash
            commit_hash = await self._run_git_command(
                ["git", "rev-parse", "HEAD"], project_dir
            )
            result.metadata["commit_hash"] = commit_hash.strip()

            # Push if configured
            if self.config.parameters.get("push_after_commit", False):
                push_output = await self._run_git_command(["git", "push"], project_dir)
                result.output["push"] = push_output

            return True

        except Exception as e:
            result.add_error(f"Commit failed: {str(e)}")
            return False

    async def _handle_status(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git status check."""
        try:
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )
            branch_output = await self._run_git_command(
                ["git", "branch", "--show-current"], project_dir
            )

            result.output["status"] = {
                "porcelain": status_output,
                "current_branch": branch_output.strip(),
                "clean": not status_output.strip(),
            }

            # Parse status
            modified_files = []
            staged_files = []
            untracked_files = []

            for line in status_output.split("\n"):
                if line.strip():
                    status_code = line[:2]
                    filename = line[3:]

                    if status_code[0] in ["M", "A", "D", "R", "C"]:
                        staged_files.append(filename)
                    if status_code[1] in ["M", "D"]:
                        modified_files.append(filename)
                    if status_code == "??":
                        untracked_files.append(filename)

            result.metadata["files"] = {
                "staged": len(staged_files),
                "modified": len(modified_files),
                "untracked": len(untracked_files),
            }

            return True

        except Exception as e:
            result.add_error(f"Status check failed: {str(e)}")
            return False

    async def _handle_branch(
        self, project_dir: str, result: UtilityResult, context: Dict[str, Any]
    ) -> bool:
        """Handle Git branch operations."""
        try:
            branch_operation = context.get(
                "branch_operation", "list"
            )  # list, create, switch, delete
            branch_name = context.get("branch_name")

            if branch_operation == "list":
                branches_output = await self._run_git_command(
                    ["git", "branch", "-a"], project_dir
                )
                result.output["branches"] = branches_output

            elif branch_operation == "create" and branch_name:
                create_output = await self._run_git_command(
                    ["git", "branch", branch_name], project_dir
                )
                result.output["branch_create"] = create_output

            elif branch_operation == "switch" and branch_name:
                switch_output = await self._run_git_command(
                    ["git", "checkout", branch_name], project_dir
                )
                result.output["branch_switch"] = switch_output

            elif branch_operation == "delete" and branch_name:
                delete_output = await self._run_git_command(
                    ["git", "branch", "-d", branch_name], project_dir
                )
                result.output["branch_delete"] = delete_output

            else:
                result.add_error(f"Invalid branch operation: {branch_operation}")
                return False

            return True

        except Exception as e:
            result.add_error(f"Branch operation failed: {str(e)}")
            return False

    async def _handle_push(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git push operation."""
        try:
            push_output = await self._run_git_command(["git", "push"], project_dir)
            result.output["push"] = push_output
            return True

        except Exception as e:
            result.add_error(f"Push failed: {str(e)}")
            return False

    async def _run_git_command(self, cmd: List[str], project_dir: str) -> str:
        """Run a Git command and return output."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            raise Exception(f"Git command failed: {' '.join(cmd)} - {error_msg}")

        return stdout.decode("utf-8")

    async def _generate_commit_message(
        self, diff_output: str, status_output: str
    ) -> str:
        """Generate intelligent commit message using Claude API."""
        try:
            max_diff_size = self.config.parameters.get("max_diff_size", 50000)
            style = self.config.parameters.get("commit_message_style", "conventional")

            # Truncate diff if too large
            if len(diff_output) > max_diff_size:
                diff_output = diff_output[:max_diff_size] + "\n[... diff truncated ...]"

            # Create prompt for commit message generation
            prompt = f"""
Generate a {style} commit message for the following changes.

Style guidelines:
- conventional: Use conventional commit format (type(scope): description)
- descriptive: Clear, descriptive message explaining what changed
- concise: Brief but informative message

Git status:
{status_output}

Git diff:
{diff_output}

Generate only the commit message, no additional text or explanation.
"""

            # Use Claude CLI to generate commit message
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(prompt)
                temp_file = f.name

            try:
                cmd = [
                    "claude",
                    "--model",
                    "claude-3-5-sonnet-20241022",
                    "--max-tokens",
                    "200",
                    "--temperature",
                    "0.1",
                    "--file",
                    temp_file,
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0 and stdout:
                    commit_message = stdout.decode("utf-8").strip()
                    # Clean up any unwanted formatting
                    commit_message = commit_message.replace('"', "").replace("\n", " ")
                    return commit_message
                else:
                    # Fallback to simple message
                    return self._generate_fallback_commit_message(status_output)

            finally:
                try:
                    Path(temp_file).unlink()
                except:
                    pass

        except Exception:
            # Fallback to simple message generation
            return self._generate_fallback_commit_message(status_output)

    def _generate_fallback_commit_message(self, status_output: str) -> str:
        """Generate fallback commit message without API."""
        lines = [line for line in status_output.split("\n") if line.strip()]

        if not lines:
            return "Update project files"

        # Count different types of changes
        added = len([line for line in lines if line.startswith("A")])
        modified = len(
            [line for line in lines if line.startswith("M") or line.startswith(" M")]
        )
        deleted = len([line for line in lines if line.startswith("D")])

        # Generate message based on changes
        if added and not modified and not deleted:
            return f"Add {added} new file{'s' if added > 1 else ''}"
        elif modified and not added and not deleted:
            return f"Update {modified} file{'s' if modified > 1 else ''}"
        elif deleted and not added and not modified:
            return f"Remove {deleted} file{'s' if deleted > 1 else ''}"
        else:
            total = added + modified + deleted
            return f"Update project: {total} file{'s' if total > 1 else ''} changed"

    def validate_config(self) -> List[str]:
        """Validate Git manager configuration."""
        errors = []

        style = self.config.parameters.get("commit_message_style")
        if style and style not in ["conventional", "descriptive", "concise"]:
            errors.append(f"Unsupported commit message style: {style}")

        branch_strategy = self.config.parameters.get("branch_strategy")
        if branch_strategy and branch_strategy not in [
            "feature",
            "hotfix",
            "release",
            "main",
        ]:
            errors.append(f"Unsupported branch strategy: {branch_strategy}")

        return errors


class DeploymentUtility(BaseUtility):
    """Utility for deployment operations."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Deploy project to target environment",
            parameters={
                "target": "staging",
                "strategy": "blue_green",
                "health_check": True,
                "rollback_on_failure": True,
            },
            timeout_seconds=600,
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute deployment."""
        result = self.create_result()

        try:
            target = self.config.parameters.get("target", "staging")
            strategy = self.config.parameters.get("strategy", "direct")

            # This is a simplified deployment simulation
            result.output["deployment"] = {
                "target": target,
                "strategy": strategy,
                "status": "simulated",
                "message": "Deployment simulation completed",
            }

            # In a real implementation, this would:
            # 1. Build artifacts
            # 2. Run pre-deployment tests
            # 3. Deploy to target environment
            # 4. Run health checks
            # 5. Handle rollback if needed

            result.metadata["deployed_to"] = target
            result.set_completed(True)

        except Exception as e:
            result.add_error(f"Deployment failed: {str(e)}")
            result.set_completed(False)

        return result

    def validate_config(self) -> List[str]:
        """Validate deployment utility configuration."""
        errors = []

        target = self.config.parameters.get("target")
        if not target:
            errors.append("Deployment target is required")

        strategy = self.config.parameters.get("strategy")
        if strategy and strategy not in ["direct", "blue_green", "canary"]:
            errors.append(f"Unsupported deployment strategy: {strategy}")

        return errors


class ArchivistUtility(BaseUtility):
    """Utility for content summarization using direct API calls."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Summarize and archive project content using Claude API",
            parameters={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000,
                "temperature": 0.1,
                "include_patterns": [
                    "*.py",
                    "*.md",
                    "*.txt",
                    "*.json",
                    "*.yaml",
                    "*.yml",
                ],
                "exclude_patterns": [
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    "node_modules",
                    "venv",
                    ".env",
                ],
                "summary_types": [
                    "code_overview",
                    "documentation",
                    "changes",
                    "architecture",
                ],
                "chunk_size": 100000,  # characters per chunk
            },
            timeout_seconds=300,
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute content summarization."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            summary_types = self.config.parameters.get(
                "summary_types", ["code_overview"]
            )

            # Collect project content
            content = await self._collect_project_content(project_dir)

            if not content:
                result.add_warning("No content found to summarize")
                result.set_completed(True)
                return result

            # Generate summaries for each requested type
            summaries = {}

            for summary_type in summary_types:
                try:
                    summary = await self._generate_summary(content, summary_type)
                    summaries[summary_type] = summary
                except Exception as e:
                    result.add_error(
                        f"Failed to generate {summary_type} summary: {str(e)}"
                    )

            result.output["summaries"] = summaries
            result.metadata["content_size"] = len(str(content))
            result.metadata["summary_count"] = len(summaries)

            # Store summaries as artifacts
            await self._store_summaries(summaries, project_dir, result)

            result.set_completed(len(summaries) > 0)

        except Exception as e:
            result.add_error(f"Content summarization failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _collect_project_content(self, project_dir: str) -> Dict[str, Any]:
        """Collect relevant project content."""
        project_path = Path(project_dir)
        include_patterns = self.config.parameters.get("include_patterns", ["*.py"])
        exclude_patterns = self.config.parameters.get("exclude_patterns", [])

        content = {
            "files": {},
            "structure": [],
            "metadata": {
                "project_name": project_path.name,
                "total_files": 0,
                "total_size": 0,
            },
        }

        def should_include(file_path: Path) -> bool:
            """Check if file should be included."""
            # Check exclude patterns first
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    return False

            # Check include patterns
            for pattern in include_patterns:
                if file_path.match(pattern):
                    return True

            return False

        # Collect file content and structure
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and should_include(file_path):
                try:
                    relative_path = file_path.relative_to(project_path)

                    # Read file content
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()

                    content["files"][str(relative_path)] = {
                        "content": file_content,
                        "size": len(file_content),
                        "lines": len(file_content.splitlines()),
                    }

                    content["structure"].append(
                        {
                            "path": str(relative_path),
                            "size": len(file_content),
                            "type": file_path.suffix,
                        }
                    )

                    content["metadata"]["total_files"] += 1
                    content["metadata"]["total_size"] += len(file_content)

                except Exception:
                    # Skip files that can't be read
                    continue

        return content

    async def _generate_summary(
        self, content: Dict[str, Any], summary_type: str
    ) -> str:
        """Generate summary using Claude API via CLI."""
        model = self.config.parameters.get("model", "claude-3-5-sonnet-20241022")
        max_tokens = self.config.parameters.get("max_tokens", 4000)
        temperature = self.config.parameters.get("temperature", 0.1)

        # Create prompt based on summary type
        prompts = {
            "code_overview": """
Analyze this codebase and provide a comprehensive code overview. Include:
1. Main components and their purposes
2. Architecture patterns used
3. Key classes and functions
4. Dependencies and integrations
5. Code quality observations
6. Suggested improvements

Be concise but thorough. Focus on the most important aspects.
""",
            "documentation": """
Generate comprehensive documentation for this codebase. Include:
1. Project purpose and overview
2. Setup and installation instructions
3. Usage examples
4. API documentation for key components
5. Configuration options
6. Troubleshooting guide

Structure it as proper documentation with clear sections.
""",
            "changes": """
Analyze this codebase and summarize recent changes and evolution. Include:
1. Major architectural changes
2. New features added
3. Improvements and optimizations
4. Bug fixes and stability improvements
5. Deprecated or removed functionality
6. Migration notes if applicable

Focus on what has changed and why.
""",
            "architecture": """
Provide a detailed architectural analysis of this codebase. Include:
1. Overall system architecture
2. Component relationships and data flow
3. Design patterns employed
4. Scalability considerations
5. Security architecture
6. Performance characteristics
7. Areas for architectural improvement

Be technical and specific about architectural decisions.
""",
        }

        prompt = prompts.get(summary_type, prompts["code_overview"])

        # Prepare content for API
        content_text = self._format_content_for_api(content)

        # Create temporary file with content
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{prompt}\n\n--- PROJECT CONTENT ---\n\n{content_text}")
            temp_file = f.name

        try:
            # Use Claude CLI to generate summary
            cmd = [
                "claude",
                "--model",
                model,
                "--max-tokens",
                str(max_tokens),
                "--temperature",
                str(temperature),
                "--file",
                temp_file,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0 and stdout:
                summary = stdout.decode("utf-8").strip()
                return summary
            else:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise Exception(f"Claude API call failed: {error_msg}")

        finally:
            # Clean up temporary file
            try:
                Path(temp_file).unlink()
            except:
                pass

    def _format_content_for_api(self, content: Dict[str, Any]) -> str:
        """Format content for API consumption."""
        chunk_size = self.config.parameters.get("chunk_size", 100000)

        formatted_parts = []

        # Add project metadata
        metadata = content.get("metadata", {})
        formatted_parts.append(f"PROJECT: {metadata.get('project_name', 'Unknown')}")
        formatted_parts.append(f"Files: {metadata.get('total_files', 0)}")
        formatted_parts.append(
            f"Total Size: {metadata.get('total_size', 0)} characters"
        )
        formatted_parts.append("")

        # Add project structure
        structure = content.get("structure", [])
        if structure:
            formatted_parts.append("PROJECT STRUCTURE:")
            for item in structure[:50]:  # Limit structure items
                formatted_parts.append(f"  {item['path']} ({item['size']} chars)")
            formatted_parts.append("")

        # Add file contents (chunked if necessary)
        files = content.get("files", {})
        current_size = len("\n".join(formatted_parts))

        formatted_parts.append("FILE CONTENTS:")
        for file_path, file_info in files.items():
            file_content = file_info["content"]

            # Check if adding this file would exceed chunk size
            if current_size + len(file_content) > chunk_size:
                formatted_parts.append(
                    "\n[Content truncated - too large for single API call]"
                )
                break

            formatted_parts.append(f"\n--- {file_path} ---")
            formatted_parts.append(file_content)
            current_size += len(file_content) + len(file_path) + 10

        return "\n".join(formatted_parts)

    async def _store_summaries(
        self, summaries: Dict[str, str], project_dir: str, result: UtilityResult
    ):
        """Store generated summaries as artifacts."""
        project_path = Path(project_dir)
        summaries_dir = project_path / ".apex" / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)

        for summary_type, summary_content in summaries.items():
            summary_file = summaries_dir / f"{summary_type}_summary.md"

            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"# {summary_type.replace('_', ' ').title()} Summary\n\n")
                f.write("Generated by APEX Archivist Utility\n")
                f.write(f"Date: {result.started_at}\n\n")
                f.write("---\n\n")
                f.write(summary_content)

            result.add_artifact(str(summary_file))

    def validate_config(self) -> List[str]:
        """Validate archivist utility configuration."""
        errors = []

        model = self.config.parameters.get("model")
        if model and not model.startswith("claude-"):
            errors.append(f"Unsupported model: {model}")

        summary_types = self.config.parameters.get("summary_types", [])
        valid_types = ["code_overview", "documentation", "changes", "architecture"]

        for summary_type in summary_types:
            if summary_type not in valid_types:
                errors.append(f"Unsupported summary type: {summary_type}")

        max_tokens = self.config.parameters.get("max_tokens", 4000)
        if max_tokens > 8192:
            errors.append("max_tokens cannot exceed 8192")

        return errors


class GitManagerUtility(BaseUtility):
    """Utility for intelligent Git operations and commit generation."""

    @classmethod
    def get_default_config(cls, name: str, category: UtilityCategory) -> UtilityConfig:
        return UtilityConfig(
            name=name,
            category=category,
            description="Intelligent Git operations with AI-generated commit messages",
            parameters={
                "auto_stage": True,
                "generate_commit_message": True,
                "commit_message_style": "conventional",  # conventional, descriptive, concise
                "max_diff_size": 50000,  # characters
                "include_file_changes": True,
                "branch_strategy": "feature",  # feature, hotfix, release
                "push_after_commit": False,
            },
            timeout_seconds=120,
            required_tools=["git"],
        )

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute Git operations."""
        result = self.create_result()

        try:
            project_dir = context.get("project_dir", ".")
            operation = context.get(
                "operation", "commit"
            )  # commit, status, branch, push

            # Check if we're in a Git repository
            if not await self._is_git_repo(project_dir):
                result.add_error("Not a Git repository")
                result.set_completed(False)
                return result

            if operation == "commit":
                success = await self._handle_commit(project_dir, result)
            elif operation == "status":
                success = await self._handle_status(project_dir, result)
            elif operation == "branch":
                success = await self._handle_branch(project_dir, result, context)
            elif operation == "push":
                success = await self._handle_push(project_dir, result)
            else:
                result.add_error(f"Unsupported Git operation: {operation}")
                success = False

            result.set_completed(success)

        except Exception as e:
            result.add_error(f"Git operation failed: {str(e)}")
            result.set_completed(False)

        return result

    async def _is_git_repo(self, project_dir: str) -> bool:
        """Check if directory is a Git repository."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "--git-dir",
                cwd=project_dir,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False

    async def _handle_commit(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git commit with intelligent message generation."""
        try:
            # Get current status
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )

            if not status_output.strip():
                result.add_warning("No changes to commit")
                return True

            # Stage files if auto_stage is enabled
            if self.config.parameters.get("auto_stage", True):
                await self._run_git_command(["git", "add", "."], project_dir)

            # Get diff for commit message generation
            diff_output = await self._run_git_command(
                ["git", "diff", "--cached"], project_dir
            )

            if not diff_output.strip():
                result.add_warning("No staged changes to commit")
                return True

            # Generate commit message
            commit_message = await self._generate_commit_message(
                diff_output, status_output
            )

            # Commit changes
            commit_output = await self._run_git_command(
                ["git", "commit", "-m", commit_message], project_dir
            )

            result.output["commit"] = {
                "message": commit_message,
                "output": commit_output,
                "files_changed": len(
                    [line for line in status_output.split("\n") if line.strip()]
                ),
            }

            # Get commit hash
            commit_hash = await self._run_git_command(
                ["git", "rev-parse", "HEAD"], project_dir
            )
            result.metadata["commit_hash"] = commit_hash.strip()

            # Push if configured
            if self.config.parameters.get("push_after_commit", False):
                push_output = await self._run_git_command(["git", "push"], project_dir)
                result.output["push"] = push_output

            return True

        except Exception as e:
            result.add_error(f"Commit failed: {str(e)}")
            return False

    async def _handle_status(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git status check."""
        try:
            status_output = await self._run_git_command(
                ["git", "status", "--porcelain"], project_dir
            )
            branch_output = await self._run_git_command(
                ["git", "branch", "--show-current"], project_dir
            )

            result.output["status"] = {
                "porcelain": status_output,
                "current_branch": branch_output.strip(),
                "clean": not status_output.strip(),
            }

            # Parse status
            modified_files = []
            staged_files = []
            untracked_files = []

            for line in status_output.split("\n"):
                if line.strip():
                    status_code = line[:2]
                    filename = line[3:]

                    if status_code[0] in ["M", "A", "D", "R", "C"]:
                        staged_files.append(filename)
                    if status_code[1] in ["M", "D"]:
                        modified_files.append(filename)
                    if status_code == "??":
                        untracked_files.append(filename)

            result.metadata["files"] = {
                "staged": len(staged_files),
                "modified": len(modified_files),
                "untracked": len(untracked_files),
            }

            return True

        except Exception as e:
            result.add_error(f"Status check failed: {str(e)}")
            return False

    async def _handle_branch(
        self, project_dir: str, result: UtilityResult, context: Dict[str, Any]
    ) -> bool:
        """Handle Git branch operations."""
        try:
            branch_operation = context.get(
                "branch_operation", "list"
            )  # list, create, switch, delete
            branch_name = context.get("branch_name")

            if branch_operation == "list":
                branches_output = await self._run_git_command(
                    ["git", "branch", "-a"], project_dir
                )
                result.output["branches"] = branches_output

            elif branch_operation == "create" and branch_name:
                create_output = await self._run_git_command(
                    ["git", "branch", branch_name], project_dir
                )
                result.output["branch_create"] = create_output

            elif branch_operation == "switch" and branch_name:
                switch_output = await self._run_git_command(
                    ["git", "checkout", branch_name], project_dir
                )
                result.output["branch_switch"] = switch_output

            elif branch_operation == "delete" and branch_name:
                delete_output = await self._run_git_command(
                    ["git", "branch", "-d", branch_name], project_dir
                )
                result.output["branch_delete"] = delete_output

            else:
                result.add_error(f"Invalid branch operation: {branch_operation}")
                return False

            return True

        except Exception as e:
            result.add_error(f"Branch operation failed: {str(e)}")
            return False

    async def _handle_push(self, project_dir: str, result: UtilityResult) -> bool:
        """Handle Git push operation."""
        try:
            push_output = await self._run_git_command(["git", "push"], project_dir)
            result.output["push"] = push_output
            return True

        except Exception as e:
            result.add_error(f"Push failed: {str(e)}")
            return False

    async def _run_git_command(self, cmd: List[str], project_dir: str) -> str:
        """Run a Git command and return output."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            raise Exception(f"Git command failed: {' '.join(cmd)} - {error_msg}")

        return stdout.decode("utf-8")

    async def _generate_commit_message(
        self, diff_output: str, status_output: str
    ) -> str:
        """Generate intelligent commit message using Claude API."""
        try:
            max_diff_size = self.config.parameters.get("max_diff_size", 50000)
            style = self.config.parameters.get("commit_message_style", "conventional")

            # Truncate diff if too large
            if len(diff_output) > max_diff_size:
                diff_output = diff_output[:max_diff_size] + "\n[... diff truncated ...]"

            # Create prompt for commit message generation
            prompt = f"""
Generate a {style} commit message for the following changes.

Style guidelines:
- conventional: Use conventional commit format (type(scope): description)
- descriptive: Clear, descriptive message explaining what changed
- concise: Brief but informative message

Git status:
{status_output}

Git diff:
{diff_output}

Generate only the commit message, no additional text or explanation.
"""

            # Use Claude CLI to generate commit message
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(prompt)
                temp_file = f.name

            try:
                cmd = [
                    "claude",
                    "--model",
                    "claude-3-5-sonnet-20241022",
                    "--max-tokens",
                    "200",
                    "--temperature",
                    "0.1",
                    "--file",
                    temp_file,
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0 and stdout:
                    commit_message = stdout.decode("utf-8").strip()
                    # Clean up any unwanted formatting
                    commit_message = commit_message.replace('"', "").replace("\n", " ")
                    return commit_message
                else:
                    # Fallback to simple message
                    return self._generate_fallback_commit_message(status_output)

            finally:
                try:
                    Path(temp_file).unlink()
                except:
                    pass

        except Exception:
            # Fallback to simple message generation
            return self._generate_fallback_commit_message(status_output)

    def _generate_fallback_commit_message(self, status_output: str) -> str:
        """Generate fallback commit message without API."""
        lines = [line for line in status_output.split("\n") if line.strip()]

        if not lines:
            return "Update project files"

        # Count different types of changes
        added = len([line for line in lines if line.startswith("A")])
        modified = len(
            [line for line in lines if line.startswith("M") or line.startswith(" M")]
        )
        deleted = len([line for line in lines if line.startswith("D")])

        # Generate message based on changes
        if added and not modified and not deleted:
            return f"Add {added} new file{'s' if added > 1 else ''}"
        elif modified and not added and not deleted:
            return f"Update {modified} file{'s' if modified > 1 else ''}"
        elif deleted and not added and not modified:
            return f"Remove {deleted} file{'s' if deleted > 1 else ''}"
        else:
            total = added + modified + deleted
            return f"Update project: {total} file{'s' if total > 1 else ''} changed"

    def validate_config(self) -> List[str]:
        """Validate Git manager configuration."""
        errors = []

        style = self.config.parameters.get("commit_message_style")
        if style and style not in ["conventional", "descriptive", "concise"]:
            errors.append(f"Unsupported commit message style: {style}")

        branch_strategy = self.config.parameters.get("branch_strategy")
        if branch_strategy and branch_strategy not in [
            "feature",
            "hotfix",
            "release",
            "main",
        ]:
            errors.append(f"Unsupported branch strategy: {branch_strategy}")

        return errors
