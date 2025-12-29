"""
Standardized event handling for Py4GW bots.

Provides common event handlers for death, party wipe, and other game events.
"""

from typing import TYPE_CHECKING, Callable, Optional, Generator

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting


class BotEventHandler:
    """
    Standardized event handling for common bot scenarios.

    Usage:
        # In your bot's event handling:
        def on_death(bot):
            yield from BotEventHandler.handle_death_recovery(
                bot,
                jump_to_state="[H]Initialize Bot_1"
            )

        # Or use the simpler approach:
        BotEventHandler.setup_death_handler(bot, "[H]Initialize Bot_1")
    """

    @staticmethod
    def handle_death_recovery(
        bot: "Botting",
        jump_to_state: Optional[str] = None,
        recovery_delay_ms: int = 8000
    ) -> Generator:
        """
        Standard death recovery routine.

        Args:
            bot: The bot instance
            jump_to_state: Optional state name to jump to after recovery
            recovery_delay_ms: Delay before resuming (default 8 seconds)

        Yields:
            Coroutine steps for the recovery process
        """
        from Py4GWCoreLib import Routines

        # Pause the FSM
        bot.Properties.ApplyNow("pause_on_danger", "active", False)
        bot.Properties.ApplyNow("halt_on_death", "active", True)

        # Wait for recovery delay
        yield from Routines.Yield.wait(recovery_delay_ms)

        # Get FSM and jump to state if specified
        fsm = bot.config.FSM
        if jump_to_state:
            fsm.jump_to_state_by_name(jump_to_state)

        # Resume the FSM
        fsm.resume()

    @staticmethod
    def handle_party_wipe(
        bot: "Botting",
        recovery_fn: Optional[Callable] = None
    ) -> Generator:
        """
        Standard party wipe handling routine.

        Args:
            bot: The bot instance
            recovery_fn: Optional recovery function to call after wipe

        Yields:
            Coroutine steps for the wipe handling process
        """
        from Py4GWCoreLib import Routines, GLOBAL_CACHE

        # Wait until player is no longer dead or map becomes invalid
        while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            yield from Routines.Yield.wait(1000)

            # Check if map is still valid
            if not Routines.Checks.Map.MapValid():
                bot.config.FSM.resume()
                return

        # Call recovery function if provided
        if recovery_fn:
            yield from recovery_fn(bot)

    @staticmethod
    def handle_map_change(
        bot: "Botting",
        expected_map_id: Optional[int] = None,
        on_wrong_map: Optional[Callable] = None
    ) -> Generator:
        """
        Handle map change events.

        Args:
            bot: The bot instance
            expected_map_id: The map ID we expect to be on
            on_wrong_map: Function to call if we're on the wrong map

        Yields:
            Coroutine steps for map change handling
        """
        from Py4GWCoreLib import Routines, GLOBAL_CACHE

        # Wait for map to finish loading
        while GLOBAL_CACHE.Map.IsMapLoading():
            yield from Routines.Yield.wait(500)

        # Check if we're on the expected map
        if expected_map_id is not None:
            current_map = GLOBAL_CACHE.Map.GetMapID()
            if current_map != expected_map_id and on_wrong_map:
                yield from on_wrong_map(bot)

    @staticmethod
    def wait_for_combat_end(bot: "Botting", timeout_ms: int = 60000) -> Generator:
        """
        Wait until combat ends or timeout.

        Args:
            bot: The bot instance
            timeout_ms: Maximum time to wait (default 60 seconds)

        Yields:
            Coroutine steps for waiting
        """
        from Py4GWCoreLib import Routines

        elapsed = 0
        check_interval = 500

        while elapsed < timeout_ms:
            if not Routines.Checks.Combat.InCombat():
                return

            yield from Routines.Yield.wait(check_interval)
            elapsed += check_interval

    @staticmethod
    def setup_death_handler(
        bot: "Botting",
        jump_to_state: Optional[str] = None,
        handler_name: str = "OnDeath"
    ) -> None:
        """
        Set up a death handler coroutine on the bot's FSM.

        Args:
            bot: The bot instance
            jump_to_state: State to jump to after recovery
            handler_name: Name for the coroutine handler
        """
        def death_handler():
            return BotEventHandler.handle_death_recovery(bot, jump_to_state)

        fsm = bot.config.FSM
        fsm.pause()
        fsm.AddManagedCoroutine(handler_name, death_handler)

    @staticmethod
    def setup_wipe_handler(
        bot: "Botting",
        recovery_fn: Optional[Callable] = None,
        handler_name: str = "OnPartyWipe"
    ) -> None:
        """
        Set up a party wipe handler coroutine on the bot's FSM.

        Args:
            bot: The bot instance
            recovery_fn: Optional recovery function
            handler_name: Name for the coroutine handler
        """
        def wipe_handler():
            return BotEventHandler.handle_party_wipe(bot, recovery_fn)

        fsm = bot.config.FSM
        fsm.pause()
        fsm.AddManagedCoroutine(handler_name, wipe_handler)
