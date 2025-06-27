"""Supervisor integration for automatic utility vs worker decision logic."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel

from apex.core.memory import MemoryPatterns
from apex.core.task_briefing import TaskBriefing, TaskRole
from apex.utilities.manager import UtilityManager
from apex.utilities.registry import UtilityRegistry


class TaskComplexity(Enum):
    """Task complexity levels for decision making."""

    SIMPLE = "simple"  # Deterministic operations
    MODERATE = "moderate"  # Some analysis required
    COMPLEX = "complex"  # Complex reasoning needed
    CREATIVE = "creative"  # Creative/innovative work


class DecisionRule(BaseModel):
    """Rule for deciding between utility and worker execution."""

    name: str
    description: str
    conditions: Dict[str, Any]
    preferred_execution: str  # "utility" or "worker"
    confidence: float  # 0.0 to 1.0
    priority: int = 0  # Higher priority rules take precedence


class SupervisorUtilityIntegrator:
    """Integrates utilities with supervisor decision making."""

    def __init__(self, memory: MemoryPatterns):
        self.memory = memory
        self.utility_manager = UtilityManager(memory)
        self.utility_registry = UtilityRegistry(memory)
        self.logger = logging.getLogger(__name__)

        # Decision rules
        self.decision_rules: List[DecisionRule] = []
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default decision rules."""
        self.decision_rules = [
            # Code linting - always use utilities
            DecisionRule(
                name="code_linting",
                description="Code linting and style checking",
                conditions={
                    "keywords": ["lint", "style", "format", "ruff", "black", "flake8"],
                    "task_type": ["code_quality", "validation"],
                },
                preferred_execution="utility",
                confidence=0.95,
                priority=10,
            ),
            # Testing - prefer utilities for standard testing
            DecisionRule(
                name="automated_testing",
                description="Running automated tests",
                conditions={
                    "keywords": ["test", "pytest", "unittest", "coverage"],
                    "task_type": ["testing", "validation"],
                },
                preferred_execution="utility",
                confidence=0.90,
                priority=9,
            ),
            # Building/compilation - use utilities
            DecisionRule(
                name="build_operations",
                description="Build and compilation tasks",
                conditions={
                    "keywords": ["build", "compile", "package", "dist", "wheel"],
                    "task_type": ["build", "deployment"],
                },
                preferred_execution="utility",
                confidence=0.95,
                priority=10,
            ),
            # Documentation generation - utilities for standard docs
            DecisionRule(
                name="documentation_generation",
                description="Standard documentation generation",
                conditions={
                    "keywords": ["docs", "documentation", "mkdocs", "sphinx"],
                    "task_type": ["documentation"],
                },
                preferred_execution="utility",
                confidence=0.85,
                priority=8,
            ),
            # Security scanning - always utilities
            DecisionRule(
                name="security_scanning",
                description="Security vulnerability scanning",
                conditions={
                    "keywords": ["security", "vulnerability", "bandit", "safety"],
                    "task_type": ["security", "analysis"],
                },
                preferred_execution="utility",
                confidence=0.95,
                priority=10,
            ),
            # Git operations - prefer utilities for standard ops
            DecisionRule(
                name="git_operations",
                description="Standard Git operations",
                conditions={
                    "keywords": ["commit", "push", "pull", "merge", "branch"],
                    "task_type": ["version_control"],
                },
                preferred_execution="utility",
                confidence=0.80,
                priority=7,
            ),
            # Content summarization - utilities
            DecisionRule(
                name="content_summarization",
                description="Content analysis and summarization",
                conditions={
                    "keywords": ["summarize", "analyze", "archive", "overview"],
                    "task_type": ["analysis", "documentation"],
                },
                preferred_execution="utility",
                confidence=0.75,
                priority=6,
            ),
            # Complex code implementation - workers
            DecisionRule(
                name="complex_implementation",
                description="Complex code implementation requiring reasoning",
                conditions={
                    "keywords": ["implement", "create", "design", "architecture"],
                    "task_type": ["implementation", "development"],
                    "complexity": ["complex", "creative"],
                },
                preferred_execution="worker",
                confidence=0.85,
                priority=8,
            ),
            # Bug fixing - workers for complex issues
            DecisionRule(
                name="bug_fixing",
                description="Bug investigation and fixing",
                conditions={
                    "keywords": ["bug", "fix", "error", "issue", "debug"],
                    "task_type": ["bug_fix", "debugging"],
                },
                preferred_execution="worker",
                confidence=0.80,
                priority=7,
            ),
            # Code review - workers
            DecisionRule(
                name="code_review",
                description="Code review and analysis",
                conditions={
                    "keywords": ["review", "analyze", "critique", "improve"],
                    "task_type": ["review", "analysis"],
                },
                preferred_execution="worker",
                confidence=0.75,
                priority=6,
            ),
            # Research tasks - workers
            DecisionRule(
                name="research_tasks",
                description="Research and investigation tasks",
                conditions={
                    "keywords": ["research", "investigate", "explore", "study"],
                    "task_type": ["research", "analysis"],
                },
                preferred_execution="worker",
                confidence=0.85,
                priority=8,
            ),
        ]

    async def decide_execution_method(
        self, task_briefing: TaskBriefing
    ) -> Dict[str, Any]:
        """Decide whether to use utility or worker for task execution."""
        try:
            # Analyze task characteristics
            task_analysis = await self._analyze_task(task_briefing)

            # Apply decision rules
            decision = await self._apply_decision_rules(task_analysis)

            # Get available utilities if utility execution is preferred
            available_utilities = []
            if decision["preferred_execution"] == "utility":
                available_utilities = await self._find_matching_utilities(task_analysis)

            result = {
                "task_id": task_briefing.task_id,
                "preferred_execution": decision["preferred_execution"],
                "confidence": decision["confidence"],
                "reasoning": decision["reasoning"],
                "matched_rules": decision["matched_rules"],
                "task_analysis": task_analysis,
                "available_utilities": available_utilities,
                "recommendation": self._generate_recommendation(
                    decision, available_utilities
                ),
            }

            # Store decision for learning
            await self._store_decision(result)

            return result

        except Exception as e:
            self.logger.error(f"Failed to decide execution method: {e}")
            return {
                "task_id": task_briefing.task_id,
                "preferred_execution": "worker",  # Default fallback
                "confidence": 0.5,
                "reasoning": f"Error in decision process: {str(e)}",
                "error": str(e),
            }

    async def _analyze_task(self, task_briefing: TaskBriefing) -> Dict[str, Any]:
        """Analyze task characteristics for decision making."""
        description = task_briefing.description.lower()

        # Extract keywords
        keywords = []
        for rule in self.decision_rules:
            rule_keywords = rule.conditions.get("keywords", [])
            for keyword in rule_keywords:
                if keyword.lower() in description:
                    keywords.append(keyword)

        # Determine task type based on role and description
        task_type = self._infer_task_type(task_briefing)

        # Assess complexity
        complexity = self._assess_complexity(task_briefing)

        # Check for deterministic patterns
        is_deterministic = self._is_deterministic_task(description)

        return {
            "description": task_briefing.description,
            "role": task_briefing.role.value,
            "keywords": keywords,
            "task_type": task_type,
            "complexity": complexity.value,
            "is_deterministic": is_deterministic,
            "dependencies": task_briefing.dependencies,
            "context": task_briefing.context,
        }

    def _infer_task_type(self, task_briefing: TaskBriefing) -> List[str]:
        """Infer task type from briefing."""
        description = task_briefing.description.lower()
        role = task_briefing.role

        task_types = []

        # Role-based inference
        if role == TaskRole.CODER:
            if any(word in description for word in ["implement", "create", "build"]):
                task_types.append("implementation")
            elif any(word in description for word in ["fix", "bug", "error"]):
                task_types.append("bug_fix")
            elif any(word in description for word in ["test", "coverage"]):
                task_types.append("testing")

        elif role == TaskRole.ADVERSARY:
            task_types.extend(["review", "analysis", "security"])

        # Content-based inference
        if any(word in description for word in ["lint", "format", "style"]):
            task_types.append("code_quality")

        if any(word in description for word in ["build", "compile", "package"]):
            task_types.append("build")

        if any(word in description for word in ["docs", "documentation"]):
            task_types.append("documentation")

        if any(word in description for word in ["security", "vulnerability"]):
            task_types.append("security")

        if any(word in description for word in ["git", "commit", "branch"]):
            task_types.append("version_control")

        return task_types or ["general"]

    def _assess_complexity(self, task_briefing: TaskBriefing) -> TaskComplexity:
        """Assess task complexity."""
        description = task_briefing.description.lower()

        # Simple deterministic tasks
        simple_indicators = [
            "lint",
            "format",
            "build",
            "compile",
            "test",
            "run",
            "install",
            "update",
            "commit",
            "push",
        ]

        # Complex reasoning tasks
        complex_indicators = [
            "design",
            "architect",
            "implement",
            "create",
            "develop",
            "analyze",
            "investigate",
            "research",
            "optimize",
        ]

        # Creative tasks
        creative_indicators = [
            "invent",
            "innovate",
            "brainstorm",
            "prototype",
            "experiment",
            "explore",
        ]

        if any(indicator in description for indicator in creative_indicators):
            return TaskComplexity.CREATIVE
        elif any(indicator in description for indicator in complex_indicators):
            return TaskComplexity.COMPLEX
        elif any(indicator in description for indicator in simple_indicators):
            return TaskComplexity.SIMPLE
        else:
            return TaskComplexity.MODERATE

    def _is_deterministic_task(self, description: str) -> bool:
        """Check if task is deterministic (suitable for utilities)."""
        deterministic_patterns = [
            "run",
            "execute",
            "lint",
            "format",
            "build",
            "compile",
            "test",
            "install",
            "update",
            "scan",
            "check",
        ]

        return any(pattern in description for pattern in deterministic_patterns)

    async def _apply_decision_rules(
        self, task_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply decision rules to determine execution method."""
        matched_rules = []
        total_score_utility = 0.0
        total_score_worker = 0.0

        # Sort rules by priority (higher first)
        sorted_rules = sorted(
            self.decision_rules, key=lambda r: r.priority, reverse=True
        )

        for rule in sorted_rules:
            match_score = self._calculate_rule_match(rule, task_analysis)

            if match_score > 0.3:  # Minimum threshold for rule activation
                matched_rules.append(
                    {
                        "name": rule.name,
                        "description": rule.description,
                        "match_score": match_score,
                        "confidence": rule.confidence,
                        "preferred_execution": rule.preferred_execution,
                    }
                )

                # Weight score by rule confidence and match score
                weighted_score = rule.confidence * match_score

                if rule.preferred_execution == "utility":
                    total_score_utility += weighted_score
                else:
                    total_score_worker += weighted_score

        # Determine preferred execution
        if total_score_utility > total_score_worker:
            preferred_execution = "utility"
            confidence = total_score_utility / (
                total_score_utility + total_score_worker
            )
        else:
            preferred_execution = "worker"
            confidence = total_score_worker / (total_score_utility + total_score_worker)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            matched_rules, preferred_execution, confidence
        )

        return {
            "preferred_execution": preferred_execution,
            "confidence": confidence,
            "reasoning": reasoning,
            "matched_rules": matched_rules,
            "scores": {"utility": total_score_utility, "worker": total_score_worker},
        }

    def _calculate_rule_match(
        self, rule: DecisionRule, task_analysis: Dict[str, Any]
    ) -> float:
        """Calculate how well a rule matches the task analysis."""
        match_score = 0.0
        total_conditions = 0

        conditions = rule.conditions

        # Check keyword matches
        if "keywords" in conditions:
            total_conditions += 1
            rule_keywords = conditions["keywords"]
            task_keywords = task_analysis.get("keywords", [])

            matched_keywords = set(rule_keywords) & set(task_keywords)
            if matched_keywords:
                match_score += len(matched_keywords) / len(rule_keywords)

        # Check task type matches
        if "task_type" in conditions:
            total_conditions += 1
            rule_types = conditions["task_type"]
            task_types = task_analysis.get("task_type", [])

            matched_types = set(rule_types) & set(task_types)
            if matched_types:
                match_score += len(matched_types) / len(rule_types)

        # Check complexity match
        if "complexity" in conditions:
            total_conditions += 1
            rule_complexity = conditions["complexity"]
            task_complexity = task_analysis.get("complexity")

            if task_complexity in rule_complexity:
                match_score += 1.0

        # Check deterministic nature
        if "deterministic" in conditions:
            total_conditions += 1
            required_deterministic = conditions["deterministic"]
            is_deterministic = task_analysis.get("is_deterministic", False)

            if required_deterministic == is_deterministic:
                match_score += 1.0

        # Normalize by number of conditions
        return match_score / max(total_conditions, 1)

    def _generate_reasoning(
        self, matched_rules: List[Dict], preferred_execution: str, confidence: float
    ) -> str:
        """Generate human-readable reasoning for the decision."""
        if not matched_rules:
            return f"No specific rules matched. Defaulting to {preferred_execution} execution."

        top_rules = sorted(matched_rules, key=lambda r: r["match_score"], reverse=True)[
            :3
        ]

        reasoning_parts = [
            f"Based on analysis, {preferred_execution} execution is preferred (confidence: {confidence:.2%})."
        ]

        reasoning_parts.append("Key factors:")
        for rule in top_rules:
            reasoning_parts.append(
                f"- {rule['description']} (match: {rule['match_score']:.1%}, "
                f"prefers: {rule['preferred_execution']})"
            )

        return " ".join(reasoning_parts)

    async def _find_matching_utilities(
        self, task_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find utilities that could handle the task."""
        try:
            available_utilities = await self.utility_registry.list_utilities()
            matching_utilities = []

            task_keywords = task_analysis.get("keywords", [])
            task_types = task_analysis.get("task_type", [])

            for utility in available_utilities:
                utility_config = utility.get("config", {})
                utility_description = utility_config.get("description", "").lower()

                # Check if utility description matches task keywords or types
                match_score = 0.0

                for keyword in task_keywords:
                    if keyword.lower() in utility_description:
                        match_score += 0.3

                for task_type in task_types:
                    if task_type.lower() in utility_description:
                        match_score += 0.4

                if match_score > 0.3:
                    matching_utilities.append(
                        {
                            "name": utility.get("name"),
                            "category": utility.get("category"),
                            "description": utility_config.get("description"),
                            "match_score": match_score,
                        }
                    )

            # Sort by match score
            return sorted(
                matching_utilities, key=lambda u: u["match_score"], reverse=True
            )

        except Exception as e:
            self.logger.error(f"Failed to find matching utilities: {e}")
            return []

    def _generate_recommendation(
        self, decision: Dict[str, Any], available_utilities: List[Dict]
    ) -> str:
        """Generate execution recommendation."""
        preferred = decision["preferred_execution"]
        confidence = decision["confidence"]

        if preferred == "utility" and available_utilities:
            top_utility = available_utilities[0]
            return (
                f"Recommend using '{top_utility['name']}' utility "
                f"(match: {top_utility['match_score']:.1%}). "
                f"Confidence in utility execution: {confidence:.1%}"
            )
        elif preferred == "utility" and not available_utilities:
            return (
                f"Utilities preferred but none available. "
                f"Consider implementing relevant utility or use worker. "
                f"Confidence: {confidence:.1%}"
            )
        else:
            return (
                f"Recommend using intelligent worker for this task. "
                f"Requires reasoning/creativity beyond utility capabilities. "
                f"Confidence: {confidence:.1%}"
            )

    async def _store_decision(self, decision_result: Dict[str, Any]) -> None:
        """Store decision for learning and analysis."""
        try:
            decision_key = f"/supervisor/decisions/{decision_result['task_id']}"
            await self.memory.mcp.write(decision_key, str(decision_result))
        except Exception as e:
            self.logger.warning(f"Failed to store decision: {e}")

    async def add_custom_rule(self, rule: DecisionRule) -> None:
        """Add a custom decision rule."""
        self.decision_rules.append(rule)

        # Store in memory for persistence
        try:
            rules_key = "/supervisor/decision_rules"
            rules_data = [rule.model_dump() for rule in self.decision_rules]
            await self.memory.mcp.write(rules_key, str(rules_data))
        except Exception as e:
            self.logger.error(f"Failed to store custom rule: {e}")

    async def get_decision_statistics(self) -> Dict[str, Any]:
        """Get statistics about decision making."""
        try:
            decision_keys = await self.memory.mcp.list_keys("/supervisor/decisions/")

            if not decision_keys:
                return {"total_decisions": 0}

            utility_decisions = 0
            worker_decisions = 0
            total_confidence = 0.0

            for key in decision_keys[:100]:  # Limit to recent decisions
                try:
                    decision_data = await self.memory.mcp.read(key)
                    decision = eval(
                        decision_data
                    )  # Note: In production, use proper JSON parsing

                    if decision.get("preferred_execution") == "utility":
                        utility_decisions += 1
                    else:
                        worker_decisions += 1

                    total_confidence += decision.get("confidence", 0.0)
                except Exception:
                    continue

            total_decisions = utility_decisions + worker_decisions

            return {
                "total_decisions": total_decisions,
                "utility_decisions": utility_decisions,
                "worker_decisions": worker_decisions,
                "utility_percentage": (
                    (utility_decisions / total_decisions * 100)
                    if total_decisions > 0
                    else 0
                ),
                "average_confidence": (
                    (total_confidence / total_decisions) if total_decisions > 0 else 0
                ),
            }

        except Exception as e:
            self.logger.error(f"Failed to get decision statistics: {e}")
            return {"error": str(e)}
