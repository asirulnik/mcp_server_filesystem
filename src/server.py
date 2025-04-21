# src/server.py (Revised for Absolute Paths)

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional # Added Optional

import structlog
from mcp.server.fastmcp import FastMCP

# Import utility functions
from src.file_tools.directory_utils import list_files as list_files_util
from src.file_tools.directory_utils import find_files_spotlight, find_files_ripgrep
from src.file_tools.file_operations import read_file as read_file_util
from src.file_tools.file_operations import save_file as save_file_util
from src.file_tools.file_operations import append_file as append_file_util
from src.file_tools.file_operations import delete_file as delete_file_util
from src.file_tools.edit_file import edit_file as edit_file_util

# REMOVED: normalize_path import as it's no longer used

from src.log_utils import log_function_call

# Initialize loggers
logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)

# Create a FastMCP server instance
mcp = FastMCP("File System Service (Absolute Paths Mode)")

# REMOVED: _project_dir global variable
# REMOVED: set_project_dir function

def _validate_abs_path(path_str: str, operation: str) -> Path:
    """Helper to validate if a path string is a valid absolute path."""
    if not path_str or not isinstance(path_str, str):
        logger.error(f"{operation}: Invalid path parameter type: {type(path_str)}")
        raise ValueError(f"Path must be a non-empty string, got {type(path_str)}")
    try:
        path_obj = Path(path_str)
    except Exception as e:
         logger.error(f"{operation}: Could not create Path object from '{path_str}': {e}")
         raise ValueError(f"Invalid path format: {path_str}") from e

    if not path_obj.is_absolute():
        logger.error(f"{operation}: Path is not absolute: {path_str}")
        raise ValueError(f"Path must be absolute, got: {path_str}")
    return path_obj

@mcp.tool()
@log_function_call
def list_directory(abs_dir_path: str) -> List[str]:
    """
    List files and directories directly within the specified ABSOLUTE directory (non-recursive).

    Args:
        abs_dir_path: The ABSOLUTE path to the directory to list contents of.

    Returns:
        A list of ABSOLUTE paths for files and directories inside the specified directory.
    """
    try:
        path_obj = _validate_abs_path(abs_dir_path, "list_directory")
        logger.info(f"Listing non-recursive contents of absolute directory: {path_obj}")
        # Call util function with the absolute path object
        result = list_files_util(path_obj) # Pass Path object
        return result
    except Exception as e:
        logger.error(f"Error listing absolute directory '{abs_dir_path}': {str(e)}")
        raise

@mcp.tool()
@log_function_call
def read_file(abs_file_path: str) -> str:
    """
    Read the contents of a file specified by an ABSOLUTE path.

    Args:
        abs_file_path: ABSOLUTE path to the file to read.

    Returns:
        The contents of the file as a string.
    """
    try:
        path_obj = _validate_abs_path(abs_file_path, "read_file")
        logger.info(f"Reading file: {path_obj}")
        content = read_file_util(path_obj) # Pass Path object
        return content
    except Exception as e:
        logger.error(f"Error reading file '{abs_file_path}': {str(e)}")
        raise

@mcp.tool()
@log_function_call
def save_file(abs_file_path: str, content: str) -> bool:
    """
    Write content to a file specified by an ABSOLUTE path. **WARNING: For large text files (more than about 300 lines), write them in parts, stopping every 300 lines or so to ask user if he wants you to continue. For such files, start by using save_file to save the first 100 lines but then STOP and wait for the user to tell you to continue. Then, write the next 400 lines using append_file, and then stop and ask the user if he wants you to continue. Repeat the process of appending about 400 lines to the end of the file and stopping to ask the user if he wants you to continue in a loop until the whole file is written.**

    Args:
        abs_file_path: ABSOLUTE path to the file to write to.
        content: Content to write to the file.

    Returns:
        True if the file was written successfully.
    """
    try:
        path_obj = _validate_abs_path(abs_file_path, "save_file")

        # Basic content validation (remains useful)
        if content is None:
            logger.warning("Content is None, treating as empty string")
            content = ""
        if not isinstance(content, str):
            logger.error(f"Invalid content type: {type(content)}")
            raise ValueError(f"Content must be a string, got {type(content)}")

        logger.info(f"Writing to file: {path_obj}")
        success = save_file_util(path_obj, content) # Pass Path object
        return success
    except Exception as e:
        logger.error(f"Error writing to file '{abs_file_path}': {str(e)}")
        raise

@mcp.tool()
@log_function_call
def append_file(abs_file_path: str, content: str) -> bool:
    """
    Append content to the end of a file specified by an ABSOLUTE path.

    Args:
        abs_file_path: ABSOLUTE path to the file to append to.
        content: Content to append to the file.

    Returns:
        True if the content was appended successfully.
    """
    try:
        path_obj = _validate_abs_path(abs_file_path, "append_file")

        # Basic content validation
        if content is None:
            logger.warning("Content is None, treating as empty string")
            content = ""
        if not isinstance(content, str):
            logger.error(f"Invalid content type: {type(content)}")
            raise ValueError(f"Content must be a string, got {type(content)}")

        logger.info(f"Appending to file: {path_obj}")
        success = append_file_util(path_obj, content) # Pass Path object
        return success
    except Exception as e:
        logger.error(f"Error appending to file '{abs_file_path}': {str(e)}")
        raise

@mcp.tool()
@log_function_call
def delete_this_file(abs_file_path: str) -> bool:
    """
    Delete a specified file from the filesystem using an ABSOLUTE path.

    Args:
        abs_file_path: ABSOLUTE path to the file to delete.

    Returns:
        True if the file was deleted successfully.
    """
    try:
        path_obj = _validate_abs_path(abs_file_path, "delete_this_file")
        logger.info(f"Deleting file: {path_obj}")
        success = delete_file_util(path_obj) # Pass Path object
        logger.info(f"File deleted successfully: {path_obj}")
        return success
    except Exception as e:
        logger.error(f"Error deleting file '{abs_file_path}': {str(e)}")
        raise

@mcp.tool()
@log_function_call
def edit_file(
    abs_file_path: str,
    edits: List[Dict[str, str]],
    dry_run: bool = False,
    options: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Make selective edits to a file specified by an ABSOLUTE path.

    Args:
        abs_file_path: ABSOLUTE path to the file to edit.
        edits: List of edit operations (old_text, new_text).
        dry_run: Preview changes without applying (default: False).
        options: Optional formatting settings (e.g., preserve_indentation).

    Returns:
        Detailed diff and match information including success status.
    """
    try:
        path_obj = _validate_abs_path(abs_file_path, "edit_file")

        # Basic validation for edits and options (remains useful)
        if not isinstance(edits, list) or not edits:
            logger.error(f"Invalid edits parameter: {edits}")
            raise ValueError(f"Edits must be a non-empty list")

        normalized_edits = []
        for i, edit in enumerate(edits):
            if not isinstance(edit, dict):
                raise ValueError(f"Edit #{i} must be a dictionary, got {type(edit)}")
            if "old_text" not in edit or "new_text" not in edit:
                missing = ", ".join([f for f in ["old_text", "new_text"] if f not in edit])
                raise ValueError(f"Edit #{i} is missing required field(s): {missing}")
            normalized_edits.append(
                {"old_text": edit["old_text"], "new_text": edit["new_text"]}
            )

        normalized_options = {}
        if options:
            for opt in ["preserve_indentation", "normalize_whitespace"]:
                if opt in options:
                    normalized_options[opt] = options[opt]

        logger.info(f"Editing file: {path_obj}, dry_run: {dry_run}")
        # Call util function with absolute Path object, remove project_dir
        return edit_file_util(
            path_obj, # Pass Path object
            normalized_edits,
            dry_run=dry_run,
            options=normalized_options,
        )
    except Exception as e:
        logger.error(f"Error editing file '{abs_file_path}': {str(e)}")
        raise


# --- Spotlight and Ripgrep Tools (Using absolute paths) ---

@mcp.tool()
@log_function_call
def find_files_spotlight_tool(query: str, abs_search_dir: str) -> List[str]:
    """
    Uses macOS Spotlight (mdfind) to search for files within a specified ABSOLUTE directory.

    Args:
        query: The Spotlight query string.
        abs_search_dir: The ABSOLUTE root directory path to limit the search to.

    Returns:
        A list of ABSOLUTE file paths matching the query within the directory.
    """
    try:
        path_obj = _validate_abs_path(abs_search_dir, "find_files_spotlight_tool")
        logger.info(f"Searching Spotlight in '{path_obj}' with query: '{query}'")
        results = find_files_spotlight(query, path_obj) # Pass Path object
        return results
    except Exception as e:
        logger.error(f"Error during Spotlight search in '{abs_search_dir}': {str(e)}")
        raise


@mcp.tool()
@log_function_call
def find_files_ripgrep_tool(
    query: str,
    abs_search_dir: str,
    case_sensitive: Optional[bool] = None,
    literal: bool = False,
) -> List[Dict[str, Any]]:
    """
    Uses Ripgrep (rg) to search file contents recursively within a specified ABSOLUTE directory.

    Args:
        query: The regex pattern (or literal string if literal=True) to search for.
        abs_search_dir: The ABSOLUTE root directory path to search within.
        case_sensitive: Control case sensitivity. None=smart case (default).
        literal: If True, treat query as a literal string (-F flag).

    Returns:
        A list of match dictionaries (containing absolute file paths).
    """
    try:
        path_obj = _validate_abs_path(abs_search_dir, "find_files_ripgrep_tool")
        logger.info(f"Searching Ripgrep in '{path_obj}' with query: '{query}'")
        results = find_files_ripgrep(query, path_obj, case_sensitive, literal) # Pass Path object
        return results
    except Exception as e:
        logger.error(f"Error during Ripgrep search in '{abs_search_dir}': {str(e)}")
        raise

# --- Revised run_server ---

@log_function_call
def run_server() -> None: # Removed project_dir parameter
    """Run the MCP server in absolute path mode."""
    logger.debug("Entering run_server function (absolute path mode)")
    structured_logger.debug(
        "Entering run_server function (absolute path mode)"
    )

    # REMOVED: set_project_dir call

    logger.info("Starting MCP server (absolute path mode)")
    structured_logger.info("Starting MCP server (absolute path mode)")
    logger.debug("About to call mcp.run()")
    structured_logger.debug("About to call mcp.run()")
    mcp.run()
    logger.debug(
        "After mcp.run() call - this line will only execute if mcp.run() returns"
    )