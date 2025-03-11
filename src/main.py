"""Main entry point for the MCP server."""
import argparse
import logging
import os
import sys
from pathlib import Path

import uvicorn

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="MCP File Tools Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--project-dir", type=str, required=True, help="Base directory for all file operations (required)")
    return parser.parse_args()

def main() -> None:
    """
    Main entry point for the MCP server.
    """
    args = parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Validate project directory
    project_dir = Path(args.project_dir)
    if not project_dir.exists() or not project_dir.is_dir():
        logger.error(f"Project directory does not exist or is not a directory: {project_dir}")
        sys.exit(1)
    
    # Set the project directory as a global variable
    os.environ["MCP_PROJECT_DIR"] = str(project_dir.absolute())
    
    logger.info(f"Starting MCP server on {args.host}:{args.port}")
    logger.info(f"Using project directory: {project_dir}")
    
    # Start the server
    uvicorn.run(
        "src.server:app",
        host=args.host,
        port=args.port,
        reload=False
    )

if __name__ == "__main__":
    main()
