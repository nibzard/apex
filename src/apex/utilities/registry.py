"""Utility registry for managing and discovering utilities."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Type

from apex.core.memory import MemoryPatterns

from .base import BaseUtility, UtilityCategory, UtilityConfig


class UtilityRegistry:
    """Registry for managing utilities in the APEX framework."""

    def __init__(self, memory: MemoryPatterns):
        self.memory = memory
        self.logger = logging.getLogger(__name__)
        self._utilities: Dict[str, Type[BaseUtility]] = {}
        self._configs: Dict[str, UtilityConfig] = {}

    async def register_utility(
        self, utility_class: Type[BaseUtility], config: UtilityConfig
    ) -> bool:
        """Register a utility in the registry.

        Args:
            utility_class: The utility class to register
            config: Configuration for the utility

        Returns:
            True if registration succeeded, False otherwise

        """
        try:
            # Validate configuration
            temp_utility = utility_class(config)
            errors = temp_utility.validate_config()

            if errors:
                self.logger.error(f"Utility {config.name} validation failed: {errors}")
                return False

            # Store in memory
            self._utilities[config.name] = utility_class
            self._configs[config.name] = config

            # Persist to LMDB
            config_key = f"/utilities/registry/{config.name}/config"
            await self.memory.mcp.write(config_key, config.model_dump_json())

            # Store utility metadata
            metadata = {
                "name": config.name,
                "category": config.category.value,
                "version": config.version,
                "description": config.description,
                "class_name": utility_class.__name__,
                "module": utility_class.__module__,
                "registered_at": UtilityConfig().model_dump().get("created_at", ""),
            }

            metadata_key = f"/utilities/registry/{config.name}/metadata"
            await self.memory.mcp.write(metadata_key, json.dumps(metadata))

            self.logger.info(f"Registered utility: {config.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register utility {config.name}: {e}")
            return False

    async def get_utility(self, name: str) -> Optional[BaseUtility]:
        """Get a utility instance by name.

        Args:
            name: Name of the utility

        Returns:
            Utility instance or None if not found

        """
        if name not in self._utilities:
            # Try to load from LMDB
            if not await self._load_utility_from_memory(name):
                return None

        utility_class = self._utilities[name]
        config = self._configs[name]

        return utility_class(config)

    async def list_utilities(
        self, category: Optional[UtilityCategory] = None
    ) -> List[Dict[str, Any]]:
        """List available utilities.

        Args:
            category: Optional category filter

        Returns:
            List of utility metadata

        """
        utilities = []

        try:
            # Load from memory if not already loaded
            registry_keys = await self.memory.mcp.list_keys("/utilities/registry/")

            for key in registry_keys:
                if key.endswith("/metadata"):
                    metadata_json = await self.memory.mcp.read(key)
                    if metadata_json:
                        metadata = json.loads(metadata_json)

                        # Apply category filter
                        if category and metadata.get("category") != category.value:
                            continue

                        utilities.append(metadata)

        except Exception as e:
            self.logger.error(f"Failed to list utilities: {e}")

        return utilities

    async def get_utilities_by_category(
        self, category: UtilityCategory
    ) -> List[BaseUtility]:
        """Get all utilities in a specific category.

        Args:
            category: Utility category

        Returns:
            List of utility instances

        """
        utilities = []

        utility_list = await self.list_utilities(category)

        for utility_info in utility_list:
            utility = await self.get_utility(utility_info["name"])
            if utility:
                utilities.append(utility)

        return utilities

    async def unregister_utility(self, name: str) -> bool:
        """Unregister a utility.

        Args:
            name: Name of the utility to unregister

        Returns:
            True if unregistration succeeded, False otherwise

        """
        try:
            # Remove from memory
            if name in self._utilities:
                del self._utilities[name]
            if name in self._configs:
                del self._configs[name]

            # Remove from LMDB
            config_key = f"/utilities/registry/{name}/config"
            metadata_key = f"/utilities/registry/{name}/metadata"

            await self.memory.mcp.delete(config_key)
            await self.memory.mcp.delete(metadata_key)

            self.logger.info(f"Unregistered utility: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister utility {name}: {e}")
            return False

    async def update_utility_config(self, name: str, config: UtilityConfig) -> bool:
        """Update utility configuration.

        Args:
            name: Name of the utility
            config: New configuration

        Returns:
            True if update succeeded, False otherwise

        """
        try:
            if name not in self._utilities:
                self.logger.error(f"Utility {name} not found")
                return False

            # Validate new configuration
            utility_class = self._utilities[name]
            temp_utility = utility_class(config)
            errors = temp_utility.validate_config()

            if errors:
                self.logger.error(f"Configuration validation failed: {errors}")
                return False

            # Update configuration
            self._configs[name] = config

            # Persist to LMDB
            config_key = f"/utilities/registry/{name}/config"
            await self.memory.mcp.write(config_key, config.model_dump_json())

            self.logger.info(f"Updated configuration for utility: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update utility config {name}: {e}")
            return False

    async def _load_utility_from_memory(self, name: str) -> bool:
        """Load utility from LMDB memory.

        Args:
            name: Name of the utility

        Returns:
            True if loaded successfully, False otherwise

        """
        try:
            # Load configuration
            config_key = f"/utilities/registry/{name}/config"
            config_json = await self.memory.mcp.read(config_key)

            if not config_json:
                return False

            config_data = json.loads(config_json)
            config = UtilityConfig(**config_data)

            # Load metadata to get class information
            metadata_key = f"/utilities/registry/{name}/metadata"
            metadata_json = await self.memory.mcp.read(metadata_key)

            if not metadata_json:
                return False

            metadata = json.loads(metadata_json)

            # Dynamically import the utility class
            module_name = metadata["module"]
            class_name = metadata["class_name"]

            module = __import__(module_name, fromlist=[class_name])
            utility_class = getattr(module, class_name)

            # Store in memory
            self._utilities[name] = utility_class
            self._configs[name] = config

            return True

        except Exception as e:
            self.logger.error(f"Failed to load utility {name} from memory: {e}")
            return False

    async def search_utilities(self, query: str) -> List[Dict[str, Any]]:
        """Search utilities by name or description.

        Args:
            query: Search query

        Returns:
            List of matching utility metadata

        """
        utilities = await self.list_utilities()

        query_lower = query.lower()
        matches = []

        for utility in utilities:
            name = utility.get("name", "").lower()
            description = utility.get("description", "").lower()

            if query_lower in name or query_lower in description:
                matches.append(utility)

        return matches

    async def get_utility_dependencies(self, name: str) -> List[str]:
        """Get dependencies for a utility.

        Args:
            name: Name of the utility

        Returns:
            List of dependency names

        """
        if name in self._configs:
            return self._configs[name].dependencies

        # Try to load from memory
        config_key = f"/utilities/registry/{name}/config"
        config_json = await self.memory.mcp.read(config_key)

        if config_json:
            config_data = json.loads(config_json)
            return config_data.get("dependencies", [])

        return []

    async def validate_dependencies(self, name: str) -> List[str]:
        """Validate that all dependencies for a utility are available.

        Args:
            name: Name of the utility

        Returns:
            List of missing dependencies

        """
        dependencies = await self.get_utility_dependencies(name)
        missing = []

        for dep in dependencies:
            if dep not in self._utilities:
                # Check if available in memory
                if not await self._load_utility_from_memory(dep):
                    missing.append(dep)

        return missing

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics.

        Returns:
            Dictionary with registry statistics

        """
        utilities = await self.list_utilities()

        stats = {
            "total_utilities": len(utilities),
            "by_category": {},
            "loaded_in_memory": len(self._utilities),
            "versions": {},
        }

        for utility in utilities:
            category = utility.get("category", "unknown")
            version = utility.get("version", "unknown")

            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            stats["versions"][version] = stats["versions"].get(version, 0) + 1

        return stats
