# Version Control Flow

## Purpose
Manage git operations within APEX projects, including automatic commits, branch management, and integration with agent workflows.

## Prerequisites
- Git installed and configured
- APEX project with git repository initialized
- Proper git user configuration

## Git Integration in APEX

### Automatic Git Setup:
```bash
# Git repository automatically created during project creation
uv run apex new my-project  # Includes git init

# Skip git initialization if needed
uv run apex new my-project --no-git
```

### Agent Git Responsibilities:
- **Supervisor Agent** - Creates commits, manages branches, handles PRs
- **Coder Agent** - Stages changes as work is completed
- **Adversary Agent** - Reviews diffs and commit history

## Basic Git Operations

### Check Git Status:
```bash
# Via standard git commands
git status
git log --oneline -10

# Via APEX memory (stores git state)
uv run apex memory show /projects/{id}/git/status
```

### Agent-Driven Commits:
Agents use standard git commands through their Claude CLI processes:

```bash
# Coder agent stages work
git add src/new_feature.py tests/test_feature.py

# Supervisor agent creates commits
git commit -m "feat: implement user authentication

Implemented:
- User registration endpoint
- Password hashing and validation
- JWT token generation

Tested by: adversary_agent
Reviewed: security vulnerabilities addressed"
```

## Workflow Integration

### 1. Feature Development Flow:

#### Supervisor Creates Feature Branch:
```bash
git checkout -b feature/user-auth
git push -u origin feature/user-auth
```

#### Store Branch Info in Memory:
```
> apex_lmdb_write /projects/{id}/git/current_branch '{
  "branch": "feature/user-auth",
  "created_by": "supervisor",
  "purpose": "Implement user authentication system",
  "created_at": "2025-01-08T14:00:00Z"
}'
```

#### Coder Implements and Stages:
```bash
# Implement feature
# Create files: src/auth.py, tests/test_auth.py

# Stage changes
git add src/auth.py tests/test_auth.py

# Update progress in memory
```

```
> apex_lmdb_write /projects/{id}/git/staged_changes '{
  "files": ["src/auth.py", "tests/test_auth.py"],
  "description": "User authentication implementation",
  "ready_for_review": true,
  "staged_by": "coder"
}'
```

#### Adversary Reviews Changes:
```bash
# Review staged changes
git diff --cached

# Check for issues
# Run tests
pytest tests/test_auth.py
```

```
> apex_lmdb_write /projects/{id}/git/review_status '{
  "reviewer": "adversary",
  "status": "approved",
  "issues_found": 0,
  "security_review": "passed",
  "recommendation": "ready_for_commit"
}'
```

#### Supervisor Commits:
```bash
git commit -m "feat: implement user authentication

- Add User model with password hashing
- Implement registration endpoint
- Add JWT token generation
- Include comprehensive test suite

Tested-by: adversary_agent
Security-review: passed"
```

### 2. Pull Request Workflow:

#### Create Pull Request (Supervisor):
```bash
# Push feature branch
git push origin feature/user-auth

# Create PR using GitHub CLI
gh pr create --title "feat: implement user authentication" --body "$(cat <<EOF
## Summary
- Implements user authentication system
- Adds registration and login endpoints
- Includes security validations

## Testing
- [x] Unit tests passing
- [x] Security review completed
- [x] Integration tests passing

## Agents
- Implementation: coder_agent
- Review: adversary_agent
- Coordination: supervisor_agent
EOF
)"
```

#### Store PR Information:
```
> apex_lmdb_write /projects/{id}/git/pull_requests/pr-123 '{
  "pr_number": 123,
  "title": "feat: implement user authentication",
  "branch": "feature/user-auth",
  "status": "open",
  "created_by": "supervisor",
  "url": "https://github.com/user/repo/pull/123"
}'
```

## Branching Strategy

### Default Branch Structure:
```
main (production)
├── develop (integration)
├── feature/user-auth (Supervisor + Coder)
├── feature/api-endpoints (Supervisor + Coder)
└── hotfix/security-fix (Adversary + Coder)
```

### Branch Naming Convention:
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

## Commit Message Standards

### APEX Commit Format:
```
<type>(<scope>): <description>

<body>

<footer>
```

### Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Test additions/changes
- `chore` - Maintenance tasks

### APEX-Specific Footer:
```
Implemented-by: coder_agent
Reviewed-by: adversary_agent
Coordinated-by: supervisor_agent
Security-review: passed|failed
Test-status: passing|failing
```

## Git Hooks Integration

### Pre-commit Hook:
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run APEX quality checks
uv run apex memory write /git/pre_commit_check '{
  "status": "running",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'

# Run tests
pytest
if [ $? -ne 0 ]; then
  echo "Tests failed - commit rejected"
  exit 1
fi

# Update memory with success
uv run apex memory write /git/pre_commit_check '{
  "status": "passed",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'
```

### Commit-msg Hook:
```bash
#!/bin/bash
# .git/hooks/commit-msg

# Validate commit message format
if ! grep -qE "^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+" "$1"; then
  echo "Invalid commit message format"
  exit 1
fi

# Add APEX footer if not present
if ! grep -q "Implemented-by:" "$1"; then
  echo "" >> "$1"
  echo "Implemented-by: $(uv run apex memory read /current_agent 2>/dev/null || echo 'unknown')" >> "$1"
fi
```

## Monitoring Git Activity

### Track Git Status:
```bash
# Store current git status in memory
git status --porcelain | uv run apex memory write /git/status -

# Monitor git changes
uv run apex memory watch "/git/*"
```

### Git History Analysis:
```bash
# Agent contribution analysis
git log --format="%an" | sort | uniq -c | sort -nr

# Commit frequency by agent
git log --grep="Implemented-by: coder_agent" --oneline | wc -l
```

## Conflict Resolution

### Merge Conflict Workflow:

#### Detect Conflicts:
```bash
git merge develop
# Conflicts detected

# Store conflict info
```

```
> apex_lmdb_write /projects/{id}/git/conflicts '{
  "status": "detected",
  "files": ["src/auth.py", "tests/test_auth.py"],
  "branch_a": "feature/user-auth",
  "branch_b": "develop",
  "detected_at": "2025-01-08T16:00:00Z"
}'
```

#### Assign Resolution (Supervisor):
```
> apex_lmdb_write /projects/{id}/tasks/resolve-conflict '{
  "description": "Resolve merge conflicts in authentication module",
  "assigned_to": "coder",
  "priority": "high",
  "files": ["src/auth.py", "tests/test_auth.py"]
}'
```

#### Resolution Process (Coder):
```bash
# Resolve conflicts manually
git status
vim src/auth.py  # Resolve conflicts
vim tests/test_auth.py  # Resolve conflicts

# Test resolution
pytest tests/test_auth.py

# Stage resolution
git add src/auth.py tests/test_auth.py
git commit -m "resolve: merge conflicts in authentication module

Resolved conflicts between feature/user-auth and develop:
- Merged authentication methods
- Updated test assertions
- Maintained backward compatibility

Tested-by: local test suite
Conflict-resolution: manual"
```

## Advanced Git Operations

### Automated Releases:
```bash
# Supervisor creates release
git checkout main
git merge develop
git tag -a v1.2.0 -m "Release v1.2.0

Features:
- User authentication system
- API rate limiting
- Enhanced security

Agents:
- supervisor_agent: coordination and release management
- coder_agent: feature implementation
- adversary_agent: security testing and validation"

git push origin main --tags
```

### Branch Cleanup:
```bash
# After PR merge, cleanup
git branch -d feature/user-auth
git push origin --delete feature/user-auth

# Update memory
```

```
> apex_lmdb_delete /projects/{id}/git/pull_requests/pr-123
> apex_lmdb_write /projects/{id}/git/completed_features/user-auth '{
  "completed_at": "2025-01-08T17:00:00Z",
  "merged_to": "main",
  "version": "v1.2.0"
}'
```

## Git Configuration for APEX

### Repository Setup:
```bash
# Configure git for APEX agents
git config user.name "APEX Development Team"
git config user.email "apex-agents@project.dev"

# Set up branch protection
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{
    "strict": true,
    "contexts": ["ci/tests", "ci/security-scan"]
  }' \
  --field enforce_admins=true
```

### Agent Identification:
```bash
# Agents can identify themselves in commits
export GIT_AUTHOR_NAME="coder_agent"
export GIT_COMMITTER_NAME="coder_agent"

# Or use git config per clone
git config user.name "supervisor_agent"
```

## Troubleshooting

### Common Issues:

**"Git repository not initialized"**
```bash
git init
git remote add origin <repository-url>
```

**"Merge conflicts blocking agents"**
```bash
# Check conflict status
uv run apex memory show /git/conflicts

# Assign resolution task
# Provide conflict resolution guidance
```

**"Commit history shows wrong agent"**
```bash
# Fix author for last commit
git commit --amend --author="correct_agent <agent@apex.dev>"
```

## Related Flows
- [Agent Management Flow](agent-management-flow.md) - How agents interact with git
- [Task Workflow Flow](task-workflow-flow.md) - Git operations as tasks
- [Multi-Agent Coordination Flow](multi-agent-coordination-flow.md) - Coordinated git workflows
- [Project Creation Flow](project-creation-flow.md) - Initial git setup
