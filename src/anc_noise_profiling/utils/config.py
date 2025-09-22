"""Configuration management for the ANC package."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml


class Config:
    """Configuration manager for ANC noise profiling."""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """Initialize configuration.
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        self.logger = logging.getLogger(__name__)
        self._config = self._load_default_config()
        
        if config_file:
            self.load_config_file(config_file)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            "audio": {
                "sample_rate": 16000,
                "chunk_duration": 0.5,
                "device": None
            },
            "noise_profiling": {
                "method": "first_0.5",
                "silence_threshold": 0.01,
                "min_silence_duration": 0.3
            },
            "processing": {
                "output_mode": "file",
                "save_raw_audio": False,
                "visualization": False
            },
            "logging": {
                "level": "INFO",
                "include_timestamp": True
            },
            "output": {
                "directory": "output",
                "filename_template": "denoised_{timestamp}.wav"
            }
        }
    
    def load_config_file(self, config_file: Union[str, Path]) -> None:
        """Load configuration from file.
        
        Args:
            config_file: Path to configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file format is invalid
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    file_config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    file_config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {config_path.suffix}")
            
            # Merge with default config
            self._config.update(file_config)
            self.logger.info(f"Loaded configuration from: {config_path}")
            
        except Exception as e:
            raise ValueError(f"Failed to load config file {config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "audio.sample_rate")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "audio.sample_rate")
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self.logger.debug(f"Set config {key} = {value}")
    
    def save_config_file(self, config_file: Union[str, Path], format: str = "yaml") -> None:
        """Save current configuration to file.
        
        Args:
            config_file: Path to save configuration
            format: File format ("yaml" or "json")
        """
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                if format.lower() == "yaml":
                    yaml.safe_dump(self._config, f, default_flow_style=False, indent=2)
                elif format.lower() == "json":
                    json.dump(self._config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Saved configuration to: {config_path}")
            
        except Exception as e:
            raise ValueError(f"Failed to save config file {config_path}: {e}")
    
    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio-related configuration."""
        return self._config.get("audio", {})
    
    def get_noise_profiling_config(self) -> Dict[str, Any]:
        """Get noise profiling configuration."""
        return self._config.get("noise_profiling", {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return self._config.get("processing", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get("logging", {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self._config.get("output", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self._config.copy()
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return json.dumps(self._config, indent=2)