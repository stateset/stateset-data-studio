from __future__ import annotations

"""Thin wrapper around the *synthetic‑data‑kit* CLI.

`SDKService.run` executes a CLI command **synchronously** inside a
`BackgroundTasks` worker (or Celery task if you swap it later), updates the
`Job` row, infers/validates the output file, and stores basic statistics via
`services.stats.extract_stats`.
"""

import logging
import os
import shlex
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from backend.db.models import Job
from backend.services import stats, files
from backend.settings import settings

log = logging.getLogger(__name__)

BIN = settings.sdk_bin  # e.g. "synthetic-data-kit"
RECENT_WINDOW = timedelta(minutes=5)  # search window to detect output files


class SDKService:
    @staticmethod
    def run(job: Job, command: str, args: List[str], db: Session):
        """Run *synthetic‑data‑kit* <command> <args> and persist result in DB.

        Parameters
        ----------
        job : Job            # SQLAlchemy row (already in DB)
        command : str        # ingest / create / curate / save-as
        args : list[str]     # list of CLI args (no command/BIN included)
        db   : Session       # open SQLAlchemy session (same instance as API)
        """
        job.status = "running"
        job.updated_at = datetime.utcnow()
        db.commit()

        cmd = [BIN, command, *args]
        log.info("[SDK] %s", shlex.join(cmd))

        try:
            completed = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            log.debug("[SDK] stdout: %s", completed.stdout[:500])
        except subprocess.CalledProcessError as exc:
            job.status = "failed"
            job.error = exc.stderr or exc.stdout or str(exc)
            job.updated_at = datetime.utcnow()
            db.commit()
            log.error("[SDK] command failed – %s", job.error)
            return

        # ------------------------------------------------------------------
        # Infer / validate output file → stats
        # ------------------------------------------------------------------
        SDKService._finalise_job_output(job, command, args, db)

    # ----------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------

    @staticmethod
    def _finalise_job_output(job: Job, command: str, args: List[str], db: Session):
        """Detect the output artifact & fill stats/error fields."""
        output_path: Path | None = Path(job.output_file) if job.output_file else None

        # If caller pre‑filled output_file we trust it; otherwise attempt to find
        if output_path and output_path.exists():
            pass  # good
        else:
            output_path = SDKService._guess_output_path(command, args)

        if output_path and output_path.exists():
            job.output_file = str(output_path)
            try:
                job.stats = stats.extract_stats(output_path)
            except Exception as exc:
                job.error = f"stat‑extract failed: {exc}"
        else:
            job.error = f"output file not found (command={command})"

        job.status = "completed" if not job.error else "warning"
        job.updated_at = datetime.utcnow()
        db.commit()

    # ------------------------------------------------------------------
    # Heuristics – same ideas as original monolith but drastically shorter
    # ------------------------------------------------------------------

    @staticmethod
    def _guess_output_path(command: str, args: List[str]) -> Path | None:
        now = datetime.utcnow()
        data_root = settings.data_dir

        def recent_files(folder: Path, suffix: tuple[str, ...]):
            if not folder.exists():
                return []
            return [
                f
                for f in folder.iterdir()
                if f.suffix in suffix and now - datetime.fromtimestamp(f.stat().st_mtime) < RECENT_WINDOW
            ]

        if command == "ingest":
            return next(iter(recent_files(data_root / "output", (".txt",))), None)
        if command == "create":
            return next(iter(recent_files(data_root / "generated", (".json",))), None)
        if command == "curate":
            return next(iter(recent_files(data_root / "cleaned", (".json",))), None)
        if command == "save-as":
            return next(iter(recent_files(data_root / "final", (".json", ".jsonl", ".csv"))), None)
        return None
