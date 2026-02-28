"""
Logging utilities for backend API operations.
"""

import functools
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, cast, get_type_hints

# Create a dedicated logger for API endpoints
endpoint_logger = logging.getLogger("api.endpoints")

# Type variable for generic function decorator
F = TypeVar('F', bound=Callable[..., Any])
WRAPS_ASSIGNED = tuple(
    attr for attr in functools.WRAPPER_ASSIGNMENTS if attr != "__annotations__"
)


def _resolve_signature(func: Callable[..., Any]) -> inspect.Signature:
    signature = inspect.signature(func)
    try:
        hints = get_type_hints(func, globalns=func.__globals__, include_extras=True)
    except Exception:
        hints = {}

    params = []
    for name, param in signature.parameters.items():
        params.append(param.replace(annotation=hints.get(name, param.annotation)))

    return signature.replace(
        parameters=params,
        return_annotation=hints.get("return", signature.return_annotation),
    )

def log_endpoint_call(func: F) -> F:
    """
    Decorator to log API endpoint calls with timing information.
    
    This decorator:
    1. Logs when the endpoint is called
    2. Times the execution
    3. Logs the result (success/error) with timing
    
    For FastAPI endpoints, it will properly log request information.
    """
    @functools.wraps(func, assigned=WRAPS_ASSIGNED)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get the function name and module
        func_name = func.__name__
        module = inspect.getmodule(func)
        module_name = module.__name__ if module else "unknown"
        
        # Extract request object if it's a FastAPI endpoint
        request = None
        request_id = "unknown"
        
        # Look for the request object in kwargs
        for arg_name, arg_value in kwargs.items():
            if arg_name == "request" or (hasattr(arg_value, "__class__") and 
                                        arg_value.__class__.__name__ == "Request"):
                request = arg_value
                if hasattr(request, "state") and hasattr(request.state, "request_id"):
                    request_id = request.state.request_id
                break
        
        # Log endpoint call start
        endpoint_logger.info(
            f"Endpoint call started | ID: {request_id} | "
            f"Function: {module_name}.{func_name}"
        )
        
        # Track execution time
        start_time = time.time()
        
        try:
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Calculate execution time
            exec_time = time.time() - start_time
            
            # Log endpoint call success
            endpoint_logger.info(
                f"Endpoint call completed | ID: {request_id} | "
                f"Function: {module_name}.{func_name} | "
                f"Time: {exec_time:.4f}s"
            )
            
            return result
            
        except Exception as e:
            # Calculate execution time
            exec_time = time.time() - start_time
            
            # Log endpoint call failure
            endpoint_logger.error(
                f"Endpoint call failed | ID: {request_id} | "
                f"Function: {module_name}.{func_name} | "
                f"Error: {str(e)} | "
                f"Time: {exec_time:.4f}s",
                exc_info=True
            )
            
            # Re-raise the exception
            raise
            
    @functools.wraps(func, assigned=WRAPS_ASSIGNED)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get the function name and module
        func_name = func.__name__
        module = inspect.getmodule(func)
        module_name = module.__name__ if module else "unknown"
        
        # Extract request object if it's a FastAPI endpoint
        request = None
        request_id = "unknown"
        
        # Look for the request object in kwargs
        for arg_name, arg_value in kwargs.items():
            if arg_name == "request" or (hasattr(arg_value, "__class__") and 
                                        arg_value.__class__.__name__ == "Request"):
                request = arg_value
                if hasattr(request, "state") and hasattr(request.state, "request_id"):
                    request_id = request.state.request_id
                break
        
        # Log endpoint call start
        endpoint_logger.info(
            f"Endpoint call started | ID: {request_id} | "
            f"Function: {module_name}.{func_name}"
        )
        
        # Track execution time
        start_time = time.time()
        
        try:
            # Call the original function
            result = func(*args, **kwargs)
            
            # Calculate execution time
            exec_time = time.time() - start_time
            
            # Log endpoint call success
            endpoint_logger.info(
                f"Endpoint call completed | ID: {request_id} | "
                f"Function: {module_name}.{func_name} | "
                f"Time: {exec_time:.4f}s"
            )
            
            return result
            
        except Exception as e:
            # Calculate execution time
            exec_time = time.time() - start_time
            
            # Log endpoint call failure
            endpoint_logger.error(
                f"Endpoint call failed | ID: {request_id} | "
                f"Function: {module_name}.{func_name} | "
                f"Error: {str(e)} | "
                f"Time: {exec_time:.4f}s",
                exc_info=True
            )
            
            # Re-raise the exception
            raise
            
    # Return the appropriate wrapper based on whether the function is async or not
    resolved_signature = _resolve_signature(func)
    async_wrapper.__signature__ = resolved_signature
    sync_wrapper.__signature__ = resolved_signature

    if inspect.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    return cast(F, sync_wrapper)

# Alias for the decorator for easier import
log_call = log_endpoint_call
