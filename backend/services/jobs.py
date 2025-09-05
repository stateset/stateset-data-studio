from __future__ import annotations

"""Business‑logic layer for Job orchestration.

All heavy work (file‑IO, SDK subprocess, stats extraction) lives here so that
API routes remain thin and unit‑tests can import this module directly.
"""

import json, uuid, os
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal, List

from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from backend.db.models import Job, Project
from backend.services import files, stats
from backend.services.sdk import SDKService

# ---------------------------------------------------------------------------
# Helper – create Job row
# ---------------------------------------------------------------------------

def _new_job(
    db: Session,
    project_id: str,
    job_type: str,
    input_file: str,
    output_file: str | None = None,
    cfg: dict | None = None,
    status: str = "pending",
) -> Job:
    job = Job(
        id=str(uuid.uuid4()),
        project_id=project_id,
        job_type=job_type,
        status=status,
        input_file=input_file,
        output_file=output_file,
        config=json.dumps(cfg or {}),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

# ---------------------------------------------------------------------------
# Ingest jobs
# ---------------------------------------------------------------------------

class JobService:
    """Stateless wrappers that enqueue SDKService tasks and manipulate DB."""

    # -------------------- INGEST --------------------
    @staticmethod
    def queue_ingest(
        db: Session,
        project_id: str,
        path: str,
        background: BackgroundTasks,
    ) -> Job:
        JobService._assert_project(db, project_id)
        
        # Determine the expected output file in advance
        input_path = Path(path)
        out_dir = files.ensure_output_dir("output")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_file = out_dir / f"processed_{timestamp}.txt"
        
        # Create job with the expected output file path
        job = _new_job(db, project_id, "ingest", path, str(out_file))
        
        # Add output file path to arguments for the SDK command - using correct parameter names
        out_dir_str = str(out_file.parent)
        out_name = out_file.name
        args = [path, "--output-dir", out_dir_str, "--name", out_name]
        background.add_task(SDKService.run, job, "ingest", args, db)
        return job

    @staticmethod
    def queue_ingest_url(
        db: Session,
        project_id: str,
        url: str,
        background: BackgroundTasks,
    ) -> Job:
        JobService._assert_project(db, project_id)
        
        # Determine the expected output file in advance
        out_dir = files.ensure_output_dir("output")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        # Use a sanitized version of the URL as part of the filename
        url_base = url.split("://")[-1].split("/")[0].replace(".", "_")[:30]
        out_file = out_dir / f"processed_{timestamp}_{url_base}.txt"
        
        # Create job with the expected output file path
        job = _new_job(db, project_id, "ingest", url, str(out_file))
        
        # Add output file path to arguments for the SDK command - using correct parameter names
        out_dir_str = str(out_file.parent)
        out_name = out_file.name
        args = [url, "--output-dir", out_dir_str, "--name", out_name]
        background.add_task(SDKService.run, job, "ingest", args, db)
        return job

    @staticmethod
    def queue_ingest_youtube(
        db: Session,
        project_id: str,
        youtube_url: str,
        background: BackgroundTasks,
    ) -> Job:
        JobService._assert_project(db, project_id)
        
        # Determine the expected output file in advance
        out_dir = files.ensure_output_dir("output")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        # Extract video ID from YouTube URL if possible
        video_id = youtube_url.split("v=")[-1].split("&")[0] if "v=" in youtube_url else "youtube"
        out_file = out_dir / f"processed_{timestamp}_{video_id}.txt"
        
        # Create job with the expected output file path
        job = _new_job(db, project_id, "ingest", youtube_url, str(out_file))
        
        # Add output file path to arguments for the SDK command - using correct parameter names
        out_dir_str = str(out_file.parent)
        out_name = out_file.name
        args = [youtube_url, "--type", "youtube", "--output-dir", out_dir_str, "--name", out_name]
        background.add_task(SDKService.run, job, "ingest", args, db)
        return job

    # -------------------- CREATE --------------------
    @staticmethod
    def queue_create(
        db: Session,
        project_id: str,
        input_path: str,
        qa_type: str,
        num_pairs: int | None,
        background: BackgroundTasks,
    ) -> Job:
        JobService._assert_project(db, project_id)
        out_dir = files.ensure_output_dir("generated")
        out_file = files.infer_output_path(out_dir, input_path, qa_type)
        cfg = {"qa_type": qa_type, "num_pairs": num_pairs}
        job = _new_job(db, project_id, "create", input_path, str(out_file), cfg)
        args = [input_path, "--type", qa_type, "--output-dir", str(out_dir)]
        if num_pairs:
            args += ["-n", str(num_pairs)]
        background.add_task(SDKService.run, job, "create", args, db)
        return job

    @staticmethod
    def queue_create_advanced(
        db: Session,
        project_id: str,
        input_path: str,
        qa_type: str,
        num_pairs: int | None,
        temperature: float | None,
        chunk_size: int | None,
        max_tokens: int | None,
        overlap: int | None,
        prompts_json: str | None,
        background: BackgroundTasks,
    ) -> Job:
        JobService._assert_project(db, project_id)
        out_dir = files.ensure_output_dir("generated")
        out_file = files.infer_output_path(out_dir, input_path, qa_type)

        cfg = {
            "qa_type": qa_type,
            "num_pairs": num_pairs,
            "temperature": temperature,
            "chunk_size": chunk_size,
            "max_tokens": max_tokens,
            "overlap": overlap,
            "custom_prompts": bool(prompts_json),
        }
        job = _new_job(db, project_id, "create", input_path, str(out_file), cfg)

        args = [input_path, "--type", qa_type, "--output-dir", str(out_dir)]
        if num_pairs:
            args += ["-n", str(num_pairs)]
        if temperature is not None:
            args += ["--temperature", str(temperature)]
        if chunk_size is not None:
            args += ["--chunk-size", str(chunk_size)]
        if max_tokens is not None:
            args += ["--max-tokens", str(max_tokens)]
        if overlap is not None:
            args += ["--overlap", str(overlap)]
        if prompts_json:
            prompts_file = out_dir / f"prompts_{job.id}.json"
            prompts_file.write_text(prompts_json)
            args += ["--prompts-file", str(prompts_file)]

            # ensure file cleanup afterwards inside SDKService or here after run
        background.add_task(SDKService.run, job, "create", args, db)
        return job

    # -------------------- CURATE --------------------
    @staticmethod
    def queue_curate(
        db: Session,
        project_id: str,
        input_path: str,
        threshold: float | None,
        batch_size: int | None,
        background: BackgroundTasks,
    ) -> Job:
        JobService._assert_project(db, project_id)
        out_dir = files.ensure_output_dir("cleaned")
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_file = out_dir / f"{Path(input_path).stem}_{ts}_curated.json"
        cfg = {"threshold": threshold, "batch_size": batch_size}
        job = _new_job(db, project_id, "curate", input_path, str(out_file), cfg)
        args = [input_path]
        if threshold is not None:
            args += ["-t", str(threshold)]
        if batch_size is not None:
            args += ["-b", str(batch_size)]
        background.add_task(SDKService.run, job, "curate", args, db)
        return job

    @staticmethod
    def queue_curate_auto(
        db: Session,
        project_id: str,
        threshold: float | None,
        batch_size: int | None,
        background: BackgroundTasks,
    ) -> Job:
        create_job = (
            db.query(Job)
            .filter(
                Job.project_id == project_id,
                Job.job_type == "create",
                Job.status == "completed",
            )
            .order_by(Job.created_at.desc())
            .first()
        )
        if not create_job or not create_job.output_file or not Path(create_job.output_file).exists():
            raise HTTPException(404, "No completed create job found")
        return JobService.queue_curate(
            db,
            project_id,
            create_job.output_file,
            threshold,
            batch_size,
            background,
        )

    # -------------------- SAVE AS --------------------
    @staticmethod
    def queue_save_as(
        db: Session,
        project_id: str,
        input_path: str,
        fmt: str,
        storage: str | None,
        output_name: str | None,
        background: BackgroundTasks,
    ) -> Job:
        JobService._assert_project(db, project_id)
        out_dir = files.ensure_output_dir("final")
        base = output_name or Path(input_path).stem
        out_file = out_dir / f"{base}_{fmt}.{ 'jsonl' if fmt in ['alpaca','llama'] else fmt }"
        cfg = {"format": fmt, "storage": storage, "output_name": output_name}
        job = _new_job(db, project_id, "save-as", input_path, str(out_file), cfg)
        args = [input_path, "-f", fmt]
        if storage:
            args += ["--storage", storage]
        if output_name:
            args += ["--output", output_name]
        background.add_task(SDKService.run, job, "save-as", args, db)
        return job

    @staticmethod
    def queue_save_as_auto(
        db: Session,
        project_id: str,
        fmt: str,
        storage: str | None,
        output_name: str | None,
        source_type: Literal["curate", "create"],
        background: BackgroundTasks,
    ) -> Job:
        source_job = (
            db.query(Job)
            .filter(
                Job.project_id == project_id,
                Job.job_type == source_type,
                Job.status == "completed",
            )
            .order_by(Job.created_at.desc())
            .first()
        )
        if not source_job or not source_job.output_file or not Path(source_job.output_file).exists():
            raise HTTPException(404, f"No completed {source_type} job found")
        return JobService.queue_save_as(
            db,
            project_id,
            source_job.output_file,
            fmt,
            storage,
            output_name,
            background,
        )

    # -------------------- CRUD helpers --------------------
    @staticmethod
    def get_job(db: Session, job_id: str) -> Job | None:
        return db.get(Job, job_id)

    @staticmethod
    def delete_job(db: Session, job_id: str) -> bool:
        job = JobService.get_job(db, job_id)
        if not job:
            return False
        db.delete(job)
        db.commit()
        return True

    @staticmethod
    def list_jobs(
        db: Session,
        project_id: str | None,
        status: str | None,
        job_type: str | None,
        skip: int,
        limit: int,
    ) -> List[Job]:
        q = db.query(Job)
        if project_id:
            q = q.filter(Job.project_id == project_id)
        if status:
            q = q.filter(Job.status == status)
        if job_type:
            q = q.filter(Job.job_type == job_type)
        return q.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    # -------------------- Download & Preview --------------------

    @staticmethod
    def preview_job(db: Session, job_id: str):
        job = JobService.get_job(db, job_id)
        if not job or not job.output_file or not Path(job.output_file).exists():
            raise HTTPException(404, "Output file not found")
        path = Path(job.output_file)
        ext = path.suffix
        try:
            if ext == ".json":
                data = json.loads(path.read_text())
                preview = json.dumps(data[:5] if isinstance(data, list) else data, indent=2)[:2000]
            elif ext == ".jsonl":
                preview = "\n".join(path.read_text().splitlines()[:5])
            else:
                preview = "\n".join(path.read_text().splitlines()[:20])
            return {
                "filename": path.name,
                "preview": preview,
                "format": ext.lstrip("."),
                "size": path.stat().st_size,
            }
        except Exception as exc:
            raise HTTPException(500, f"Error previewing file: {exc}")

    @staticmethod
    def download_job_json(db: Session, job_id: str):
        job = JobService.get_job(db, job_id)
        if not job or not job.output_file or not Path(job.output_file).exists():
            raise HTTPException(404, "Output file not found")
        content = Path(job.output_file).read_text()
        return JSONResponse(content={"filename": Path(job.output_file).name, "content": content})

    @staticmethod
    def download_job_file(db: Session, job_id: str):
        job = JobService.get_job(db, job_id)
        if not job or not job.output_file or not Path(job.output_file).exists():
            raise HTTPException(404, "Output file not found")
        return FileResponse(path=job.output_file, filename=Path(job.output_file).name)

    # -------------------- internal --------------------
    @staticmethod
    def _assert_project(db: Session, project_id: str):
        if not db.get(Project, project_id):
            raise HTTPException(404, "Project not found")
