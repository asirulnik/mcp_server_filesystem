# src/file_tools/directory_utils.py (Revised for Absolute Paths)
"""
Directory utilities for file operations using absolute paths.

Provides:
- Non-recursive directory listing (list_files).
- macOS Spotlight search via mdfind (find_files_spotlight).
- Fast content search via ripgrep (find_files_ripgrep).
"""

import json
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# REMOVED: from .path_utils import normalize_path

logger = logging.getLogger(__name__)


def list_files(abs_directory_path: Path) -> List[str]:
    """
    List files and directories directly within the specified ABSOLUTE directory (non-recursive).

    Args:
        abs_directory_path: The ABSOLUTE Path object for the directory to list contents of.

    Returns:
        A list of ABSOLUTE string paths for files and directories inside the specified directory.

    Raises:
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path points to a file instead of a directory.
    """
    try:
        # Input is now already an absolute Path object, validated by the caller (_validate_abs_path)
        if not abs_directory_path.exists():
            raise FileNotFoundError(f"Directory '{abs_directory_path}' does not exist")

        if not abs_directory_path.is_dir():
            raise NotADirectoryError(f"Path '{abs_directory_path}' is not a directory")

        logger.info(f"Listing non-recursive contents of directory: {abs_directory_path}")

        results = []
        # Use os.scandir for efficient non-recursive listing
        with os.scandir(abs_directory_path) as it:
            for entry in it:
                # Return absolute paths as strings
                results.append(str(Path(entry.path))) # Use entry.path for absolute path

        logger.info(f"Found {len(results)} items in {abs_directory_path}")
        return results

    except (FileNotFoundError, NotADirectoryError) as e:
        logger.error(f"Error listing directory '{abs_directory_path}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing directory '{abs_directory_path}': {e}")
        # Re-raise unexpected errors
        raise


def find_files_spotlight(query: str, abs_search_dir: Path) -> List[str]:
    """
    Uses macOS Spotlight (mdfind) to search for files within the specified ABSOLUTE directory.
    Best suited for finding files by metadata (name, kind, dates, tags).

    Args:
        query: The Spotlight query string.
        abs_search_dir: The ABSOLUTE Path object for the directory path to limit the search to.

    Returns:
        A list of ABSOLUTE file paths matching the query within the project directory.

    Raises:
        RuntimeError: If not running on macOS or if mdfind command fails.
    """
    if platform.system() != "Darwin":
        logger.error("Attempted to use mdfind on non-macOS system.")
        raise RuntimeError("Spotlight search (mdfind) is only available on macOS.")

    # Use the provided absolute Path object directly
    command = ["mdfind", "-onlyin", str(abs_search_dir), query]

    logger.info(f"Running Spotlight search in '{abs_search_dir}' with query: '{query}'")
    logger.debug(f"Executing command: {' '.join(command)}")

    try:
        # Execute the command
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )

        # Process the output - lines are absolute paths
        output_lines = process.stdout.strip().splitlines()

        # Optional: Filter results to ensure they are strictly within the search directory
        absolute_paths = []
        for line in output_lines:
            try:
                result_path = Path(line)
                # Check if the result is within the requested directory
                if result_path.is_relative_to(abs_search_dir):
                     absolute_paths.append(str(result_path))
                else:
                     logger.warning(f"mdfind returned path outside requested search dir '{abs_search_dir}', skipping: {line}")
            except ValueError: # is_relative_to can raise ValueError on Windows for different drives
                 logger.warning(f"Could not verify if path '{line}' is relative to '{abs_search_dir}', skipping.")
            except Exception as path_err:
                 logger.warning(f"Error processing mdfind result path '{line}': {path_err}")


        logger.info(f"Spotlight search found {len(absolute_paths)} items.")
        return absolute_paths

    except subprocess.CalledProcessError as e:
        error_message = f"mdfind command failed with exit code {e.returncode}."
        stderr_output = e.stderr.strip()
        if stderr_output:
            error_message += f" Stderr: {stderr_output}"
        logger.error(error_message)
        raise RuntimeError(error_message) from e
    except FileNotFoundError:
        logger.error("mdfind command not found. Ensure Spotlight is available.")
        raise RuntimeError("mdfind command not found.") from None
    except Exception as e:
        logger.error(f"Unexpected error during Spotlight search: {e}")
        raise RuntimeError(f"Unexpected error during Spotlight search: {e}") from e


def find_files_ripgrep(
    query: str,
    abs_search_dir: Path,
    case_sensitive: Optional[bool] = None,
    literal: bool = False,
) -> List[Dict[str, Any]]:
    """
    Uses Ripgrep (rg) to search file contents recursively within the specified ABSOLUTE directory.
    Best suited for finding text/code snippets within files.

    Args:
        query: The regex pattern (or literal string if literal=True) to search for.
        abs_search_dir: The ABSOLUTE Path object for the directory path to search within.
        case_sensitive: Control case sensitivity. None=smart case (default).
        literal: If True, treat the query as a literal string (-F flag).

    Returns:
        A list of dictionaries, where each dictionary represents a match and contains
        ABSOLUTE file paths.

    Raises:
        RuntimeError: If the rg command fails or is not found.
    """

    # Basic command using the absolute Path object
    command = ["rg", "--json", query, str(abs_search_dir)]

    # Add flags based on arguments
    if literal:
        command.insert(1, "-F") # Use fixed strings
    if case_sensitive is True:
        command.insert(1, "-s") # Case sensitive
    elif case_sensitive is False:
        command.insert(1, "-i") # Ignore case
    # If case_sensitive is None, rg defaults to smart case, so no flag needed

    logger.info(f"Running Ripgrep search in '{abs_search_dir}' with query: '{query}' (literal={literal}, case_sensitive={case_sensitive})")
    logger.debug(f"Executing command: {' '.join(command)}")

    try:
        # Execute the command
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )

        matches = []
        # Process each JSON object line
        for line in process.stdout.strip().splitlines():
            try:
                data = json.loads(line)
                if data.get("type") == "match":
                    match_info = data.get("data", {})
                    file_path_str = match_info.get("path", {}).get("text")
                    line_num = match_info.get("line_number")
                    match_text = match_info.get("lines", {}).get("text", "").rstrip('\n')
                    absolute_offset = match_info.get("absolute_offset")
                    submatches = match_info.get("submatches", [])

                    if file_path_str and line_num is not None:
                        # Paths returned by rg are already absolute in this usage
                        abs_file_path = Path(file_path_str)
                        # Optional: Double-check path is within scope
                        try:
                            if abs_file_path.is_relative_to(abs_search_dir):
                                matches.append({
                                    "file_path": str(abs_file_path), # Return absolute path string
                                    "line_number": line_num,
                                    "match_text": match_text,
                                    "absolute_offset": absolute_offset,
                                    "submatches": submatches
                                })
                            else:
                                logger.warning(f"rg returned path outside requested search dir '{abs_search_dir}', skipping: {file_path_str}")
                        except ValueError:
                             logger.warning(f"Could not verify if path '{file_path_str}' is relative to '{abs_search_dir}', skipping.")
                        except Exception as path_err:
                             logger.warning(f"Error processing rg result path '{file_path_str}': {path_err}")

            except json.JSONDecodeError as json_err:
                logger.warning(f"Failed to parse JSON line from rg output: {json_err}. Line: '{line}'")
            except Exception as parse_err:
                logger.warning(f"Error processing rg match data: {parse_err}. Data: '{data if 'data' in locals() else 'N/A'}'")


        logger.info(f"Ripgrep search found {len(matches)} matches.")
        return matches

    except subprocess.CalledProcessError as e:
        error_message = f"Ripgrep (rg) command failed with exit code {e.returncode}."
        stderr_output = e.stderr.strip()
        if stderr_output:
            error_message += f" Stderr: {stderr_output}"
        logger.error(error_message)
        raise RuntimeError(error_message) from e
    except FileNotFoundError:
        logger.error("Ripgrep (rg) command not found. Please ensure it is installed and in PATH.")
        raise RuntimeError("Ripgrep (rg) command not found.") from None
    except Exception as e:
        logger.error(f"Unexpected error during Ripgrep search: {e}")
        raise RuntimeError(f"Unexpected error during Ripgrep search: {e}") from e