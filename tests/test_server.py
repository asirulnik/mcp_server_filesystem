"""Tests for the MCP server API endpoints."""
import os
from pathlib import Path
from fastapi.testclient import TestClient

from src.server import app
from src.models import (
    ListFilesRequest, ReadFileRequest, WriteFileRequest
)

# Create a test client
client = TestClient(app)

# Test constants
TEST_DIR = Path("tests/testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_api_file.txt"
TEST_CONTENT = "This is API test content."


def setup_function():
    """Setup for each test function."""
    # Ensure the test directory exists
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def teardown_function():
    """Teardown for each test function."""
    # Clean up any test files
    if TEST_FILE.exists():
        TEST_FILE.unlink()


def test_write_file_endpoint():
    """Test the write_file endpoint."""
    request = WriteFileRequest(
        file_path=str(TEST_FILE),
        content=TEST_CONTENT
    )
    
    response = client.post("/write_file", json=request.model_dump())
    
    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert TEST_FILE.exists()
    
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    assert content == TEST_CONTENT


def test_read_file_endpoint():
    """Test the read_file endpoint."""
    # Create a test file
    with open(TEST_FILE, 'w', encoding='utf-8') as f:
        f.write(TEST_CONTENT)
    
    request = ReadFileRequest(file_path=str(TEST_FILE))
    
    response = client.post("/read_file", json=request.model_dump())
    
    assert response.status_code == 200
    assert response.json() == {"content": TEST_CONTENT}


def test_list_files_endpoint():
    """Test the list_files endpoint."""
    # Create a test file
    with open(TEST_FILE, 'w', encoding='utf-8') as f:
        f.write(TEST_CONTENT)
    
    request = ListFilesRequest(directory=str(TEST_DIR))
    
    response = client.post("/list_files", json=request.model_dump())
    
    assert response.status_code == 200
    files = response.json()["files"]
    assert TEST_FILE.name in files


def test_read_file_not_found():
    """Test the read_file endpoint with a non-existent file."""
    non_existent_file = TEST_DIR / "non_existent.txt"
    
    # Ensure the file doesn't exist
    if non_existent_file.exists():
        non_existent_file.unlink()
    
    request = ReadFileRequest(file_path=str(non_existent_file))
    
    response = client.post("/read_file", json=request.model_dump())
    
    assert response.status_code == 400
    response_data = response.json()
    assert "FileNotFoundError" in response_data["detail"]


def test_list_files_directory_not_found():
    """Test the list_files endpoint with a non-existent directory."""
    non_existent_dir = TEST_DIR / "non_existent_dir"
    
    # Ensure the directory doesn't exist
    if non_existent_dir.exists() and non_existent_dir.is_dir():
        non_existent_dir.rmdir()
    
    request = ListFilesRequest(directory=str(non_existent_dir))
    
    response = client.post("/list_files", json=request.model_dump())
    
    assert response.status_code == 400
    response_data = response.json()
    assert "FileNotFoundError" in response_data["detail"]


def test_list_files_endpoint_with_gitignore():
    """Test the list_files endpoint with gitignore filtering."""
    # Create a .gitignore file
    gitignore_path = TEST_DIR / ".gitignore"
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write("*.ignore\n")
    
    # Create a test file that should be ignored
    test_ignore_file = TEST_DIR / "test.ignore"
    with open(test_ignore_file, 'w', encoding='utf-8') as f:
        f.write("This should be ignored")
    
    # Create a test file that should not be ignored
    test_normal_file = TEST_DIR / "test_normal.txt"
    with open(test_normal_file, 'w', encoding='utf-8') as f:
        f.write("This should not be ignored")
    
    # Test with gitignore filtering enabled (default)
    request = ListFilesRequest(directory=str(TEST_DIR))
    response = client.post("/list_files", json=request.model_dump())
    
    assert response.status_code == 200
    files = response.json()["files"]
    assert "test_normal.txt" in files
    assert ".gitignore" in files
    assert "test.ignore" not in files
    
    # Clean up
    gitignore_path.unlink()
    test_ignore_file.unlink()
    test_normal_file.unlink()


def test_list_files_endpoint_without_gitignore():
    """Test the list_files endpoint without gitignore filtering."""
    # Create a .gitignore file
    gitignore_path = TEST_DIR / ".gitignore"
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write("*.ignore\n")
    
    # Create a test file that would normally be ignored
    test_ignore_file = TEST_DIR / "test.ignore"
    with open(test_ignore_file, 'w', encoding='utf-8') as f:
        f.write("This would normally be ignored")
    
    # Create a test file that would not be ignored
    test_normal_file = TEST_DIR / "test_normal.txt"
    with open(test_normal_file, 'w', encoding='utf-8') as f:
        f.write("This would not be ignored")
    
    # Test with gitignore filtering disabled
    request = ListFilesRequest(directory=str(TEST_DIR), use_gitignore=False)
    response = client.post("/list_files", json=request.model_dump())
    
    assert response.status_code == 200
    files = response.json()["files"]
    assert "test_normal.txt" in files
    assert ".gitignore" in files
    assert "test.ignore" in files
    
    # Clean up
    gitignore_path.unlink()
    test_ignore_file.unlink()
    test_normal_file.unlink()
