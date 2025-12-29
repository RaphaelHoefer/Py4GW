"""
Shared utilities for Py4GW.

This package provides common utilities and base classes to reduce code duplication
across bots and widgets.
"""

from .config import ConfigManager, ConfigType
from .logging import BotLogger, LogLevel
from .widget_base import WidgetBase
from .event_handler import BotEventHandler
from .retry import retry_on_failure, safe_execute

__all__ = [
    'ConfigManager',
    'ConfigType',
    'BotLogger',
    'LogLevel',
    'WidgetBase',
    'BotEventHandler',
    'retry_on_failure',
    'safe_execute',
]
