from __future__ import annotations

"""Periodic job‑watchdog.

* marks jobs stuck in `running` > N minutes → `failed`
* keeps lightweight counters for `/system/health`
* does *not* spin a thread on import – caller must invoke `start()` from
  `main.py` (e.g. app startup event) to avoid duplicated workers when the
  server is run with multiple processes (gunicorn/uvicorn --workers).
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from sqlalchemy.orm import Session

from db import SessionLocal
from db.models import Job
from settings import settings

log = logging.getLogger(__name__)

CHECK_EVERY = 300  # seconds
TIMEOUT = timedelta(minutes=60)  # running → failed after 60min

_stats: dict[str, Dict] = {}
_started = False


def _scan():
    """One sweep: mark stalled jobs + refresh in‑mem stats dict."""
    global _stats
    now = datetime.utcnow()
    cutoff = now - TIMEOUT

    with SessionLocal() as db:
        # 1. timeout running jobs ------------------------------------------
        stalled = (
            db.query(Job)
            .filter(Job.status == "running", Job.updated_at < cutoff)
            .all()
        )
        if stalled:
            log.warning("Marking %d stalled jobs → failed", len(stalled))
            for j in stalled:
                j.status = "failed"
                j.error = "Timed‑out by monitor"
                j.updated_at = now
            db.commit()

        # 2. recalc stats ---------------------------------------------------
        by_status = {
            row.status: row.count
            for row in db.query(Job.status, Job.id.count()).group_by(Job.status).all()
        }
        by_type = {
            row.job_type: row.count
            for row in db.query(Job.job_type, Job.id.count()).group_by(Job.job_type).all()
        }
        failures = (
            db.query(Job.id, Job.job_type, Job.error)
            .filter(Job.status == "failed")
            .order_by(Job.updated_at.desc())
            .limit(5)
            .all()
        )
        _stats = {
            "by_status": by_status,
            "by_type": by_type,
            "recent_failures": [
                {"id": j.id, "job_type": j.job_type, "error": j.error} for j in failures
            ],
            "timestamp": now.isoformat(),
        }


def _loop():
    log.info("Job‑monitor thread running (interval=%ss)", CHECK_EVERY)
    while True:
        try:
            _scan()
        except Exception as exc:
            log.exception("job‑monitor sweep failed: %s", exc)
        time.sleep(CHECK_EVERY)


def start():
    """Launch background watcher (safe to call multiple times)."""
    global _started
    if _started:
        return
    t = threading.Thread(target=_loop, daemon=True, name="job‑monitor")
    t.start()
    _started = True


def stats() -> dict:
    """Return last cached stats for /system/health."""
    return _stats.copy()
