"""
Custom exception hierarchy for Py4GW.

This module provides a structured exception hierarchy for better error handling
and debugging across the Py4GW codebase.
"""


class Py4GWError(Exception):
    """Base exception for all Py4GW errors."""
    pass


class AgentError(Py4GWError):
    """Exception raised for agent-related errors."""
    pass


class InvalidAgentError(AgentError):
    """Exception raised when an agent ID is invalid."""
    def __init__(self, agent_id: int, message: str = None):
        self.agent_id = agent_id
        self.message = message or f"Invalid agent ID: {agent_id}"
        super().__init__(self.message)


class PartyError(Py4GWError):
    """Exception raised for party-related errors."""
    pass


class InventoryError(Py4GWError):
    """Exception raised for inventory-related errors."""
    pass


class ItemError(Py4GWError):
    """Exception raised for item-related errors."""
    pass


class SkillError(Py4GWError):
    """Exception raised for skill-related errors."""
    pass


class MapError(Py4GWError):
    """Exception raised for map-related errors."""
    pass


class UIError(Py4GWError):
    """Exception raised for UI-related errors."""
    pass


class CacheError(Py4GWError):
    """Exception raised for cache-related errors."""
    pass


class ConfigError(Py4GWError):
    """Exception raised for configuration-related errors."""
    pass


class ThreadingError(Py4GWError):
    """Exception raised for threading-related errors."""
    pass


class TimeoutError(Py4GWError):
    """Exception raised when an operation times out."""
    pass


class ValidationError(Py4GWError):
    """Exception raised for validation failures."""
    pass
