"""
Unified configuration management for Py4GW.

Provides a consistent interface for loading and saving configuration files,
supporting both JSON and INI formats.
"""

import json
import os
from enum import Enum
from typing import Any, Dict, Optional, Union
from configparser import ConfigParser


class ConfigType(Enum):
    """Supported configuration file types."""
    JSON = "json"
    INI = "ini"


class ConfigManager:
    """
    Unified configuration manager supporting JSON and INI formats.

    Usage:
        # JSON config
        config = ConfigManager("my_bot", ConfigType.JSON)
        config.load()
        value = config.get("setting_name", default="default_value")
        config.set("setting_name", "new_value")
        config.save()

        # INI config
        config = ConfigManager("my_widget", ConfigType.INI)
        config.load()
        value = config.get("section.key", default=100)
    """

    def __init__(
        self,
        config_name: str,
        config_type: ConfigType = ConfigType.JSON,
        config_dir: Optional[str] = None
    ):
        """
        Initialize the configuration manager.

        Args:
            config_name: Name of the configuration file (without extension)
            config_type: Type of configuration file (JSON or INI)
            config_dir: Optional directory for config files. Defaults to Config/
        """
        self.config_name = config_name
        self.config_type = config_type

        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "Config")

        self.config_dir = config_dir
        self._data: Dict[str, Any] = {}
        self._ini_parser: Optional[ConfigParser] = None

        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

    @property
    def config_path(self) -> str:
        """Get the full path to the configuration file."""
        extension = "json" if self.config_type == ConfigType.JSON else "ini"
        return os.path.join(self.config_dir, f"{self.config_name}.{extension}")

    def load(self) -> bool:
        """
        Load configuration from file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if self.config_type == ConfigType.JSON:
                return self._load_json()
            else:
                return self._load_ini()
        except Exception:
            return False

    def _load_json(self) -> bool:
        """Load JSON configuration."""
        if not os.path.exists(self.config_path):
            self._data = {}
            return False

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        return True

    def _load_ini(self) -> bool:
        """Load INI configuration."""
        self._ini_parser = ConfigParser()
        if not os.path.exists(self.config_path):
            return False

        self._ini_parser.read(self.config_path, encoding="utf-8")

        # Convert to dict for consistent interface
        self._data = {}
        for section in self._ini_parser.sections():
            self._data[section] = dict(self._ini_parser[section])

        return True

    def save(self) -> bool:
        """
        Save configuration to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if self.config_type == ConfigType.JSON:
                return self._save_json()
            else:
                return self._save_ini()
        except Exception:
            return False

    def _save_json(self) -> bool:
        """Save JSON configuration."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4)
        return True

    def _save_ini(self) -> bool:
        """Save INI configuration."""
        if self._ini_parser is None:
            self._ini_parser = ConfigParser()

        # Update parser from data
        for section, values in self._data.items():
            if not self._ini_parser.has_section(section):
                self._ini_parser.add_section(section)
            for key, value in values.items():
                self._ini_parser.set(section, key, str(value))

        with open(self.config_path, "w", encoding="utf-8") as f:
            self._ini_parser.write(f)
        return True

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        For INI files, use "section.key" format.
        For JSON files, use dot notation for nested values.

        Args:
            key: The configuration key
            default: Default value if key not found

        Returns:
            The configuration value or default
        """
        parts = key.split(".")
        value = self._data

        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default

    def get_int(self, key: str, default: int = 0) -> int:
        """Get a configuration value as integer."""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a configuration value as float."""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a configuration value as boolean."""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        return bool(value)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        For INI files, use "section.key" format.
        For JSON files, use dot notation for nested values.

        Args:
            key: The configuration key
            value: The value to set
        """
        parts = key.split(".")

        if len(parts) == 1:
            self._data[key] = value
        else:
            current = self._data
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value

    def has(self, key: str) -> bool:
        """Check if a configuration key exists."""
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """
        Delete a configuration key.

        Returns:
            True if deleted, False if key didn't exist
        """
        parts = key.split(".")

        try:
            if len(parts) == 1:
                del self._data[key]
            else:
                current = self._data
                for part in parts[:-1]:
                    current = current[part]
                del current[parts[-1]]
            return True
        except (KeyError, TypeError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Get the entire configuration as a dictionary."""
        return self._data.copy()
