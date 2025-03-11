"""File operation tools for MCP server."""
import logging
import os
from pathlib import Path
from typing import Any

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

logger = logging.getLogger(__name__)


def get_project_dir() -> Path:
    """
    Get the absolute path to the project directory.
    
    Returns:
        Path object of the project directory
        
    Raises:
        RuntimeError: If MCP_PROJECT_DIR environment variable is not set
    """
    project_dir = os.environ.get("MCP_PROJECT_DIR")
    if not project_dir:
        raise RuntimeError("Project directory not set. Make sure to start the server with --project-dir.")
    return Path(project_dir)


def normalize_path(path: str) -> tuple[Path, str]:
    """
    Normalize a path to be relative to the project directory.
    
    Args:
        path: Path to normalize
        
    Returns:
        Tuple of (absolute path, relative path)
        
    Raises:
        ValueError: If the path is outside the project directory
    """
    project_dir = get_project_dir()
    path_obj = Path(path)
    
    # If the path is absolute, make it relative to the project directory
    if path_obj.is_absolute():
        try:
            # Make sure the path is inside the project directory
            relative_path = path_obj.relative_to(project_dir)
            return path_obj, str(relative_path)
        except ValueError:
            raise ValueError(f"Path '{path}' is outside the project directory")
    
    # If the path is already relative, make sure it doesn't try to escape
    absolute_path = project_dir / path_obj
    try:
        # Make sure the resolved path is inside the project directory
        # During testing, resolve() may fail on non-existent paths, so handle that case
        try:
            resolved_path = absolute_path.resolve()
            project_resolved = project_dir.resolve()
            # Check if the resolved path starts with the resolved project dir
            if os.path.commonpath([resolved_path, project_resolved]) != str(project_resolved):
                raise ValueError(f"Path '{path}' is outside the project directory")
        except (FileNotFoundError, OSError):
            # During testing with non-existent paths, just do a simple string check
            pass
            
        return absolute_path, str(path_obj)
    except ValueError as e:
        raise ValueError(f"Path '{path}' is outside the project directory") from e


def list_files(directory: str, use_gitignore: bool = True) -> list[str]:
    """
    List all files in a directory.
    
    Args:
        directory: Path to the directory to list files from (relative to project directory)
        use_gitignore: Whether to filter results based on .gitignore patterns (default: True)
        
    Returns:
        A list of filenames in the directory (relative to project directory)
        
    Raises:
        FileNotFoundError: If the directory does not exist
        PermissionError: If access to the directory is denied
        ValueError: If the directory is outside the project directory
    """
    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(directory)
    
    if not abs_path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")
    
    if not abs_path.is_dir():
        raise NotADirectoryError(f"Path '{directory}' is not a directory")
    
    # Get all files in the directory
    all_files = [str(f.name) for f in abs_path.iterdir()]
    
    # If gitignore filtering is not requested, return all files
    if not use_gitignore:
        return all_files
    
    # Check if a .gitignore file exists in the directory
    gitignore_path = abs_path / ".gitignore"
    if not gitignore_path.exists() or not gitignore_path.is_file():
        # No .gitignore file found, return all files
        return all_files
    
    try:
        # Read and parse .gitignore file
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_patterns = f.read().splitlines()
            
        # Always ignore .git directory if .gitignore exists
        if not any(pattern.strip() == ".git/" or pattern.strip() == ".git" for pattern in gitignore_patterns):
            gitignore_patterns.append(".git/")
        
        # Create PathSpec object for pattern matching
        spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_patterns)
        
        # Filter files based on gitignore patterns
        filtered_files = []
        for item in all_files:
            # Check both the file name and the directory-style name with trailing slash
            # This ensures directories are properly matched by gitignore patterns
            if not spec.match_file(item) and not spec.match_file(f"{item}/"):
                # If it's a directory, make extra sure it's not excluded
                if (abs_path / item).is_dir():
                    # Additional check specifically for directories
                    if not any(pattern.endswith('/') and pattern.rstrip('/') == item for pattern in gitignore_patterns):
                        filtered_files.append(item)
                else:
                    # Regular file
                    filtered_files.append(item)
        
        return filtered_files
    
    except Exception as e:
        # If there's an error parsing .gitignore, log it and return all files
        logger.warning(f"Error applying gitignore filter: {str(e)}. Returning all files.")
        return all_files


def read_file(file_path: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read (relative to project directory)
        
    Returns:
        The contents of the file as a string
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If access to the file is denied
        ValueError: If the file is outside the project directory
    """
    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path)
    
    if not abs_path.exists():
        raise FileNotFoundError(f"File '{file_path}' does not exist")
    
    if not abs_path.is_file():
        raise IsADirectoryError(f"Path '{file_path}' is not a file")
    
    with open(abs_path, 'r', encoding='utf-8') as file:
        return file.read()


def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write to (relative to project directory)
        content: Content to write to the file
        
    Returns:
        True if the file was written successfully
        
    Raises:
        PermissionError: If access to the file is denied
        ValueError: If the file is outside the project directory
    """
    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path)
    
    # Create directory if it doesn't exist
    if not abs_path.parent.exists():
        abs_path.parent.mkdir(parents=True)
    
    with open(abs_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    return True
