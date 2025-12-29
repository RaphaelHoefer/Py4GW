#region MultiThreading
import threading
from .Console import ConsoleLog, Console
import time
import ctypes


class MultiThreading:
    """
    Thread manager with graceful shutdown support.

    Provides thread lifecycle management with:
    - Stop events for graceful shutdown
    - Watchdog for timeout detection
    - Keepalive mechanism for health monitoring
    """

    def __init__(self, timeout=1.0, log_actions=False):
        """Initialize thread manager."""
        self.threads = {}
        self.log_actions = log_actions
        self.lock = threading.Lock()
        self.timeout = timeout
        self.watchdog_thread = None
        self.watchdog_active = False

    def add_thread(self, name, execute_fn, *args, **kwargs):
        """Add and immediately start a thread."""
        with self.lock:
            if name in self.threads:
                ConsoleLog("MultiThreading", f"Thread '{name}' already exists.", Console.MessageType.Warning)
                return

            # Prepare thread entry with stop event for graceful shutdown
            last_keepalive = time.time()
            stop_event = threading.Event()
            self.threads[name] = {
                "thread": None,
                "target_fn": execute_fn,
                "args": args,
                "kwargs": kwargs,
                "last_keepalive": last_keepalive,
                "stop_event": stop_event
            }

        # Start thread immediately
        self.start_thread(name)

    def start_thread(self, name):
        """Start the thread."""
        with self.lock:
            if name not in self.threads:
                ConsoleLog("MultiThreading", f"Thread '{name}' does not exist.", Console.MessageType.Warning)
                return

            thread_info = self.threads[name]
            thread = thread_info.get("thread")
            if thread and thread.is_alive():
                ConsoleLog("MultiThreading", f"Thread '{name}' already running.", Console.MessageType.Warning)
                return

            # Create a NEW thread object every time we start
            execute_fn = thread_info["target_fn"]
            args = thread_info["args"]
            kwargs = thread_info["kwargs"]

            def wrapped_target(*args, **kwargs):
                if self.log_actions:
                    ConsoleLog("MultiThreading", f"Thread '{name}' running.", Console.MessageType.Info)
                try:
                    execute_fn(*args, **kwargs)
                except SystemExit:
                    if self.log_actions:
                        ConsoleLog("MultiThreading", f"Thread '{name}' forcefully exited.", Console.MessageType.Info)
                except Exception as e:
                    ConsoleLog("MultiThreading", f"Thread '{name}' exception: {str(e)}", Console.MessageType.Error)
                finally:
                    if self.log_actions:
                        ConsoleLog("MultiThreading", f"Thread '{name}' exited.", Console.MessageType.Info)

            new_thread = threading.Thread(target=wrapped_target, args=args, kwargs=kwargs, daemon=True)
            self.threads[name]["thread"] = new_thread
            self.threads[name]["last_keepalive"] = time.time()
            new_thread.start()

            if self.log_actions:
                ConsoleLog("MultiThreading", f"Thread '{name}' started.", Console.MessageType.Success)

    def update_keepalive(self, name):
        """Update keepalive timestamp."""
        with self.lock:
            if name in self.threads:
                self.threads[name]["last_keepalive"] = time.time()
                
    def update_all_keepalives(self):
        """Update keepalive timestamp for all threads except the watchdog."""
        current_time = time.time()
        with self.lock:
            for name, info in self.threads.items():
                if name == "watchdog":  # Optional: skip watchdog
                    continue
                self.threads[name]["last_keepalive"] = current_time


    def stop_thread(self, name, graceful_timeout: float = 2.0):
        """
        Stop a thread, preferring graceful shutdown.

        Args:
            name: Name of the thread to stop
            graceful_timeout: Seconds to wait for graceful shutdown before forcing
        """
        with self.lock:
            if name not in self.threads:
                if self.log_actions:
                    ConsoleLog("MultiThreading", f"Thread '{name}' does not exist.", Console.MessageType.Warning)
                return

            thread_info = self.threads[name]
            thread = thread_info.get("thread")
            stop_event = thread_info.get("stop_event")

        # Signal the thread to stop gracefully
        if stop_event:
            stop_event.set()

        if thread and thread.is_alive():
            if self.log_actions:
                ConsoleLog("MultiThreading", f"Requesting graceful stop for thread '{name}'.", Console.MessageType.Info)

            # Wait for graceful shutdown
            thread.join(timeout=graceful_timeout)

            # If still alive after timeout, force stop as last resort
            if thread.is_alive():
                if self.log_actions:
                    ConsoleLog("MultiThreading", f"Force stopping thread '{name}' (graceful shutdown timed out).", Console.MessageType.Warning)
                try:
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), ctypes.py_object(SystemExit))
                    time.sleep(0.1)
                except (ValueError, SystemError):
                    # Thread may have already exited
                    pass

        with self.lock:
            if name in self.threads:
                del self.threads[name]

        if self.log_actions:
            ConsoleLog("MultiThreading", f"Thread '{name}' stopped and removed.", Console.MessageType.Info)

    def stop_all_threads(self):
        """Stop all managed threads."""
        with self.lock:
            thread_names = list(self.threads.keys())

        for name in thread_names:
            self.stop_thread(name)

    def should_stop(self, name: str) -> bool:
        """
        Check if a thread should stop.

        Threads can call this periodically to check if they should exit gracefully.

        Args:
            name: Name of the thread

        Returns:
            True if the thread should stop, False otherwise
        """
        with self.lock:
            if name not in self.threads:
                return True
            stop_event = self.threads[name].get("stop_event")
            if stop_event:
                return stop_event.is_set()
        return False

    def get_stop_event(self, name: str) -> threading.Event:
        """
        Get the stop event for a thread.

        Threads can use this to wait on the stop event or check it directly.

        Args:
            name: Name of the thread

        Returns:
            The threading.Event for this thread, or a new set event if not found
        """
        with self.lock:
            if name in self.threads:
                return self.threads[name].get("stop_event", threading.Event())
        # Return a set event if thread not found (signals should stop)
        event = threading.Event()
        event.set()
        return event




    def check_timeouts(self):
        """Watchdog force-stops expired threads."""
        current_time = time.time()
        expired = []
        with self.lock:
            for name, info in self.threads.items():
                if current_time - info["last_keepalive"] > self.timeout:
                    expired.append(name)

        for name in expired:
            ConsoleLog("MultiThreading", f"Thread '{name}' keepalive expired, force stopping.", Console.MessageType.Warning)
            self.stop_thread(name)


    def start_watchdog(self, main_thread_name):
        if self.watchdog_thread and self.watchdog_thread.is_alive():
            ConsoleLog("MultiThreading", "Watchdog already running.", Console.MessageType.Warning)
            return

        self.watchdog_active = True

        def watchdog_fn():
            from ..Map import Map
            if self.log_actions:
                ConsoleLog("Watchdog", "Watchdog started.", Console.MessageType.Info)
            while self.watchdog_active:
                current_time = time.time()
                expired_threads = []

                if Map.IsMapLoading():
                    time.sleep(3)
                    continue
                else:
                    with self.lock:
                        for name, info in self.threads.items():
                            if name == "watchdog":
                                continue

                            last_keepalive = info["last_keepalive"]
                            if current_time - last_keepalive > self.timeout:
                                expired_threads.append(name)

                # Expire threads
                for name in expired_threads:
                    if name != main_thread_name:
                        ConsoleLog("Watchdog", f"Thread '{name}' timed out. Stopping it.", Console.MessageType.Warning, log=True)
                        self.stop_thread(name)

                # MAIN_THREAD_NAME expired → stop all
                if main_thread_name in expired_threads:
                    ConsoleLog("Watchdog", f"Main thread '{main_thread_name}' timed out! Stopping all threads.", Console.MessageType.Error, log=True)
                    self.stop_all_threads()
                    break

                # Check if only watchdog remains
                with self.lock:
                    active_threads = [name for name in self.threads.keys() if name != "watchdog"]

                if not active_threads:
                    ConsoleLog("Watchdog", "No active threads left. Stopping watchdog.", Console.MessageType.Notice, log=True)
                    self.watchdog_active = False
                    break

                time.sleep(0.3)

            # Final cleanup
            with self.lock:
                if "watchdog" in self.threads:
                    del self.threads["watchdog"]
            ConsoleLog("Watchdog", "Watchdog stopped & cleaned.", Console.MessageType.Info)

        # Register watchdog in threads registry
        with self.lock:
            self.threads["watchdog"] = {
                "thread": None,
                "target_fn": None,
                "args": (),
                "kwargs": {},
                "last_keepalive": time.time()
            }

        # Start watchdog thread
        watchdog_thread = threading.Thread(target=watchdog_fn, daemon=True)
        self.watchdog_thread = watchdog_thread
        self.threads["watchdog"]["thread"] = watchdog_thread
        watchdog_thread.start()
        if self.log_actions:
            ConsoleLog("MultiThreading", "Watchdog thread started.", Console.MessageType.Success)

    def stop_watchdog(self):
        """Manually stop watchdog if needed."""
        self.watchdog_active = False

#endregion
