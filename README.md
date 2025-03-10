# MCP File Tools Server

A simple Model Context Protocol (MCP) server with file operation tools. This server provides a straightforward API for performing file system operations, following the MCP protocol design.

## Features

- `list_files`: List all files in a directory
- `read_file`: Read the contents of a file
- `write_file`: Write content to a file

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-server-filesystem

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
python -m src.main
```

By default, the server will run on `http://127.0.0.1:8000`. You can change the host and port using command line arguments:

```bash
python -m src.main --host 0.0.0.0 --port 8080
```

You can also specify a base directory for file operations (optional):

```bash
python -m src.main --base-dir /path/to/base/directory
```

## API Endpoints

### List Files
- **URL**: `/list_files`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "directory": "/path/to/directory"
  }
  ```
- **Response**:
  ```json
  {
    "files": ["file1.txt", "file2.txt"]
  }
  ```

### Read File
- **URL**: `/read_file`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "file_path": "/path/to/file.txt"
  }
  ```
- **Response**:
  ```json
  {
    "content": "File content goes here"
  }
  ```

### Write File
- **URL**: `/write_file`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "file_path": "/path/to/file.txt",
    "content": "Content to write to the file"
  }
  ```
- **Response**:
  ```json
  {
    "success": true
  }
  ```

## Running Tests

```bash
pytest
```

## Project Structure

For a complete overview of the project structure, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

```
mcp_server_filesystem/
├── src/            # Source code
├── tests/          # Test files
└── requirements.txt # Dependencies
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd mcp-server-filesystem

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
```

## License

MIT
