"""File operation tools for MCP server."""
import logging
from pathlib import Path
from typing import Any

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
logger = logging.getLogger(__name__)

def list_files(directory: str, use_gitignore: bool = True) -> list[str]:
    """
    List all files in a directory.
    
    Args:
        directory: Path to the directory to list files from
        use_gitignore: Whether to filter results based on .gitignore patterns (default: True)
        
    Returns:
        A list of filenames in the directory
        
    Raises:
        FileNotFoundError: If the directory does not exist
        PermissionError: If access to the directory is denied
    """
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")
    
    if not path.is_dir():
        raise NotADirectoryError(f"Path '{directory}' is not a directory")
    
    # Get all files in the directory
    all_files = [str(f.name) for f in path.iterdir()]
    
    # If gitignore filtering is not requested, return all files
    if not use_gitignore:
        return all_files
    
    # Check if a .gitignore file exists in the directory
    gitignore_path = path / ".gitignore"
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
        # Convert to full paths for matching, then extract names back
        filtered_files = [
            item for item in all_files 
            if not spec.match_file(item) and not spec.match_file(f"{item}/")
        ]
        
        return filtered_files
    
    except Exception as e:
        # If there's an error parsing .gitignore, log it and return all files
        logger.warning(f"Error applying gitignore filter: {str(e)}. Returning all files.")
        return all_files


def read_file(file_path: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        The contents of the file as a string
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If access to the file is denied
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File '{file_path}' does not exist")
    
    if not path.is_file():
        raise IsADirectoryError(f"Path '{file_path}' is not a file")
    
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()


def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write to
        content: Content to write to the file
        
    Returns:
        True if the file was written successfully
        
    Raises:
        PermissionError: If access to the file is denied
    """
    path = Path(file_path)
    
    # Create directory if it doesn't exist
    if not path.parent.exists():
        path.parent.mkdir(parents=True)
    
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    return True
