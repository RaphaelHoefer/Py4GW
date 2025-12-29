"""
Base class for Py4GW widgets.

Provides common window management functionality to reduce code duplication.
"""

from typing import Tuple, Optional
import PyImGui

from .config import ConfigManager, ConfigType


class WidgetBase:
    """
    Base class for widgets with common window management.

    Handles:
    - Window position persistence
    - Window state (collapsed, etc.)
    - First-run initialization
    - Auto-save of window state

    Usage:
        class MyWidget(WidgetBase):
            def __init__(self):
                super().__init__("MyWidget")

            def draw(self):
                if self.begin_window():
                    # Draw your widget content here
                    PyImGui.text("Hello World")
                self.end_window()
    """

    def __init__(
        self,
        module_name: str,
        default_pos: Tuple[int, int] = (100, 100),
        default_size: Tuple[int, int] = (0, 0),
        config_type: ConfigType = ConfigType.INI,
        save_interval_ms: int = 1000
    ):
        """
        Initialize the widget base.

        Args:
            module_name: Unique name for the widget
            default_pos: Default window position (x, y)
            default_size: Default window size (width, height). Use (0, 0) for auto-size.
            config_type: Configuration file type for persistence
            save_interval_ms: How often to save window state (in milliseconds)
        """
        self.module_name = module_name
        self.default_pos = default_pos
        self.default_size = default_size
        self.save_interval_ms = save_interval_ms

        # Window state
        self._first_run = True
        self._window_x, self._window_y = default_pos
        self._window_collapsed = False
        self._current_pos: Tuple[int, int] = default_pos
        self._last_save_time = 0

        # Configuration
        self._config = ConfigManager(f"widget_{module_name}", config_type)
        self._load_window_state()

    def _load_window_state(self) -> None:
        """Load window state from configuration."""
        if self._config.load():
            self._window_x = self._config.get_int(f"{self.module_name}.x", self.default_pos[0])
            self._window_y = self._config.get_int(f"{self.module_name}.y", self.default_pos[1])
            self._window_collapsed = self._config.get_bool(f"{self.module_name}.collapsed", False)

    def _save_window_state(self) -> None:
        """Save window state to configuration."""
        self._config.set(f"{self.module_name}.x", self._window_x)
        self._config.set(f"{self.module_name}.y", self._window_y)
        self._config.set(f"{self.module_name}.collapsed", self._window_collapsed)
        self._config.save()

    def begin_window(
        self,
        flags: int = PyImGui.WindowFlags.AlwaysAutoResize,
        closable: bool = False
    ) -> bool:
        """
        Begin the widget window.

        Args:
            flags: ImGui window flags
            closable: Whether the window has a close button

        Returns:
            True if window is open and content should be drawn
        """
        # Set initial position on first run
        if self._first_run:
            PyImGui.set_next_window_pos(self._window_x, self._window_y)
            if self._window_collapsed:
                PyImGui.set_next_window_collapsed(True, 0)
            if self.default_size != (0, 0):
                PyImGui.set_next_window_size(*self.default_size)
            self._first_run = False

        # Begin the window
        if closable:
            is_open = PyImGui.begin(self.module_name, flags)
        else:
            is_open = PyImGui.begin(self.module_name, flags)

        return is_open

    def end_window(self) -> None:
        """
        End the widget window and handle state saving.

        Call this after begin_window(), regardless of whether content was drawn.
        """
        # Get current state
        new_collapsed = PyImGui.is_window_collapsed()
        new_pos = PyImGui.get_window_pos()

        # Check if state changed
        state_changed = (
            new_pos[0] != self._window_x or
            new_pos[1] != self._window_y or
            new_collapsed != self._window_collapsed
        )

        if state_changed:
            self._window_x = int(new_pos[0])
            self._window_y = int(new_pos[1])
            self._window_collapsed = new_collapsed
            self._save_window_state()

        self._current_pos = (self._window_x, self._window_y)

        PyImGui.end()

    @property
    def window_position(self) -> Tuple[int, int]:
        """Get the current window position."""
        return self._current_pos

    @property
    def is_collapsed(self) -> bool:
        """Check if the window is collapsed."""
        return self._window_collapsed

    def reset_position(self) -> None:
        """Reset window to default position."""
        self._window_x, self._window_y = self.default_pos
        self._first_run = True
        self._save_window_state()
