"""MCP server implementation with file operation tools."""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.file_tools import list_files, read_file, write_file
from src.models import (
    ErrorResponse,
    ListFilesRequest,
    ListFilesResponse,
    ReadFileRequest,
    ReadFileResponse,
    WriteFileRequest,
    WriteFileResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP File Tools Server",
    description="A simple Model Context Protocol server with file operation tools",
    version="0.1.0",
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors in API requests."""
    error_detail = f"Validation error: {str(exc)}"
    logger.warning(f"{error_detail} - Path: {request.url.path}")
    return JSONResponse(status_code=400, content={"detail": error_detail})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle security and validation errors."""
    error_detail = str(exc)
    if "Security error:" in error_detail:
        logger.warning(f"Security violation: {error_detail} - Path: {request.url.path}")
        return JSONResponse(status_code=403, content={"detail": error_detail})
    else:
        logger.warning(f"Validation error: {error_detail} - Path: {request.url.path}")
        return JSONResponse(status_code=400, content={"detail": error_detail})


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Handle file not found errors."""
    error_detail = f"FileNotFoundError: {str(exc)}"
    logger.info(f"File not found: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(status_code=404, content={"detail": error_detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    error_detail = str(exc)
    logger.error(f"Unexpected error: {error_detail} - Path: {request.url.path}")
    logger.error(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "An internal server error occurred"})


@app.post(
    "/list_files",
    response_model=ListFilesResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def list_files_endpoint(request: ListFilesRequest) -> dict[str, Any]:
    """
    List files in a directory.

    Args:
        request: The request containing the directory path

    Returns:
        A response with the list of files
    """
    # Variables to be cleaned up in finally block
    files = []

    try:
        logger.info(f"Listing files in directory: {request.directory}")
        files = list_files(request.directory, request.use_gitignore)
        logger.debug(f"Found {len(files)} files in {request.directory}")
        return {"files": files}
    except Exception as e:
        # Let the global exception handlers deal with it
        logger.error(f"Error in list_files_endpoint: {str(e)}")
        raise
    finally:
        # Cleanup resources if needed (nothing to clean up here)
        pass


@app.post(
    "/read_file",
    response_model=ReadFileResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def read_file_endpoint(request: ReadFileRequest) -> dict[str, Any]:
    """
    Read the contents of a file.

    Args:
        request: The request containing the file path

    Returns:
        A response with the file content
    """
    # Variables to be cleaned up in finally block
    content = ""
    file_handle = None

    try:
        logger.info(f"Reading file: {request.file_path}")
        content = read_file(request.file_path)
        logger.debug(f"Successfully read {len(content)} bytes from {request.file_path}")
        return {"content": content}
    except Exception as e:
        # Let the global exception handlers deal with it
        logger.error(f"Error in read_file_endpoint: {str(e)}")
        raise
    finally:
        # Cleanup resources if needed (file is already closed in read_file function)
        pass


@app.post(
    "/write_file",
    response_model=WriteFileResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def write_file_endpoint(request: WriteFileRequest) -> dict[str, Any]:
    """
    Write content to a file.

    Args:
        request: The request containing the file path and content

    Returns:
        A response indicating success
    """
    # Variables to be cleaned up in finally block
    file_handle = None

    try:
        logger.info(f"Writing to file: {request.file_path}")
        success = write_file(request.file_path, request.content)
        logger.debug(f"Successfully wrote {len(request.content)} bytes to {request.file_path}")
        return {"success": success}
    except Exception as e:
        # Let the global exception handlers deal with it
        logger.error(f"Error in write_file_endpoint: {str(e)}")
        raise
    finally:
        # Cleanup resources if needed (file is already closed in write_file function)
        pass
