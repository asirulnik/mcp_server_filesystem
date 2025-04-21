# src/file_tools/file_operations.py (Revised for Absolute Paths)
"""File operations utilities using absolute paths."""

import logging
import os
import tempfile
from pathlib import Path

# REMOVED: from .path_utils import normalize_path

logger = logging.getLogger(__name__)


def read_file(abs_path: Path) -> str:
    """
    Read the contents of a file specified by an absolute Path object.

    Args:
        abs_path: Absolute Path object of the file to read.

    Returns:
        The contents of the file as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
        PermissionError: If access to the file is denied.
        ValueError: If the file contains invalid characters.
    """
    # Path validation (existence, is_file) still important
    if not abs_path.exists():
        logger.error(f"File not found: {abs_path}")
        raise FileNotFoundError(f"File '{abs_path}' does not exist")

    if not abs_path.is_file():
        logger.error(f"Path is not a file: {abs_path}")
        raise IsADirectoryError(f"Path '{abs_path}' is not a file")

    file_handle = None
    try:
        logger.debug(f"Reading file: {abs_path}")
        # Open using the absolute path directly
        file_handle = open(abs_path, "r", encoding="utf-8")
        content = file_handle.read()
        logger.debug(f"Successfully read {len(content)} bytes from {abs_path}")
        return content
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error while reading {abs_path}: {str(e)}")
        raise ValueError(
            f"File '{abs_path}' contains invalid characters. Ensure it's a valid text file."
        ) from e
    except PermissionError as e:
        logger.error(f"Permission denied reading file {abs_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error reading file {abs_path}: {str(e)}")
        raise
    finally:
        if file_handle is not None:
            file_handle.close()


def save_file(abs_path: Path, content: str) -> bool:
    """
    Write content to a file specified by an absolute Path object, atomically.

    Args:
        abs_path: Absolute Path object of the file to write to.
        content: Content to write to the file.

    Returns:
        True if the file was written successfully.

    Raises:
        PermissionError: If access to the file or directory is denied.
        ValueError: If content contains unencodable characters.
    """
    # Content validation remains the same
    if content is None: content = ""
    if not isinstance(content, str): raise ValueError(f"Content must be a string, got {type(content)}")

    # Create parent directory if it doesn't exist
    try:
        parent_dir = abs_path.parent
        if not parent_dir.exists():
            logger.info(f"Creating directory: {parent_dir}")
            parent_dir.mkdir(parents=True, exist_ok=True) # Use exist_ok=True
    except PermissionError as e:
        logger.error(f"Permission denied creating directory {parent_dir}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating directory {parent_dir}: {str(e)}")
        raise

    # Use a temporary file for atomic write
    temp_file_path_obj = None
    temp_file_handle = None
    try:
        # Create temp file in the same directory as the target
        # Use delete=False and manage cleanup manually for more control
        temp_file_handle = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=str(parent_dir), delete=False)
        temp_file_path_obj = Path(temp_file_handle.name)

        logger.debug(f"Writing to temporary file '{temp_file_path_obj}' for target '{abs_path}'")

        # Write content to temporary file
        try:
            temp_file_handle.write(content)
        except UnicodeEncodeError as e:
            logger.error(f"Unicode encode error while writing to temp file for {abs_path}: {str(e)}")
            raise ValueError("Content contains characters that cannot be encoded.") from e
        finally:
             if temp_file_handle: temp_file_handle.close() # Ensure file is closed before moving

        # Atomically replace the target file
        logger.debug(f"Atomically replacing {abs_path} with {temp_file_path_obj}")
        try:
            # os.replace is generally atomic on POSIX and handles Windows cases better
            os.replace(str(temp_file_path_obj), str(abs_path))
            temp_file_path_obj = None # Prevent deletion in finally block if replace succeeds
        except PermissionError as e:
             logger.error(f"Permission denied replacing file {abs_path}: {str(e)}")
             raise
        except Exception as e:
            logger.error(f"Error replacing file {abs_path}: {str(e)}")
            raise

        logger.debug(f"Successfully wrote {len(content)} bytes to {abs_path}")
        return True

    except Exception as e:
        logger.error(f"Error writing to file {abs_path}: {str(e)}")
        raise
    finally:
        # Clean up the temporary file if it still exists (i.e., if os.replace failed)
        if temp_file_path_obj and temp_file_path_obj.exists():
            try:
                logger.warning(f"Cleaning up leftover temporary file: {temp_file_path_obj}")
                temp_file_path_obj.unlink()
            except Exception as cleanup_e:
                logger.error(f"Failed to clean up temporary file {temp_file_path_obj}: {cleanup_e}")

# Keep write_file for backward compatibility
write_file = save_file


def append_file(abs_path: Path, content: str) -> bool:
    """
    Append content to the end of a file specified by an absolute Path object.

    Args:
        abs_path: Absolute Path object of the file to append to.
        content: Content to append to the file.

    Returns:
        True if the content was appended successfully.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
        PermissionError: If access to the file is denied.
        ValueError: If content is invalid.
    """
    # Content validation
    if content is None: content = ""
    if not isinstance(content, str): raise ValueError(f"Content must be a string, got {type(content)}")

    # Check if the file exists and is a file (read_file will also check this)
    if not abs_path.exists():
        logger.error(f"File not found: {abs_path}")
        raise FileNotFoundError(f"File '{abs_path}' does not exist for appending")

    if not abs_path.is_file():
        logger.error(f"Path is not a file: {abs_path}")
        raise IsADirectoryError(f"Path '{abs_path}' is not a file")

    try:
        # Appending is simpler, can often be done directly
        # Using 'a' mode handles file creation implicitly if needed, but we check existence first
        logger.debug(f"Appending {len(content)} bytes to {abs_path}")
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(content)
        logger.debug(f"Successfully appended to {abs_path}")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied appending to file {abs_path}: {str(e)}")
        raise
    except UnicodeEncodeError as e:
         logger.error(f"Unicode encode error while appending to {abs_path}: {str(e)}")
         raise ValueError("Content contains characters that cannot be encoded.") from e
    except Exception as e:
        logger.error(f"Error appending to file {abs_path}: {str(e)}")
        raise


def delete_file(abs_path: Path) -> bool:
    """
    Delete a file specified by an absolute Path object.

    Args:
        abs_path: Absolute Path object of the file to delete.

    Returns:
        True if the file was deleted successfully.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
        PermissionError: If access to the file is denied.
    """
    # Path validation
    if not abs_path.exists():
        logger.error(f"File not found: {abs_path}")
        raise FileNotFoundError(f"File '{abs_path}' does not exist")

    if not abs_path.is_file():
        logger.error(f"Path is not a file: {abs_path}")
        raise IsADirectoryError(f"Path '{abs_path}' is not a file")

    try:
        logger.debug(f"Deleting file: {abs_path}")
        abs_path.unlink()
        logger.debug(f"Successfully deleted file: {abs_path}")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied when deleting file {abs_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting file {abs_path}: {str(e)}")
        raise