# src/main.py (Revised with Parent Process Check)

import argparse
import logging
import sys
import os # <-- Added
import threading # <-- Added
import time # <-- Added
from pathlib import Path

import structlog

# Import logging utilities
from src.log_utils import setup_logging
# Import run_server from server module
from src.server import run_server # Keep this import

# Create loggers
stdlogger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)

# --- Parent Process Monitoring ---
_parent_pid = None # Global to store the initial parent PID
_shutdown_event = threading.Event() # Event to signal shutdown

def check_parent_process():
    """Periodically checks if the original parent process is alive."""
    global _parent_pid
    if _parent_pid is None:
        stdlogger.error("Parent PID was not captured. Cannot monitor.")
        return # Should not happen if called correctly

    stdlogger.info(f"Monitoring parent process PID: {_parent_pid}")

    while not _shutdown_event.is_set():
        try:
            # On Unix-like systems (macOS, Linux), os.kill(pid, 0)
            # checks for process existence without sending a signal.
            # Raises ProcessLookupError if the process doesn't exist.
            os.kill(_parent_pid, 0)
            # stdlogger.debug(f"Parent process {_parent_pid} is still alive.")
        except ProcessLookupError:
            stdlogger.warning(f"Parent process {_parent_pid} not found. Initiating shutdown.")
            # Signal the main thread or directly exit
            # Option 1: Try to signal a graceful shutdown (if mcp supports it - needs investigation)
            #            e.g., somehow trigger mcp.stop() if possible
            # Option 2: Force exit (less clean, might skip cleanup)
            _shutdown_event.set() # Signal loop to stop
            os._exit(1) # Force exit the entire process immediately
            # Use sys.exit(1) if you want Python's cleanup, but os._exit is more forceful
            # break # Exit the loop after triggering exit
        except PermissionError:
            # We might lose permission if the parent changes user ID,
            # but it likely still exists. Log this edge case.
            stdlogger.warning(f"Permission denied checking parent process {_parent_pid}. Assuming alive.")
        except Exception as e:
            stdlogger.error(f"Error checking parent process {_parent_pid}: {e}", exc_info=True)
            # Decide whether to continue monitoring or exit on unexpected errors

        # Wait for 5 seconds before the next check, or until shutdown is signaled
        _shutdown_event.wait(5.0)

    stdlogger.info("Parent process monitoring thread finished.")

# --- End Parent Process Monitoring ---


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="MCP File System Server (Absolute Paths Mode)")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path for structured JSON logs. If not specified, only console logging is used.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the MCP server operating in absolute path mode.
    """
    global _parent_pid
    _parent_pid = os.getppid() # <-- Capture parent PID at the start

    stdlogger.debug("Starting main function (absolute paths mode)")

    # Parse command line arguments
    args = parse_args()

    # Configure logging
    setup_logging(args.log_level, args.log_file)

    stdlogger.debug("Logger initialized in main")
    structured_logger.debug(
        "Structured logger initialized in main", log_level=args.log_level
    )

    stdlogger.info(f"Starting MCP server in absolute path mode. SECURITY WARNING: No project directory constraint.")
    if args.log_file:
        structured_logger.info(
            "Starting MCP server (absolute path mode)",
            log_level=args.log_level,
            log_file=args.log_file,
        )

    # --- Start the monitoring thread ---
    monitor_thread = threading.Thread(target=check_parent_process, daemon=True)
    # daemon=True ensures the thread exits when the main program exits *cleanly*,
    # but our check_parent_process function forces exit anyway if the parent dies.
    monitor_thread.start()
    # ---

    try:
        # Run the server (this will block)
        run_server()
    except KeyboardInterrupt:
        stdlogger.info("KeyboardInterrupt received, stopping server.")
        # Signal the monitoring thread to stop if the main loop exits cleanly
        _shutdown_event.set()
    except Exception as e:
         stdlogger.error(f"Main server loop exited with error: {e}", exc_info=True)
         _shutdown_event.set() # Signal monitor thread to stop on error too
    finally:
        stdlogger.info("Server shutdown initiated.")
        # Wait briefly for the monitor thread to potentially finish its last check
        if monitor_thread.is_alive():
             monitor_thread.join(timeout=1.0) # Wait max 1 second
        stdlogger.info("Exiting main function.")


if __name__ == "__main__":
    main()