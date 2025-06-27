"""Custom utility templates for user-defined utility creation."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from apex.core.memory import MemoryPatterns
from apex.utilities.base import UtilityCategory, UtilityConfig
from apex.utilities.registry import UtilityRegistry


class ParameterTemplate(BaseModel):
    """Template for utility parameters."""

    name: str
    type: str  # "string", "integer", "boolean", "list", "dict"
    description: str
    default: Optional[Any] = None
    required: bool = False
    validation: Optional[Dict[str, Any]] = None  # Validation rules
    choices: Optional[List[Any]] = None  # Valid choices for the parameter


class UtilityTemplate(BaseModel):
    """Template for creating custom utilities."""

    name: str
    category: UtilityCategory
    description: str
    author: Optional[str] = None
    version: str = "1.0.0"

    # Execution configuration
    execution_type: str  # "command", "python", "script"
    command_template: Optional[str] = None  # For command utilities
    script_template: Optional[str] = None  # For script utilities
    python_function: Optional[str] = None  # For python utilities

    # Parameters
    parameters: List[ParameterTemplate] = Field(default_factory=list)

    # Requirements
    required_tools: List[str] = Field(default_factory=list)
    required_packages: List[str] = Field(default_factory=list)

    # Configuration
    timeout_seconds: int = 300
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    working_directory: Optional[str] = None

    # Output configuration
    capture_stdout: bool = True
    capture_stderr: bool = True
    output_format: str = "text"  # "text", "json", "xml"

    # Documentation
    usage_examples: List[str] = Field(default_factory=list)
    troubleshooting: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)


class UtilityTemplateManager:
    """Manages custom utility templates."""

    def __init__(self, memory: MemoryPatterns):
        self.memory = memory
        self.registry = UtilityRegistry(memory)
        self.logger = logging.getLogger(__name__)

        # Built-in templates
        self.builtin_templates: Dict[str, UtilityTemplate] = {}
        self._initialize_builtin_templates()

    def _initialize_builtin_templates(self) -> None:
        """Initialize built-in utility templates."""
        self.builtin_templates = {
            "command_utility": UtilityTemplate(
                name="Command Utility Template",
                category=UtilityCategory.AUTOMATION,
                description="Template for creating command-line utilities",
                execution_type="command",
                command_template="{command} {args}",
                parameters=[
                    ParameterTemplate(
                        name="command",
                        type="string",
                        description="The command to execute",
                        required=True,
                    ),
                    ParameterTemplate(
                        name="args",
                        type="string",
                        description="Command arguments",
                        default="",
                    ),
                    ParameterTemplate(
                        name="working_dir",
                        type="string",
                        description="Working directory for command execution",
                        default=".",
                    ),
                ],
                usage_examples=[
                    "Basic command: {command: 'ls', args: '-la'}",
                    "With working directory: {command: 'git', args: 'status', working_dir: '/path/to/repo'}",
                ],
            ),
            "python_function": UtilityTemplate(
                name="Python Function Template",
                category=UtilityCategory.AUTOMATION,
                description="Template for creating Python function utilities",
                execution_type="python",
                python_function="async def execute_utility(context, **kwargs): pass",
                parameters=[
                    ParameterTemplate(
                        name="function_name",
                        type="string",
                        description="Name of the Python function to execute",
                        required=True,
                    ),
                    ParameterTemplate(
                        name="module_path",
                        type="string",
                        description="Path to the Python module",
                        required=True,
                    ),
                ],
                usage_examples=[
                    "Call function: {function_name: 'process_data', module_path: 'utils.data_processor'}"
                ],
            ),
            "script_runner": UtilityTemplate(
                name="Script Runner Template",
                category=UtilityCategory.AUTOMATION,
                description="Template for running custom scripts",
                execution_type="script",
                script_template="#!/bin/bash\n# Script template\necho 'Executing utility script'",
                parameters=[
                    ParameterTemplate(
                        name="script_path",
                        type="string",
                        description="Path to the script file",
                        required=True,
                    ),
                    ParameterTemplate(
                        name="interpreter",
                        type="string",
                        description="Script interpreter",
                        default="bash",
                        choices=["bash", "python", "node", "ruby"],
                    ),
                ],
                usage_examples=[
                    "Bash script: {script_path: 'scripts/deploy.sh', interpreter: 'bash'}",
                    "Python script: {script_path: 'scripts/analyzer.py', interpreter: 'python'}",
                ],
            ),
            "api_client": UtilityTemplate(
                name="API Client Template",
                category=UtilityCategory.INTEGRATION,
                description="Template for creating API client utilities",
                execution_type="python",
                python_function="async def api_request(context, **kwargs): pass",
                parameters=[
                    ParameterTemplate(
                        name="base_url",
                        type="string",
                        description="Base URL for the API",
                        required=True,
                    ),
                    ParameterTemplate(
                        name="endpoint",
                        type="string",
                        description="API endpoint path",
                        required=True,
                    ),
                    ParameterTemplate(
                        name="method",
                        type="string",
                        description="HTTP method",
                        default="GET",
                        choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
                    ),
                    ParameterTemplate(
                        name="headers",
                        type="dict",
                        description="HTTP headers",
                        default={},
                    ),
                    ParameterTemplate(
                        name="auth_token",
                        type="string",
                        description="Authentication token",
                        default="",
                    ),
                ],
                usage_examples=[
                    "GET request: {base_url: 'https://api.example.com', endpoint: '/users', method: 'GET'}",
                    "POST with auth: {base_url: 'https://api.example.com', endpoint: '/data', method: 'POST', auth_token: 'your-token'}",
                ],
            ),
            "file_processor": UtilityTemplate(
                name="File Processor Template",
                category=UtilityCategory.DATA_PROCESSING,
                description="Template for file processing utilities",
                execution_type="python",
                python_function="async def process_files(context, **kwargs): pass",
                parameters=[
                    ParameterTemplate(
                        name="input_pattern",
                        type="string",
                        description="Input file pattern (glob)",
                        required=True,
                    ),
                    ParameterTemplate(
                        name="output_dir",
                        type="string",
                        description="Output directory",
                        default="./output",
                    ),
                    ParameterTemplate(
                        name="operation",
                        type="string",
                        description="Processing operation",
                        choices=["copy", "move", "transform", "analyze"],
                    ),
                    ParameterTemplate(
                        name="recursive",
                        type="boolean",
                        description="Process files recursively",
                        default=False,
                    ),
                ],
                usage_examples=[
                    "Process all Python files: {input_pattern: '**/*.py', operation: 'analyze'}",
                    "Copy images: {input_pattern: '*.jpg', output_dir: '/backup', operation: 'copy'}",
                ],
            ),
            "database_utility": UtilityTemplate(
                name="Database Utility Template",
                category=UtilityCategory.DATA_PROCESSING,
                description="Template for database operation utilities",
                execution_type="python",
                python_function="async def database_operation(context, **kwargs): pass",
                parameters=[
                    ParameterTemplate(
                        name="connection_string",
                        type="string",
                        description="Database connection string",
                        required=True,
                    ),
                    ParameterTemplate(
                        name="operation",
                        type="string",
                        description="Database operation",
                        choices=["query", "insert", "update", "delete", "migrate"],
                    ),
                    ParameterTemplate(
                        name="query",
                        type="string",
                        description="SQL query to execute",
                        default="",
                    ),
                    ParameterTemplate(
                        name="table",
                        type="string",
                        description="Target table name",
                        default="",
                    ),
                ],
                usage_examples=[
                    "Run query: {connection_string: 'sqlite:///db.sqlite', operation: 'query', query: 'SELECT * FROM users'}",
                    "Insert data: {operation: 'insert', table: 'users', data: {...}}",
                ],
            ),
        }

    async def list_templates(self) -> List[Dict[str, Any]]:
        """List all available utility templates."""
        templates = []

        # Add built-in templates
        for template_id, template in self.builtin_templates.items():
            templates.append(
                {
                    "id": template_id,
                    "name": template.name,
                    "category": template.category.value,
                    "description": template.description,
                    "execution_type": template.execution_type,
                    "author": template.author or "APEX",
                    "version": template.version,
                    "builtin": True,
                }
            )

        # Add custom templates from memory
        try:
            custom_templates = await self._load_custom_templates()
            for template_id, template in custom_templates.items():
                templates.append(
                    {
                        "id": template_id,
                        "name": template.name,
                        "category": template.category.value,
                        "description": template.description,
                        "execution_type": template.execution_type,
                        "author": template.author,
                        "version": template.version,
                        "builtin": False,
                    }
                )
        except Exception as e:
            self.logger.warning(f"Failed to load custom templates: {e}")

        return templates

    async def get_template(self, template_id: str) -> Optional[UtilityTemplate]:
        """Get a specific utility template."""
        # Check built-in templates first
        if template_id in self.builtin_templates:
            return self.builtin_templates[template_id]

        # Check custom templates
        try:
            custom_templates = await self._load_custom_templates()
            if template_id in custom_templates:
                return custom_templates[template_id]
        except Exception as e:
            self.logger.error(f"Failed to load custom template {template_id}: {e}")

        return None

    async def create_utility_from_template(
        self, template_id: str, utility_name: str, parameters: Dict[str, Any]
    ) -> Optional[str]:
        """Create a new utility from a template."""
        try:
            template = await self.get_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # Validate parameters against template
            validation_errors = self._validate_parameters(template, parameters)
            if validation_errors:
                raise ValueError(f"Parameter validation failed: {validation_errors}")

            # Create utility configuration
            utility_config = self._generate_utility_config(
                template, utility_name, parameters
            )

            # Register the utility
            utility_id = await self.registry.register_utility(
                name=utility_name, config=utility_config
            )

            self.logger.info(
                f"Created utility '{utility_name}' from template '{template_id}'"
            )
            return utility_id

        except Exception as e:
            self.logger.error(f"Failed to create utility from template: {e}")
            raise

    async def save_custom_template(self, template: UtilityTemplate) -> str:
        """Save a custom utility template."""
        try:
            # Generate template ID
            template_id = f"custom_{template.name.lower().replace(' ', '_')}"

            # Store in memory
            template_key = f"/utilities/templates/custom/{template_id}"
            await self.memory.mcp.write(template_key, template.model_dump_json())

            self.logger.info(
                f"Saved custom template '{template.name}' with ID '{template_id}'"
            )
            return template_id

        except Exception as e:
            self.logger.error(f"Failed to save custom template: {e}")
            raise

    async def delete_custom_template(self, template_id: str) -> bool:
        """Delete a custom utility template."""
        try:
            if template_id in self.builtin_templates:
                raise ValueError("Cannot delete built-in templates")

            template_key = f"/utilities/templates/custom/{template_id}"
            result = await self.memory.mcp.delete(template_key)

            if result:
                self.logger.info(f"Deleted custom template '{template_id}'")

            return result

        except Exception as e:
            self.logger.error(f"Failed to delete custom template: {e}")
            return False

    async def export_template(self, template_id: str, file_path: str) -> bool:
        """Export a template to a file."""
        try:
            template = await self.get_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            export_data = {
                "template_id": template_id,
                "template": template.model_dump(),
                "exported_by": "APEX Utility Template Manager",
                "export_version": "1.0",
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Exported template '{template_id}' to '{file_path}'")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export template: {e}")
            return False

    async def import_template(self, file_path: str) -> Optional[str]:
        """Import a template from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            template_data = import_data.get("template")
            if not template_data:
                raise ValueError("Invalid template file format")

            template = UtilityTemplate(**template_data)
            template_id = await self.save_custom_template(template)

            self.logger.info(
                f"Imported template from '{file_path}' with ID '{template_id}'"
            )
            return template_id

        except Exception as e:
            self.logger.error(f"Failed to import template: {e}")
            return None

    def _validate_parameters(
        self, template: UtilityTemplate, parameters: Dict[str, Any]
    ) -> List[str]:
        """Validate parameters against template definition."""
        errors = []

        # Check required parameters
        for param_template in template.parameters:
            if param_template.required and param_template.name not in parameters:
                errors.append(f"Required parameter '{param_template.name}' is missing")

        # Validate parameter types and values
        for param_name, param_value in parameters.items():
            param_template = next(
                (p for p in template.parameters if p.name == param_name), None
            )

            if param_template:
                # Type validation
                if not self._validate_parameter_type(param_value, param_template.type):
                    errors.append(
                        f"Parameter '{param_name}' has invalid type. Expected {param_template.type}"
                    )

                # Choice validation
                if param_template.choices and param_value not in param_template.choices:
                    errors.append(
                        f"Parameter '{param_name}' must be one of {param_template.choices}"
                    )

                # Custom validation
                if param_template.validation:
                    validation_error = self._validate_parameter_custom(
                        param_value, param_template.validation
                    )
                    if validation_error:
                        errors.append(f"Parameter '{param_name}': {validation_error}")

        return errors

    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type."""
        type_map = {
            "string": str,
            "integer": int,
            "boolean": bool,
            "list": list,
            "dict": dict,
        }

        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True  # Unknown type, assume valid

    def _validate_parameter_custom(
        self, value: Any, validation: Dict[str, Any]
    ) -> Optional[str]:
        """Apply custom validation rules."""
        if "min_length" in validation and isinstance(value, str):
            if len(value) < validation["min_length"]:
                return f"Must be at least {validation['min_length']} characters"

        if "max_length" in validation and isinstance(value, str):
            if len(value) > validation["max_length"]:
                return f"Must be at most {validation['max_length']} characters"

        if "pattern" in validation and isinstance(value, str):
            import re

            if not re.match(validation["pattern"], value):
                return f"Must match pattern: {validation['pattern']}"

        if "min_value" in validation and isinstance(value, (int, float)):
            if value < validation["min_value"]:
                return f"Must be at least {validation['min_value']}"

        if "max_value" in validation and isinstance(value, (int, float)):
            if value > validation["max_value"]:
                return f"Must be at most {validation['max_value']}"

        return None

    def _generate_utility_config(
        self, template: UtilityTemplate, utility_name: str, parameters: Dict[str, Any]
    ) -> UtilityConfig:
        """Generate utility configuration from template and parameters."""
        # Merge template defaults with provided parameters
        final_parameters = {}

        for param_template in template.parameters:
            if param_template.name in parameters:
                final_parameters[param_template.name] = parameters[param_template.name]
            elif param_template.default is not None:
                final_parameters[param_template.name] = param_template.default

        # Add any additional parameters not in template
        for key, value in parameters.items():
            if key not in final_parameters:
                final_parameters[key] = value

        # Add execution-specific parameters
        if template.execution_type == "command" and template.command_template:
            final_parameters["command_template"] = template.command_template
        elif template.execution_type == "python" and template.python_function:
            final_parameters["python_function"] = template.python_function
        elif template.execution_type == "script" and template.script_template:
            final_parameters["script_template"] = template.script_template

        return UtilityConfig(
            name=utility_name,
            category=template.category,
            description=f"{template.description} (Created from template)",
            parameters=final_parameters,
            timeout_seconds=template.timeout_seconds,
            required_tools=template.required_tools,
            environment_variables=template.environment_variables,
        )

    async def _load_custom_templates(self) -> Dict[str, UtilityTemplate]:
        """Load custom templates from memory."""
        templates = {}

        try:
            template_keys = await self.memory.mcp.list_keys(
                "/utilities/templates/custom/"
            )

            for key in template_keys:
                try:
                    template_json = await self.memory.mcp.read(key)
                    if template_json:
                        template_data = json.loads(template_json)
                        template = UtilityTemplate(**template_data)

                        # Extract template ID from key
                        template_id = key.split("/")[-1]
                        templates[template_id] = template

                except Exception as e:
                    self.logger.warning(f"Failed to load template from {key}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Failed to list custom templates: {e}")

        return templates

    async def generate_template_from_existing_utility(
        self, utility_name: str
    ) -> Optional[UtilityTemplate]:
        """Generate a template from an existing utility."""
        try:
            # Get utility configuration
            utilities = await self.registry.list_utilities()
            utility = next(
                (u for u in utilities if u.get("name") == utility_name), None
            )

            if not utility:
                raise ValueError(f"Utility '{utility_name}' not found")

            config = utility.get("config", {})

            # Create parameter templates from utility parameters
            parameter_templates = []
            for param_name, param_value in config.get("parameters", {}).items():
                param_type = "string"
                if isinstance(param_value, bool):
                    param_type = "boolean"
                elif isinstance(param_value, int):
                    param_type = "integer"
                elif isinstance(param_value, list):
                    param_type = "list"
                elif isinstance(param_value, dict):
                    param_type = "dict"

                parameter_templates.append(
                    ParameterTemplate(
                        name=param_name,
                        type=param_type,
                        description=f"Parameter {param_name}",
                        default=param_value,
                    )
                )

            # Create template
            template = UtilityTemplate(
                name=f"{utility_name} Template",
                category=UtilityCategory(config.get("category", "automation")),
                description=f"Template generated from utility '{utility_name}'",
                execution_type="command",  # Default assumption
                parameters=parameter_templates,
                timeout_seconds=config.get("timeout_seconds", 300),
                required_tools=config.get("required_tools", []),
            )

            return template

        except Exception as e:
            self.logger.error(f"Failed to generate template from utility: {e}")
            return None
