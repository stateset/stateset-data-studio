#!/usr/bin/env python3
"""
Test script to validate API extensions import.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-api-import")

def test_import():
    """Test importing the API extensions router."""
    try:
        # Method 1: Direct import
        logger.info("Trying direct import...")
        try:
            from api_extensions import router as extensions_router
            logger.info("Direct import successful!")
            logger.info(f"Router routes: {[route.path for route in extensions_router.routes]}")
            return True
        except ImportError as e:
            logger.error(f"Direct import failed: {str(e)}")
        
        # Method 2: Backend-prefixed import
        logger.info("Trying backend-prefixed import...")
        try:
            from backend.api_extensions import router as extensions_router
            logger.info("Backend-prefixed import successful!")
            logger.info(f"Router routes: {[route.path for route in extensions_router.routes]}")
            return True
        except ImportError as e:
            logger.error(f"Backend-prefixed import failed: {str(e)}")
        
        # Method 3: Add current directory to path
        logger.info("Adding current directory to sys.path...")
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
            
        logger.info("Trying import again...")
        try:
            from api_extensions import router as extensions_router
            logger.info("Import successful after path addition!")
            logger.info(f"Router routes: {[route.path for route in extensions_router.routes]}")
            return True
        except ImportError as e:
            logger.error(f"Import failed even after path addition: {str(e)}")
        
        # Method 4: Try with direct backend directory path
        logger.info("Adding 'backend' directory to sys.path...")
        backend_dir = os.path.join(os.getcwd(), "backend")
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
            
        logger.info("Trying import with backend directory in path...")
        try:
            from api_extensions import router as extensions_router
            logger.info("Import successful with backend in path!")
            logger.info(f"Router routes: {[route.path for route in extensions_router.routes]}")
            return True
        except ImportError as e:
            logger.error(f"Import failed even with backend in path: {str(e)}")
        
        return False
    except Exception as e:
        logger.error(f"Unexpected error during import test: {str(e)}")
        return False

if __name__ == "__main__":
    # Print the current directory and Python path
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Current Python path: {sys.path}")
    
    # List files in the current directory and backend directory
    logger.info(f"Files in current directory: {os.listdir('.')}")
    logger.info(f"Files in backend directory: {os.listdir('./backend')}")
    
    # Run the import test
    success = test_import()
    
    if success:
        logger.info("Import test passed successfully!")
        sys.exit(0)
    else:
        logger.error("Import test failed!")
        sys.exit(1)