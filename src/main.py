"""Main entry point for the MCP server."""
import argparse
import logging
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
    parser.add_argument("--base-dir", type=str, help="Base directory for file operations (optional)")
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
    
    logger.info(f"Starting MCP server on {args.host}:{args.port}")
    if args.base_dir:
        logger.info(f"Using base directory: {args.base_dir}")
    
    # Start the server
    uvicorn.run(
        "src.server:app",
        host=args.host,
        port=args.port,
        reload=False
    )

if __name__ == "__main__":
    main()
