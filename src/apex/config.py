"""Configuration management for APEX."""

from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import toml


class Config(BaseModel):
    """APEX configuration."""
    
    # Core settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="info", description="Logging level")
    
    # Database settings
    lmdb_path: Path = Field(default_factory=lambda: Path("./apex.db"))
    lmdb_map_size: int = Field(default=10 * 1024 * 1024 * 1024)  # 10GB
    
    # Claude CLI settings
    claude_model: str = Field(default="claude-sonnet-4-20250514")
    max_turns: int = Field(default=50)
    
    # Process settings
    max_agents: int = Field(default=10)
    process_timeout: int = Field(default=300)  # 5 minutes
    
    # MCP settings
    mcp_config_path: Path = Field(default_factory=lambda: Path("./configs/lmdb_mcp.json"))
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> "Config":
        """Load configuration from TOML file."""
        if config_path.exists():
            data = toml.load(config_path)
            return cls(**data)
        return cls()
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to TOML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            toml.dump(self.model_dump(), f)
    
    @classmethod
    def get_default(cls) -> "Config":
        """Get default configuration."""
        return cls()