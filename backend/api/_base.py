from fastapi import APIRouter, Request
from datetime import datetime
from typing import Optional, Callable, Any, Dict
from pydantic import BaseModel
import logging
import functools

logger = logging.getLogger(__name__)

class BaseRouter(APIRouter):
    """Base router with default dependencies"""
    
    def __init__(self, *args, **kwargs):
        # Add default dependencies
        kwargs.setdefault("dependencies", [])
        
        super().__init__(*args, **kwargs)
        
    # Override route decorator to add default db dependency
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)
    
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)
    
    def put(self, *args, **kwargs):
        return super().put(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)
        
# API response models to replace the SQLAlchemy models
class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class JobResponse(BaseModel):
    id: str
    project_id: str
    job_type: str
    status: str
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    config: Optional[str] = None
    stats: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }
    
class JobCreationResponse(BaseModel):
    """Simple response model for job creation endpoints"""
    id: str
    status: str
    job_type: str
    
class APIResponse(BaseModel):
    """Generic API response model"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    
def log_call(func: Callable) -> Callable:
    """Decorator to log API calls with request information"""
    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs) -> Any:
        client_host = request.client.host if request.client else "unknown"
        logger.info(f"API call: {func.__name__} | Client: {client_host} | Path: {request.url.path}")
        try:
            result = await func(request, *args, **kwargs)
            logger.info(f"API call completed: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"API call failed: {func.__name__} | Error: {str(e)}")
            raise
    return wrapper
