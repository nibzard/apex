# Multi-Agent Coordination Flow

## Purpose
Coordinate complex development tasks across multiple APEX agents, managing dependencies, communication, conflict resolution, and collaborative workflows for optimal development outcomes.

## Prerequisites
- Multiple APEX agents running (Supervisor, Coder, Adversary)
- Shared LMDB memory system
- Understanding of agent roles and capabilities
- Devcontainer setup (recommended for isolated agent execution)

## Coordination Architecture

### Coordination Layers:
1. **Task-Level Coordination** - Individual task assignment and tracking
2. **Workflow Coordination** - Multi-task dependencies and sequencing
3. **Resource Coordination** - Shared resource access and conflict prevention
4. **Communication Coordination** - Message routing and information sharing
5. **Strategic Coordination** - High-level planning and goal alignment

## Core Coordination Patterns

### 1. Hierarchical Coordination

#### Supervisor-Led Coordination:
```
Supervisor> Breaking down complex feature into coordinated tasks for the team.

> mcp__lmdb__write /projects/{id}/coordination/feature-plan '{
  "coordinator": "supervisor",
  "feature": "user-dashboard",
  "coordination_strategy": "hierarchical",
  "task_breakdown": [
    {
      "task_id": "dashboard-api",
      "assigned_to": "coder",
      "dependencies": [],
      "coordination_notes": "Will interface with auth system from previous sprint"
    },
    {
      "task_id": "dashboard-security-review",
      "assigned_to": "adversary",
      "dependencies": ["dashboard-api"],
      "coordination_notes": "Focus on data access controls and user isolation"
    },
    {
      "task_id": "dashboard-integration",
      "assigned_to": "coder",
      "dependencies": ["dashboard-security-review"],
      "coordination_notes": "Implement security recommendations before merge"
    }
  ]
}'
```

### 2. Peer-to-Peer Coordination

#### Direct Agent Communication:
```
Coder> I need input from Adversary on security requirements before implementing payment processing.

> mcp__lmdb__write /projects/{id}/coordination/coder-to-adversary '{
  "from": "coder",
  "to": "adversary",
  "type": "security_consultation",
  "context": "payment_processing_implementation",
  "questions": [
    "What encryption standards should I use for payment data?",
    "How should I handle PCI compliance requirements?",
    "What input validation is needed for payment forms?"
  ],
  "urgency": "high",
  "blocking": true
}'

Adversary> Responding to Coder's security consultation on payment processing.

> mcp__lmdb__write /projects/{id}/coordination/adversary-to-coder-response '{
  "from": "adversary",
  "to": "coder",
  "response_to": "coder-to-adversary",
  "security_requirements": {
    "encryption": "AES-256 for data at rest, TLS 1.3 for transit",
    "pci_compliance": "Use tokenization, avoid storing card data",
    "input_validation": "Strict regex patterns, no special characters in payment fields",
    "additional_measures": "Implement request signing, rate limiting, fraud detection"
  },
  "implementation_notes": "I'll review the implementation once basic structure is complete"
}'
```

## Coordination Mechanisms

### 1. Shared Memory Coordination

#### Coordination Channels:
```
/coordination/
├── /announcements/          # System-wide announcements
├── /task-dependencies/      # Task dependency tracking
├── /resource-locks/         # Resource access coordination
├── /agent-availability/     # Agent status and availability
├── /conflict-resolution/    # Conflict mediation
└── /decision-logs/         # Coordination decisions
```

#### Resource Lock Coordination:
```
Coder> I need to modify the user authentication module. Acquiring lock to prevent conflicts.

> mcp__lmdb__write /coordination/resource-locks/auth-module '{
  "resource": "src/auth/authentication.py",
  "locked_by": "coder",
  "lock_type": "exclusive",
  "purpose": "implementing_password_reset",
  "estimated_duration": "2 hours",
  "locked_at": "2025-01-08T14:30:00Z"
}'
```

### 2. Event-Driven Coordination

#### Coordination Events:
```json
{
  "event": "task_completed",
  "agent": "coder",
  "task_id": "user-auth-implementation",
  "triggers": [
    {
      "condition": "task_completed",
      "action": "notify_dependent_agents",
      "targets": ["adversary"]
    },
    {
      "condition": "tests_passed",
      "action": "unlock_resources",
      "resources": ["auth-module"]
    }
  ]
}
```

### 3. Consensus-Based Coordination

#### Multi-Agent Decision Making:
```
Supervisor> We need to decide on the database schema for user profiles. Requesting input from all agents.

> mcp__lmdb__write /coordination/decisions/user-profile-schema '{
  "decision_id": "user-profile-schema-v1",
  "decision_type": "architecture",
  "coordinator": "supervisor",
  "participants": ["supervisor", "coder", "adversary"],
  "proposal": {
    "schema": "PostgreSQL with JSON fields for flexible attributes",
    "rationale": "Balances structure with flexibility for future features"
  },
  "voting_deadline": "2025-01-08T18:00:00Z",
  "status": "open"
}'

Coder> Voting on user profile schema proposal.

> mcp__lmdb__write /coordination/decisions/user-profile-schema-votes/coder '{
  "voter": "coder",
  "vote": "approve",
  "comments": "PostgreSQL JSON support is mature, good for development velocity",
  "alternative_suggestion": "Consider adding indices on commonly queried JSON fields"
}'

Adversary> Voting on user profile schema with security concerns.

> mcp__lmdb__write /coordination/decisions/user-profile-schema-votes/adversary '{
  "voter": "adversary",
  "vote": "approve_with_conditions",
  "comments": "Acceptable if we implement proper input validation for JSON fields",
  "security_requirements": [
    "Validate JSON structure against schema",
    "Sanitize all JSON inputs",
    "Implement size limits on JSON fields"
  ]
}'
```

## Workflow Coordination Patterns

### 1. Sequential Workflow

#### Linear Task Chain:
```
Planning → Implementation → Security Review → Testing → Integration → Deployment
    ↓           ↓              ↓            ↓          ↓           ↓
Supervisor → Coder      → Adversary   → Adversary → Coder    → Supervisor
```

### 2. Parallel Workflow

#### Concurrent Development:
```
                  ┌─ Frontend (Coder A) ─┐
Feature Planning ─┤                      ├─ Integration
                  └─ Backend (Coder B) ──┘
                            │
                     Security Review (Adversary)
```

### 3. Iterative Workflow

#### Feedback Loops:
```
Implement → Review → Feedback → Refine → Review → Approve
   ↓         ↓        ↓         ↓        ↓        ↓
 Coder → Adversary → Adversary → Coder → Adversary → Supervisor
   ↑                                       │
   └─────────── Refine Again ──────────────┘
```

## Conflict Resolution

### 1. Automated Conflict Detection

#### Detect Conflicting Tasks:
```
> mcp__lmdb__write /coordination/conflicts/detected '{
  "conflict_id": "auth-module-conflict",
  "type": "resource_conflict",
  "description": "Both Coder and Adversary trying to modify authentication module",
  "participants": ["coder", "adversary"],
  "resources": ["src/auth/authentication.py"],
  "detected_at": "2025-01-08T15:00:00Z",
  "auto_resolution": "queue_based_on_priority"
}'
```

### 2. Supervisor-Mediated Resolution

#### Conflict Mediation:
```
Supervisor> Resolving conflict between Coder and Adversary over authentication approach.

> mcp__lmdb__write /coordination/conflict-resolution/auth-approach '{
  "mediator": "supervisor",
  "conflict": "authentication_method_disagreement",
  "parties": {
    "coder": "Proposes JWT tokens for simplicity",
    "adversary": "Insists on session-based auth for security"
  },
  "resolution": "Hybrid approach - JWT for API, sessions for web interface",
  "rationale": "Balances security concerns with API usability",
  "implementation_plan": {
    "phase_1": "Implement session-based auth for web (Coder)",
    "phase_2": "Add JWT endpoint for API access (Coder)",
    "phase_3": "Security review of both implementations (Adversary)"
  }
}'
```

### 3. Consensus-Based Resolution

#### Democratic Decision Making:
```
# When Supervisor is unavailable or conflict involves Supervisor
> mcp__lmdb__write /coordination/consensus/api-versioning '{
  "issue": "API versioning strategy",
  "voting_method": "majority_rule",
  "proposals": {
    "A": "URL versioning (/v1/api/users)",
    "B": "Header versioning (Accept: application/vnd.api+json;version=1)",
    "C": "Query parameter versioning (?version=1)"
  },
  "votes": {
    "coder": "A",
    "adversary": "B",
    "supervisor": "A"
  },
  "result": "Proposal A wins (2/3 votes)",
  "implementation": "URL versioning will be implemented"
}'
```

## Communication Coordination

### 1. Message Routing

#### Intelligent Message Distribution:
```json
{
  "message_routing": {
    "broadcasts": "/coordination/announcements/",
    "direct_messages": "/coordination/messages/{from}-to-{to}/",
    "group_discussions": "/coordination/groups/{topic}/",
    "urgent_alerts": "/coordination/alerts/",
    "status_updates": "/coordination/status/"
  }
}
```

### 2. Information Sharing Protocols

#### Knowledge Sharing:
```
Coder> Sharing implementation insights that might help other agents.

> mcp__lmdb__write /coordination/knowledge-sharing/database-optimization '{
  "from": "coder",
  "type": "implementation_insight",
  "topic": "database_query_optimization",
  "insight": "Using database connection pooling reduced response time by 40%",
  "applicable_to": ["any agent working on database queries"],
  "implementation_details": {
    "library": "SQLAlchemy connection pooling",
    "configuration": "pool_size=20, max_overflow=30",
    "metrics": "Average query time: 45ms → 27ms"
  }
}'
```

## Advanced Coordination Scenarios

### 1. Crisis Coordination

#### Emergency Response Protocol:
```
Adversary> SECURITY ALERT: Critical vulnerability detected in production.

> mcp__lmdb__write /coordination/crisis/security-breach '{
  "alert_level": "critical",
  "reporter": "adversary",
  "issue": "SQL injection vulnerability in user search",
  "immediate_actions": [
    "Take search feature offline immediately",
    "Audit all user inputs for similar vulnerabilities",
    "Prepare security patch"
  ],
  "coordination_protocol": "emergency",
  "all_agents_required": true
}'

Supervisor> Activating emergency coordination protocol.

> mcp__lmdb__write /coordination/crisis/response-plan '{
  "crisis_id": "security-breach",
  "coordinator": "supervisor",
  "response_assignments": {
    "coder": "Implement immediate patch for SQL injection",
    "adversary": "Audit entire codebase for similar vulnerabilities",
    "supervisor": "Coordinate with operations team for deployment"
  },
  "timeline": "Patch within 2 hours, full audit within 24 hours",
  "communication": "All updates to /coordination/crisis/updates/"
}'
```

### 2. Multi-Project Coordination

#### Cross-Project Dependencies:
```
Supervisor> Managing dependencies between authentication service and main application.

> mcp__lmdb__write /coordination/multi-project/auth-service-deps '{
  "coordinator": "supervisor",
  "projects": ["user-app", "auth-service"],
  "dependency": "Auth service API changes affect user app integration",
  "coordination_plan": {
    "auth_team": "Notify 48 hours before API changes",
    "app_team": "Update integration within 1 week of API release",
    "testing": "Joint integration testing required"
  },
  "communication_channel": "/coordination/cross-project/auth-integration/"
}'
```

## Coordination Metrics and Optimization

### 1. Coordination Effectiveness

#### Measure Coordination Success:
```json
{
  "coordination_metrics": {
    "task_completion_rate": 95,
    "dependency_resolution_time": "avg 4.2 hours",
    "conflict_frequency": "2 per week",
    "conflict_resolution_time": "avg 1.3 hours",
    "communication_response_time": "avg 15 minutes",
    "coordination_overhead": "12% of total development time"
  }
}
```

### 2. Optimization Strategies

#### Improve Coordination Efficiency:
```
> mcp__lmdb__write /coordination/optimization/strategies '{
  "analysis": "Coordination bottlenecks identified",
  "bottlenecks": [
    "Manual dependency tracking causing delays",
    "Ad-hoc communication leading to missed messages",
    "Lack of automated conflict detection"
  ],
  "optimizations": [
    "Implement automated dependency checking",
    "Standardize communication protocols",
    "Add conflict prevention mechanisms",
    "Create coordination templates for common scenarios"
  ]
}'
```

## Coordination Best Practices

### 1. Clear Communication
- Use structured message formats
- Specify urgency and blocking conditions
- Include context and background information
- Confirm receipt of critical messages

### 2. Proactive Coordination
- Anticipate dependencies early
- Communicate changes that might affect others
- Share knowledge and insights regularly
- Plan for potential conflicts

### 3. Efficient Conflict Resolution
- Address conflicts early before they escalate
- Use data and objective criteria for decisions
- Document resolution rationale
- Learn from conflicts to prevent recurrence

## Related Flows
- [Agent Management Flow](agent-management-flow.md) - Managing coordinated agents
- [Task Workflow Flow](task-workflow-flow.md) - Task-level coordination
- [Memory Management Flow](memory-management-flow.md) - Coordination data storage
- [Adversarial Development Flow](adversarial-development-flow.md) - Coordination in adversarial context
