"""
Unified logging utility for Py4GW bots and widgets.

Provides consistent logging interface that integrates with Py4GW's console system.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field

import Py4GW


class LogLevel(Enum):
    """Log message levels."""
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    NOTICE = "notice"


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: datetime
    message: str
    level: LogLevel
    module: str

    @property
    def formatted(self) -> str:
        """Get the formatted log message."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.message}"


class BotLogger:
    """
    Centralized logging utility for bots and widgets.

    Features:
    - Consistent logging format across all bots/widgets
    - Log history for display in UI
    - Integration with Py4GW console
    - Configurable max history size

    Usage:
        logger = BotLogger("MyBot")
        logger.info("Bot started")
        logger.error("Something went wrong")

        # Display log history in ImGui window
        for entry in logger.history:
            PyImGui.text(entry.formatted)
    """

    # Map LogLevel to Py4GW.Console.MessageType
    _LEVEL_MAP = {
        LogLevel.DEBUG: Py4GW.Console.MessageType.Info,
        LogLevel.INFO: Py4GW.Console.MessageType.Info,
        LogLevel.SUCCESS: Py4GW.Console.MessageType.Success,
        LogLevel.WARNING: Py4GW.Console.MessageType.Warning,
        LogLevel.ERROR: Py4GW.Console.MessageType.Error,
        LogLevel.NOTICE: Py4GW.Console.MessageType.Notice,
    }

    def __init__(
        self,
        module_name: str,
        max_history: int = 100,
        console_output: bool = True
    ):
        """
        Initialize the logger.

        Args:
            module_name: Name of the module/bot/widget for log prefix
            max_history: Maximum number of log entries to keep in history
            console_output: Whether to also output to Py4GW console
        """
        self.module_name = module_name
        self.max_history = max_history
        self.console_output = console_output
        self._history: List[LogEntry] = []

    @property
    def history(self) -> List[LogEntry]:
        """Get the log history (newest first)."""
        return self._history.copy()

    def _log(self, message: str, level: LogLevel) -> None:
        """Internal logging method."""
        entry = LogEntry(
            timestamp=datetime.now(),
            message=message,
            level=level,
            module=self.module_name
        )

        # Add to history (newest first)
        self._history.insert(0, entry)

        # Trim history if needed
        if len(self._history) > self.max_history:
            self._history = self._history[:self.max_history]

        # Output to console if enabled
        if self.console_output:
            msg_type = self._LEVEL_MAP.get(level, Py4GW.Console.MessageType.Info)
            Py4GW.Console.Log(self.module_name, message, msg_type)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self._log(message, LogLevel.DEBUG)

    def info(self, message: str) -> None:
        """Log an info message."""
        self._log(message, LogLevel.INFO)

    def success(self, message: str) -> None:
        """Log a success message."""
        self._log(message, LogLevel.SUCCESS)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self._log(message, LogLevel.WARNING)

    def error(self, message: str) -> None:
        """Log an error message."""
        self._log(message, LogLevel.ERROR)

    def notice(self, message: str) -> None:
        """Log a notice message."""
        self._log(message, LogLevel.NOTICE)

    def clear(self) -> None:
        """Clear the log history."""
        self._history.clear()

    def get_by_level(self, level: LogLevel) -> List[LogEntry]:
        """Get all log entries of a specific level."""
        return [entry for entry in self._history if entry.level == level]

    def get_errors(self) -> List[LogEntry]:
        """Get all error log entries."""
        return self.get_by_level(LogLevel.ERROR)

    def get_warnings(self) -> List[LogEntry]:
        """Get all warning log entries."""
        return self.get_by_level(LogLevel.WARNING)
