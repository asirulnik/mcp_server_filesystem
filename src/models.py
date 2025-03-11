"""Data models for MCP server."""

from pydantic import BaseModel, Field


class ListFilesRequest(BaseModel):
    """Request model for list_files operation."""

    directory: str = Field(..., description="Directory path to list files from")
    use_gitignore: bool = Field(
        True, description="Whether to filter files based on .gitignore patterns"
    )


class ListFilesResponse(BaseModel):
    """Response model for list_files operation."""

    files: list[str] = Field(..., description="List of files in the directory")


class ReadFileRequest(BaseModel):
    """Request model for read_file operation."""

    file_path: str = Field(..., description="Path to the file to read")


class ReadFileResponse(BaseModel):
    """Response model for read_file operation."""

    content: str = Field(..., description="Content of the file")


class WriteFileRequest(BaseModel):
    """Request model for write_file operation."""

    file_path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")


class WriteFileResponse(BaseModel):
    """Response model for write_file operation."""

    success: bool = Field(..., description="Whether the write operation was successful")


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")
