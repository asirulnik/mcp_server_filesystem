# src/file_tools/path_utils.py (Revised - normalize_path no longer needed)

"""Path utilities for file operations."""

import logging
# import os # No longer needed for normalize_path
# from pathlib import Path # No longer needed for normalize_path
# from typing import Optional # No longer needed for normalize_path

logger = logging.getLogger(__name__)

# The normalize_path function is no longer required when using absolute paths.
# You can remove it or leave it commented out for reference.

# def normalize_path(path: str, project_dir: Path) -> tuple[Path, str]:
#     """
#     Normalize a path to be relative to the project directory. (DEPRECATED)
#     """
#     # ... (original implementation) ...
#     pass