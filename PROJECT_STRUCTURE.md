# Project Structure

This document outlines the structure of the MCP Server Filesystem project.

## Directory Layout

```
mcp_server_filesystem/
├── .gitignore             # Git ignore file
├── README.md              # Project documentation
├── PROJECT_STRUCTURE.md   # This file
├── pyproject.toml         # Project configuration
├── requirements.txt       # Project dependencies
├── src/                   # Source code directory
│   ├── __init__.py        # Package initialization
│   ├── file_tools.py      # Implementation of file operations
│   ├── main.py            # Entry point to run the server
│   ├── models.py          # Pydantic models for requests/responses
│   └── server.py          # FastAPI server implementation
└── tests/                 # Tests directory
    ├── __init__.py        # Test package initialization
    ├── test_file_tools.py # Tests for file operations
    ├── test_server.py     # Tests for API endpoints
    └── testdata/          # Test data directory
        └── test_file_tools/ # Test data for file tools tests
```

## Component Details

### Source Code (`src/`)

#### `file_tools.py`

Contains core file system operation functions:

- `list_files`: Lists all files in a directory with optional .gitignore filtering and .git folder exclusion (paths are relative to project directory)
- `read_file`: Reads content from a file (path is relative to project directory)
- `write_file`: Writes content to a file atomically (path is relative to project directory)
- `normalize_path`: Ensures paths are within the project directory
- `get_project_dir`: Retrieves the configured project directory

Each function handles errors appropriately and includes detailed type hints and docstrings.

#### `models.py`

Defines Pydantic models for request and response objects:

- `ListFilesRequest`/`ListFilesResponse`
- `ReadFileRequest`/`ReadFileResponse`
- `WriteFileRequest`/`WriteFileResponse`
- `ErrorResponse`

These models provide schema validation and documentation for the API.

#### `server.py`

Implements FastAPI endpoints that correspond to each file operation:

- `/list_files`
- `/read_file`
- `/write_file`

Each endpoint handles errors and returns appropriate responses.

#### `main.py`

Entry point for running the server:

- Parses command-line arguments
- Validates the required project directory
- Configures logging
- Starts the FastAPI server using uvicorn

### Tests (`tests/`)

#### `test_file_tools.py`

Unit tests for the file operation functions, ensuring they:

- Handle successful cases correctly
- Respond appropriately to errors
- Clean up after themselves

#### `test_server.py`

Integration tests for the API endpoints, verifying they:

- Process valid requests correctly
- Return appropriate error responses
- Interact with the file system as expected

## Design Principles

1. **Separation of Concerns**:
   - File operations are separate from API endpoints
   - Models are isolated from business logic

2. **Comprehensive Error Handling**:
   - All functions have appropriate error cases
   - Errors include detailed messages and types

3. **Clean API Design**:
   - Consistent request/response patterns
   - Clear documentation through Pydantic models

4. **Security**:
   - Validates that requested files are within the project directory
   - Converts all paths to be relative to the project directory
   - Rejects operations that attempt to access files outside the project directory

5. **Testability**:
   - Each component can be tested independently
   - Tests clean up after themselves

## Development Workflow

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest`
3. Run the server: `python -m src.main --project-dir /path/to/project`
4. Access API documentation: http://127.0.0.1:8000/docs
