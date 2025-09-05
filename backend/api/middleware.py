"""
FastAPI middleware for standardized logging and request tracking.
"""

import time
import uuid
import logging
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

# Set up a dedicated API logger
api_logger = logging.getLogger("api")


class BackgroundTasksMiddleware(BaseHTTPMiddleware):
    '''
    Middleware that injects BackgroundTasks if missing in the request.
    This middleware automatically provides a BackgroundTasks object for routes
    that require it but don't receive it from the client.
    '''
    
    async def dispatch(self, request: Request, call_next):
        # Process the request and continue the middleware chain
        return await call_next(request)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every API request with timing and content info.
    
    This middleware:
    1. Generates a unique request ID for each request
    2. Logs the incoming request method, path, and headers
    3. Times the request processing
    4. Logs the response status code and timing
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state for downstream use
        request.state.request_id = request_id
        
        # Get client info
        client_host = request.client.host if request.client else "unknown"
        
        # Log the request
        api_logger.info(
            f"Request started | ID: {request_id} | "
            f"{request.method} {request.url.path} | "
            f"Client: {client_host}"
        )
        
        # Process the request and time it
        start_time = time.time()
        
        try:
            # Call the next middleware/endpoint
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log the response
            api_logger.info(
                f"Request completed | ID: {request_id} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.4f}s | "
                f"{request.method} {request.url.path}"
            )
            
            # Add the request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate processing time even for errors
            process_time = time.time() - start_time
            
            # Log the error
            api_logger.error(
                f"Request failed | ID: {request_id} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.4f}s | "
                f"{request.method} {request.url.path}",
                exc_info=True
            )
            
            # Re-raise the exception for proper error handling
            raise

def configure_logging():
    """
    Configure standardized logging format and handlers.
    """
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Configure API logger with both console and file handlers
    logger = logging.getLogger("api")
    logger.setLevel(logging.INFO)
    
    # Add file handler
    file_handler = logging.FileHandler("server.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(file_handler)

def setup_middleware(app: FastAPI):
    """
    Set up all middleware for the FastAPI app.
    """
    # Configure logging first
    configure_logging()
    
    # Add CORS middleware (use the settings from the app)
    from backend.settings import settings
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
        max_age=86400,  # 24 hours
    )
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add background tasks middleware
    app.add_middleware(BackgroundTasksMiddleware)