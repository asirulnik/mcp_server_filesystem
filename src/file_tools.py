"""File operation tools for MCP server."""
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def list_files(directory: str) -> list[str]:
    """
    List all files in a directory.
    
    Args:
        directory: Path to the directory to list files from
        
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
    
    return [str(f.name) for f in path.iterdir()]


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
