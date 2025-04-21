# src/file_tools/__init__.py (Revised)

"""File operation tools for MCP server."""

# Imports for functions still in use
from src.file_tools.directory_utils import list_files, find_files_spotlight, find_files_ripgrep # Assuming these are exposed if needed
from src.file_tools.edit_file import edit_file
from src.file_tools.file_operations import (
    append_file,
    delete_file,
    read_file,
    save_file,
    write_file, # write_file is an alias for save_file
)
# REMOVED: from src.file_tools.path_utils import normalize_path

# Define what functions are exposed when importing from this package
# Ensure this list only contains functions/classes that are actually defined and needed externally
__all__ = [
    # REMOVED: "normalize_path",
    "read_file",
    "write_file", # Keep alias if used
    "save_file",
    "append_file",
    "delete_file",
    "list_files",
    "edit_file",
    "find_files_spotlight", # Add if you intend to expose these via `from src.file_tools import *`
    "find_files_ripgrep", # Add if you intend to expose these via `from src.file_tools import *`
]