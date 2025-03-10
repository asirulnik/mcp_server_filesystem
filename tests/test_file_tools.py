"""Tests for file_tools module."""
import os
import pytest
from pathlib import Path

from src.file_tools import list_files, read_file, write_file

# Test constants
TEST_DIR = Path("tests/testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_file.txt"
TEST_CONTENT = "This is test content."


def setup_function():
    """Setup for each test function."""
    # Ensure the test directory exists
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def teardown_function():
    """Teardown for each test function."""
    # Clean up any test files
    if TEST_FILE.exists():
        TEST_FILE.unlink()


def test_write_file():
    """Test writing to a file."""
    # Test writing to a file
    result = write_file(str(TEST_FILE), TEST_CONTENT)
    
    # Verify the file was written
    assert result is True
    assert TEST_FILE.exists()
    
    # Verify the file content
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    assert content == TEST_CONTENT


def test_read_file():
    """Test reading from a file."""
    # Create a test file
    with open(TEST_FILE, 'w', encoding='utf-8') as f:
        f.write(TEST_CONTENT)
    
    # Test reading the file
    content = read_file(str(TEST_FILE))
    
    # Verify the content
    assert content == TEST_CONTENT


def test_read_file_not_found():
    """Test reading a file that doesn't exist."""
    non_existent_file = TEST_DIR / "non_existent.txt"
    
    # Ensure the file doesn't exist
    if non_existent_file.exists():
        non_existent_file.unlink()
    
    # Test reading a non-existent file
    with pytest.raises(FileNotFoundError):
        read_file(str(non_existent_file))


def test_list_files():
    """Test listing files in a directory."""
    # Create a test file
    with open(TEST_FILE, 'w', encoding='utf-8') as f:
        f.write(TEST_CONTENT)
    
    # Test listing files
    files = list_files(str(TEST_DIR))
    
    # Verify the file is in the list
    assert TEST_FILE.name in files


def test_list_files_directory_not_found():
    """Test listing files in a directory that doesn't exist."""
    non_existent_dir = TEST_DIR / "non_existent_dir"
    
    # Ensure the directory doesn't exist
    if non_existent_dir.exists():
        if non_existent_dir.is_dir():
            os.rmdir(non_existent_dir)
        else:
            non_existent_dir.unlink()
    
    # Test listing files in a non-existent directory
    with pytest.raises(FileNotFoundError):
        list_files(str(non_existent_dir))
