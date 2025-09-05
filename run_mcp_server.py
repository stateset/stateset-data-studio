#!/usr/bin/env python3
"""
Launch script for the StateSet Data Studio MCP Server
"""

import os
import sys
import argparse
import uvicorn
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mcp-server")

def main():
    parser = argparse.ArgumentParser(description="StateSet Data Studio MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level (debug, info, warning, error, critical)")
    args = parser.parse_args()
    
    # Set log level
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)
    
    logger.info(f"Starting MCP Server on {args.host}:{args.port}")
    logger.info(f"Auto-reload: {'enabled' if args.reload else 'disabled'}")
    
    # Run the server
    uvicorn.run(
        "mcp_server:app", 
        host=args.host, 
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower()
    )

if __name__ == "__main__":
    main()