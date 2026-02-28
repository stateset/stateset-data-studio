# app.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.settings import settings
from backend.api import projects, jobs, system, synthdata, extensions
from backend.api.middleware import setup_middleware

app = FastAPI(
    title="StateSet Data Studio API",
    default_response_class=ORJSONResponse,
    version="1.1.0",
)

# Setup all middleware including CORS
setup_middleware(app)

# Add request dependency
class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        return response

app.add_middleware(RequestMiddleware)

# Import our direct endpoint module
from backend.api import direct_endpoint

# Routers
for router in (
    projects.router,
    jobs.router,
    system.router,
    synthdata.router,
    extensions.router,
    direct_endpoint.router,  # Add our new direct endpoint router
):
    app.include_router(router)

# Health probe for k8s / Docker-compose
@app.get("/healthz", tags=["System"])
async def healthz():
    return {"status": "ok"}
    
@app.get("/", tags=["System"])
async def root():
    return {"status": "ok", "message": "Welcome to StateSet Data Studio API"}
