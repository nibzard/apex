"""Tests for configuration module."""

import pytest
from pathlib import Path
from apex.config import Config


class TestConfig:
    """Test suite for Config class."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = Config.get_default()
        assert config.debug is False
        assert config.log_level == "info"
        assert config.claude_model == "claude-sonnet-4-20250514"
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = Config(
            debug=True,
            log_level="debug",
            max_agents=5
        )
        assert config.debug is True
        assert config.log_level == "debug"
        assert config.max_agents == 5
    
    def test_config_save_load(self, tmp_path):
        """Test saving and loading configuration."""
        config_path = tmp_path / "config.toml"
        
        # Create and save config
        original_config = Config(debug=True, log_level="debug")
        original_config.save_to_file(config_path)
        
        # Load config
        loaded_config = Config.load_from_file(config_path)
        
        assert loaded_config.debug == original_config.debug
        assert loaded_config.log_level == original_config.log_level