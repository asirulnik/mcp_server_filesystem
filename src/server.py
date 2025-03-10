"""MCP server implementation with file operation tools."""
import logging
from typing import Any

from fastapi import FastAPI, HTTPException

from src.models import (
    ListFilesRequest, ListFilesResponse,
    ReadFileRequest, ReadFileResponse,
    WriteFileRequest, WriteFileResponse,
    ErrorResponse
)
from src.file_tools import list_files, read_file, write_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP File Tools Server",
    description="A simple Model Context Protocol server with file operation tools",
    version="0.1.0"
)


@app.post("/list_files", response_model=ListFilesResponse, responses={400: {"model": ErrorResponse}})
async def list_files_endpoint(request: ListFilesRequest) -> dict[str, Any]:
    """
    List files in a directory.
    
    Args:
        request: The request containing the directory path
        
    Returns:
        A response with the list of files
    """
    try:
        files = list_files(request.directory)
        return {"files": files}
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=400, detail={
            "error": str(e),
            "error_type": type(e).__name__
        })


@app.post("/read_file", response_model=ReadFileResponse, responses={400: {"model": ErrorResponse}})
async def read_file_endpoint(request: ReadFileRequest) -> dict[str, Any]:
    """
    Read the contents of a file.
    
    Args:
        request: The request containing the file path
        
    Returns:
        A response with the file content
    """
    try:
        content = read_file(request.file_path)
        return {"content": content}
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(status_code=400, detail={
            "error": str(e),
            "error_type": type(e).__name__
        })


@app.post("/write_file", response_model=WriteFileResponse, responses={400: {"model": ErrorResponse}})
async def write_file_endpoint(request: WriteFileRequest) -> dict[str, Any]:
    """
    Write content to a file.
    
    Args:
        request: The request containing the file path and content
        
    Returns:
        A response indicating success
    """
    try:
        success = write_file(request.file_path, request.content)
        return {"success": success}
    except PermissionError as e:
        logger.error(f"Error writing file: {str(e)}")
        raise HTTPException(status_code=400, detail={
            "error": str(e),
            "error_type": type(e).__name__
        })
