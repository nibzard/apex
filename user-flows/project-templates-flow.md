# Project Templates Flow

## Purpose
Use, create, and manage APEX project templates to quickly bootstrap new projects with predefined configurations, tech stacks, and agent behaviors for common development scenarios.

## Prerequisites
- APEX installed and configured
- Understanding of project structure and configuration
- Basic knowledge of template customization

## Template Overview

### What are APEX Templates?
Templates are predefined project configurations that include:
- **Project Structure** - Directory layout and initial files
- **Technology Stack** - Languages, frameworks, and tools
- **Agent Configuration** - Customized agent behaviors and prompts
- **Task Templates** - Common task patterns for the project type
- **Development Workflow** - Predefined coordination patterns

### Built-in Templates:
- **web-application** - Full-stack web apps with frontend/backend
- **api-service** - REST/GraphQL API services
- **cli-tool** - Command-line applications
- **library** - Reusable code libraries
- **data-pipeline** - Data processing and ETL systems
- **microservice** - Containerized microservices

## Using Existing Templates

### 1. List Available Templates

#### View Built-in Templates:
```bash
# List all available templates
uv run apex templates list

# View template details
uv run apex templates show web-application
```

**Example Output:**
```
Available APEX Templates:

web-application
├── Description: Full-stack web application with React frontend and Node.js backend
├── Tech Stack: JavaScript, React, Node.js, Express, PostgreSQL
├── Features: Authentication, API endpoints, database integration
└── Agent Config: Frontend/backend specialization, security focus

api-service
├── Description: RESTful API service with authentication and documentation
├── Tech Stack: Python, FastAPI, PostgreSQL, Docker
├── Features: OpenAPI docs, authentication, rate limiting
└── Agent Config: API design focus, comprehensive testing

cli-tool
├── Description: Command-line application with argument parsing and configuration
├── Tech Stack: Python, Click, pytest
├── Features: CLI interface, configuration management, testing
└── Agent Config: User experience focus, cross-platform compatibility
```

### 2. Create Project from Template

#### Use Template with Customization:
```bash
# Create project from template
uv run apex new my-api --template api-service

# Create with custom tech stack
uv run apex new my-web-app --template web-application --tech "TypeScript,React,Python,FastAPI"

# Create with specific features
uv run apex new my-service --template microservice --features "authentication,monitoring,logging"
```

#### Interactive Template Selection:
```bash
# Start interactive template wizard
uv run apex new my-project --interactive

# Example interaction:
# ? Select project type:
#   > Web Application
#     API Service
#     CLI Tool
#     Library
#     Custom
#
# ? Select tech stack:
#   > JavaScript/TypeScript
#     Python
#     Mixed (JS frontend, Python backend)
#     Other
#
# ? Include authentication? (Y/n) Y
# ? Include database integration? (Y/n) Y
# ? Deployment target:
#   > Docker containers
#     Serverless functions
#     Traditional servers
```

## Template Structure

### 1. Template Configuration File

#### Template Definition (template.json):
```json
{
  "template_id": "api-service",
  "name": "REST API Service",
  "description": "Production-ready REST API with authentication and documentation",
  "version": "1.0.0",
  "author": "APEX Templates",
  "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker", "pytest"],
  "project_type": "API Service",
  "features": ["authentication", "documentation", "rate-limiting", "monitoring"],
  "agent_config": {
    "supervisor": {
      "focus": "api_design_and_architecture",
      "planning_style": "api_first",
      "documentation_requirements": "comprehensive"
    },
    "coder": {
      "coding_standards": "pep8_strict",
      "api_standards": "openapi_3.0",
      "testing_approach": "test_driven",
      "security_practices": "owasp_api_security"
    },
    "adversary": {
      "security_focus": "api_security",
      "testing_emphasis": "edge_cases_and_abuse",
      "performance_testing": true,
      "documentation_review": true
    }
  },
  "initial_tasks": [
    "Design API endpoints and data models",
    "Implement authentication and authorization",
    "Create comprehensive API documentation",
    "Set up monitoring and logging"
  ],
  "directory_structure": {
    "src/": "Main application code",
    "src/api/": "API endpoint definitions",
    "src/models/": "Data models and schemas",
    "src/auth/": "Authentication and authorization",
    "tests/": "Test suites",
    "docs/": "API documentation",
    "docker/": "Container configurations"
  }
}
```

### 2. Template Files Structure

#### Directory Layout:
```
templates/api-service/
├── template.json                # Template configuration
├── project_config.json          # Default apex.json
├── files/                       # Template files to copy
│   ├── src/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── endpoints.py
│   │   ├── models/
│   │   │   └── user.py
│   │   └── auth/
│   │       └── authentication.py
│   ├── tests/
│   │   ├── test_api.py
│   │   └── test_auth.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── tasks/                       # Template task definitions
│   ├── initial-setup.json
│   ├── api-implementation.json
│   └── security-review.json
└── prompts/                     # Custom agent prompts
    ├── supervisor-prompt.md
    ├── coder-prompt.md
    └── adversary-prompt.md
```

## Creating Custom Templates

### 1. Template Creation Process

#### Create New Template:
```bash
# Start template creation wizard
uv run apex templates create my-custom-template

# Or create from existing project
cd my-existing-project
uv run apex templates create-from-project --name "microservice-template"
```

#### Manual Template Creation:
```bash
# Create template directory
mkdir -p ~/.apex/templates/my-template

# Create template configuration
cat > ~/.apex/templates/my-template/template.json << 'EOF'
{
  "template_id": "my-template",
  "name": "My Custom Template",
  "description": "Custom template for my specific needs",
  "tech_stack": ["Python", "Flask", "SQLite"],
  "project_type": "Web Application",
  "features": ["simple-auth", "basic-crud"],
  "agent_config": {
    "supervisor": {"planning_style": "simple"},
    "coder": {"coding_style": "pragmatic"},
    "adversary": {"security_level": "basic"}
  }
}
EOF
```

### 2. Template File Organization

#### Create Template Files:
```bash
# Create template file structure
mkdir -p ~/.apex/templates/my-template/files/src
mkdir -p ~/.apex/templates/my-template/files/tests

# Add template files with placeholders
cat > ~/.apex/templates/my-template/files/src/app.py << 'EOF'
"""{{PROJECT_NAME}} - {{PROJECT_DESCRIPTION}}"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from {{PROJECT_NAME}}!"

if __name__ == '__main__':
    app.run(debug=True)
EOF
```

#### Template Variables:
- `{{PROJECT_NAME}}` - Project name
- `{{PROJECT_DESCRIPTION}}` - Project description
- `{{AUTHOR_NAME}}` - Project author
- `{{PROJECT_ID}}` - Unique project ID
- `{{TECH_STACK}}` - Technology stack list
- `{{CREATION_DATE}}` - Project creation date

### 3. Advanced Template Features

#### Conditional File Inclusion:
```json
{
  "conditional_files": {
    "docker/": {
      "condition": "features.includes('containerization')",
      "files": ["Dockerfile", "docker-compose.yml"]
    },
    "src/auth/": {
      "condition": "features.includes('authentication')",
      "files": ["authentication.py", "middleware.py"]
    }
  }
}
```

#### Template Hooks:
```json
{
  "hooks": {
    "pre_creation": ["scripts/validate-dependencies.sh"],
    "post_creation": ["scripts/setup-database.sh", "scripts/install-deps.sh"],
    "post_init": ["scripts/run-initial-tests.sh"]
  }
}
```

## Template Management

### 1. Template Operations

#### Install Template:
```bash
# Install from URL
uv run apex templates install https://github.com/user/apex-template

# Install from local directory
uv run apex templates install ./my-template-dir

# Install specific version
uv run apex templates install template-name@1.2.0
```

#### Manage Templates:
```bash
# List installed templates
uv run apex templates list

# Update template
uv run apex templates update api-service

# Remove template
uv run apex templates remove old-template

# Validate template
uv run apex templates validate my-template
```

### 2. Template Versioning

#### Version Management:
```json
{
  "template_id": "api-service",
  "version": "2.1.0",
  "compatibility": {
    "apex_version": ">=0.1.0",
    "python_version": ">=3.8"
  },
  "changelog": [
    {
      "version": "2.1.0",
      "changes": ["Added monitoring support", "Updated security practices"]
    },
    {
      "version": "2.0.0",
      "changes": ["Breaking: New agent configuration format"]
    }
  ]
}
```

## Specialized Templates

### 1. Technology-Specific Templates

#### React + FastAPI Template:
```json
{
  "template_id": "react-fastapi",
  "name": "React + FastAPI Full Stack",
  "tech_stack": ["TypeScript", "React", "Python", "FastAPI", "PostgreSQL"],
  "agent_config": {
    "supervisor": {
      "coordination_style": "fullstack",
      "api_contract_focus": true
    },
    "coder": {
      "frontend_backend_coordination": true,
      "api_contract_driven": true
    },
    "adversary": {
      "cross_stack_security": true,
      "integration_testing": true
    }
  },
  "directory_structure": {
    "frontend/": "React application",
    "backend/": "FastAPI application",
    "shared/": "Shared types and contracts"
  }
}
```

### 2. Industry-Specific Templates

#### E-commerce Platform Template:
```json
{
  "template_id": "ecommerce-platform",
  "name": "E-commerce Platform",
  "features": [
    "product-catalog", "shopping-cart", "payment-processing",
    "user-accounts", "order-management", "inventory-tracking"
  ],
  "agent_config": {
    "supervisor": {
      "business_logic_focus": true,
      "compliance_requirements": ["PCI-DSS", "GDPR"]
    },
    "coder": {
      "payment_security": "high",
      "performance_requirements": "high_traffic"
    },
    "adversary": {
      "payment_security_testing": true,
      "fraud_prevention": true,
      "data_privacy": true
    }
  }
}
```

## Template Best Practices

### 1. Template Design Principles

#### Good Template Characteristics:
- **Minimal but Complete** - Include essential files without bloat
- **Configurable** - Support customization through variables
- **Well-Documented** - Clear README and inline comments
- **Agent-Optimized** - Tailored prompts for specific project types
- **Technology-Aligned** - Follow best practices for chosen tech stack

### 2. Template Testing

#### Validate Template:
```bash
# Test template creation
uv run apex new test-project --template my-template --test-mode

# Validate template structure
uv run apex templates validate my-template --strict

# Test agent configuration
uv run apex start --test-agents --dry-run
```

### 3. Template Documentation

#### Template README:
```markdown
# My Custom Template

## Description
Brief description of what this template creates and its intended use case.

## Features
- List of included features
- Technology stack details
- Agent specializations

## Usage
```bash
uv run apex new my-project --template my-custom-template
```

## Customization
- How to modify the template
- Available configuration options
- Template variables

## Requirements
- Prerequisites and dependencies
- Minimum APEX version
```

## Template Sharing

### 1. Template Registry

#### Publish Template:
```bash
# Prepare template for publishing
uv run apex templates package my-template

# Publish to registry
uv run apex templates publish my-template --registry public

# Set template metadata
uv run apex templates metadata my-template \
  --author "Your Name" \
  --license "MIT" \
  --keywords "web,api,python"
```

### 2. Community Templates

#### Browse Community Templates:
```bash
# Search templates
uv run apex templates search --keyword "microservice"

# Browse by category
uv run apex templates browse --category "web-development"

# Show template ratings and reviews
uv run apex templates show react-template --with-reviews
```

## Template Troubleshooting

### Common Issues:

**"Template not found"**
```bash
# Check template installation
uv run apex templates list | grep template-name

# Reinstall template
uv run apex templates install template-name --force
```

**"Template validation failed"**
```bash
# Check template structure
uv run apex templates validate my-template --verbose

# Fix common issues
uv run apex templates fix my-template --auto
```

**"Agent configuration invalid"**
```bash
# Validate agent prompts
uv run apex templates test-agents my-template

# Reset to default agent config
uv run apex templates reset-agents my-template
```

## Related Flows
- [Project Creation Flow](project-creation-flow.md) - Using templates during project creation
- [Configuration Management Flow](configuration-management-flow.md) - Template configurations
- [Agent Management Flow](agent-management-flow.md) - Template-specific agent behaviors
- [Multi-Agent Coordination Flow](multi-agent-coordination-flow.md) - Template coordination patterns
