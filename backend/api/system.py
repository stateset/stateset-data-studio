from __future__ import annotations

"""System & Ops endpoints: health, config, SDK probe, PDF conversion, etc."""

import json
import subprocess
import platform
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml
import psutil
from fastapi import APIRouter, Depends, HTTPException, status, Form, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api._base import BaseRouter
from backend.db.session import get_db
from backend.db.models import Job, Project
from backend.services import files
from backend.services.jobs import JobService
from backend.settings import settings

router: APIRouter = BaseRouter(prefix="/system", tags=["System"])

# ---------------------------------------------------------------------------
# 0. CORS test endpoint
# ---------------------------------------------------------------------------

@router.get("/cors-test")
async def cors_test():
    """
    Simple endpoint to test CORS configuration.
    Returns a success message if CORS is properly configured.
    """
    return JSONResponse(
        content={"status": "success", "message": "CORS is working correctly"},
        status_code=200
    )

# ---------------------------------------------------------------------------
# 1. SDK / env checks
# ---------------------------------------------------------------------------

@router.get("/info")
async def sdk_info():
    """Return SDK version + API version."""
    try:
        out = subprocess.check_output([settings.sdk_bin, "--version"], text=True)
        return {"status": "ok", "sdk_version": out.strip(), "api_version": "1.0.0"}
    except Exception as exc:
        raise HTTPException(500, f"SDK error: {exc}")


@router.get("/check")
async def sdk_check():
    try:
        out = subprocess.check_output([settings.sdk_bin, "system-check"], text=True)
        return {"status": "ok", "message": out.strip()}
    except subprocess.CalledProcessError as exc:
        raise HTTPException(500, exc.stderr or exc.stdout or str(exc))

# ---------------------------------------------------------------------------
# 2. Config endpoints
# ---------------------------------------------------------------------------

CONFIG_PATH = Path("configs/config.yaml")


class SystemConfig(BaseModel):
    api_type: Optional[str]
    vllm_api_base: Optional[str]
    vllm_model: Optional[str]
    llama_api_key: Optional[str]
    llama_model: Optional[str]


class GenerationConfig(BaseModel):
    temperature: Optional[float]
    chunk_size: Optional[int]
    num_pairs: Optional[int]


class CurationConfig(BaseModel):
    threshold: Optional[float]
    batch_size: Optional[int]


@router.get("/config")
async def get_config():
    if not CONFIG_PATH.exists():
        raise HTTPException(404, "config.yaml not found")
    return yaml.safe_load(CONFIG_PATH.read_text())


@router.put("/config", status_code=status.HTTP_204_NO_CONTENT)
async def update_config(body: dict):
    if not CONFIG_PATH.exists():
        current = {}
    else:
        current = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    current.update(body)
    CONFIG_PATH.write_text(yaml.safe_dump(current))


@router.patch("/config/generation", status_code=status.HTTP_204_NO_CONTENT)
async def patch_generation(cfg: GenerationConfig):
    data = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    data.setdefault("generation", {})
    for k, v in cfg.dict(exclude_none=True).items():
        data["generation"][k] = v
    CONFIG_PATH.write_text(yaml.safe_dump(data))


@router.patch("/config/curation", status_code=status.HTTP_204_NO_CONTENT)
async def patch_curation(cfg: CurationConfig):
    data = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    data.setdefault("curate", {})
    for k, v in cfg.dict(exclude_none=True).items():
        data["curate"][k] = v
    CONFIG_PATH.write_text(yaml.safe_dump(data))

# ---------------------------------------------------------------------------
# 3. Convert existing PDF to text (convenience)
# ---------------------------------------------------------------------------

@router.post("/convert-pdf")
async def convert_pdf(file_path: str = Form(...)):
    path = files.normalise_path(file_path)
    if not path.exists():
        raise HTTPException(404, f"File not found: {file_path}")
    if path.suffix.lower() != ".pdf":
        raise HTTPException(400, "Not a PDF")
    out_path = settings.data_dir / "output" / f"{path.stem}.txt"
    ok = files.convert_pdf_to_text(path, out_path)
    if not ok:
        raise HTTPException(500, "Conversion failed")
    return {"status": "ok", "output": str(out_path)}

# ---------------------------------------------------------------------------
# 4. Health probe (DB + SDK + system resources)
# ---------------------------------------------------------------------------

@router.get("/health")
async def health(db: Session = Depends(get_db)):
    # DB counts
    try:
        projects = db.query(Project).count()
        jobs = db.query(Job).count()
        db_status = "ok"
    except Exception as exc:
        db_status = "error"
        projects = jobs = None

    # SDK version
    try:
        sdk_v = subprocess.check_output([settings.sdk_bin, "--version"], text=True).strip()
        sdk_status = "ok"
    except Exception as exc:
        sdk_v = str(exc)
        sdk_status = "error"

    sys = psutil.virtual_memory()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {"status": db_status, "projects": projects, "jobs": jobs},
        "sdk": {"status": sdk_status, "version": sdk_v},
        "system": {
            "platform": platform.platform(),
            "cpu": psutil.cpu_count(),
            "memory_total_gb": round(sys.total / 1e9, 2),
            "memory_used_pct": sys.percent,
            "disk_used_pct": psutil.disk_usage("/").percent,
        },
    }

# ---------------------------------------------------------------------------
# 5. Restart stalled jobs (running → pending)
# ---------------------------------------------------------------------------

@router.post("/restart-stalled-jobs")
async def restart_stalled(background: BackgroundTasks, db: Session = Depends(get_db)):
    stalled = (
        db.query(Job).filter(Job.status == "running").all()
    )
    for j in stalled:
        j.status = "pending"
        j.error = "Restarted by /system/restart-stalled-jobs"
        db.commit()
        background.add_task(
            JobService.queue_create,  # noqa pseudo-code; you'd call correct queue fn
            db,
            j.project_id,
            j.input_file,
            j.job_type,
            j.num_pairs,
            background,
        )
    return {"restarted": len(stalled)}

# ---------------------------------------------------------------------------
# 6. Server logs
# ---------------------------------------------------------------------------

class LogEntry(BaseModel):
    timestamp: str
    level: str
    source: str
    message: str

class LogsResponse(BaseModel):
    logs: List[LogEntry]
    total: int

@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    log_level: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """
    Get server logs with optional filtering and pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of log entries per page
        search: Optional text to search for in log messages
        log_level: Optional log level filter (INFO, ERROR, WARNING, DEBUG)
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
    """
    log_files = [
        Path("server.log"),
        Path("run_log.txt"),
        Path("api_tests.log"),
        Path("production_test.log"),
        Path("workflow_test.log"),
    ]
    
    # Filter to only existing log files
    log_files = [f for f in log_files if f.exists()]
    
    if not log_files:
        return LogsResponse(logs=[], total=0)
    
    all_logs = []
    
    # Regular expression for common log formats
    log_pattern = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s+'
        r'(?P<level>[A-Z]+)\s+'
        r'(?P<source>[\w\.]+)\s+-\s+'
        r'(?P<message>.*)'
    )
    
    # Simple log pattern (fallback)
    simple_pattern = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s+'
        r'(?P<message>.*)'
    )
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try to match the log pattern
                    match = log_pattern.match(line)
                    if match:
                        log_entry = LogEntry(
                            timestamp=match.group('timestamp'),
                            level=match.group('level'),
                            source=match.group('source'),
                            message=match.group('message')
                        )
                    else:
                        # Try the simpler pattern
                        simple_match = simple_pattern.match(line)
                        if simple_match:
                            log_entry = LogEntry(
                                timestamp=simple_match.group('timestamp'),
                                level="INFO",  # Default level
                                source=log_file.name,  # Use filename as source
                                message=simple_match.group('message')
                            )
                        else:
                            # If no match, add as a continuation of the previous message
                            if all_logs:
                                all_logs[-1].message += f"\n{line}"
                            continue
                    
                    # Apply filters
                    if log_level and log_entry.level != log_level:
                        continue
                    
                    if search and search.lower() not in log_entry.message.lower():
                        continue
                    
                    if start_date and log_entry.timestamp < start_date:
                        continue
                    
                    if end_date and log_entry.timestamp > end_date:
                        continue
                    
                    all_logs.append(log_entry)
        except Exception as e:
            # If there's an error reading a log file, continue with other files
            print(f"Error reading log file {log_file}: {e}")
            continue
    
    # Sort logs by timestamp (newest first)
    all_logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply pagination
    total = len(all_logs)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_logs = all_logs[start_idx:end_idx]
    
    return LogsResponse(logs=page_logs, total=total)