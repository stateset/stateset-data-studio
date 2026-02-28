"""files.py — shared helper functions (pure python, testable)"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException

from backend.settings import settings

log = logging.getLogger(__name__)

ALLOWED_EXT: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".html": "html",
    ".htm": "html",
    ".txt": "txt",
    ".md": "txt",
    ".rst": "txt",
}


def _data_roots() -> tuple[Path, ...]:
    roots = {
        settings.data_dir.resolve(),
        (settings.backend_dir / "data").resolve(),
    }
    return tuple(sorted(roots, key=str))


def _is_within_roots(path: Path) -> bool:
    for root in _data_roots():
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def sanitise_filename(filename: str, default: str = "upload.txt") -> str:
    """Return a filename safe for local filesystem writes."""
    basename = Path(filename or "").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", basename).strip("._")
    if not cleaned:
        return default
    return cleaned[:200]


def safe_save_json(data: Any, dst: str | os.PathLike) -> str:
    """Atomically dump *data* to *dst* as UTF‑8 JSON.

    Guarantees that either the old file stays intact or the new file is
    completely written (no half‑files if the process crashes).
    Returns the absolute path of the written file.
    """
    dst_path = Path(dst).expanduser().resolve()
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # write to tmp then move
    with tempfile.NamedTemporaryFile("w", delete=False, dir=dst_path.parent, suffix=".tmp", encoding="utf-8") as tmp:
        json.dump(data, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)

    shutil.move(str(tmp_path), dst_path)
    size = dst_path.stat().st_size
    log.info("saved %s (%d bytes)", dst_path, size)
    return str(dst_path)

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def normalise_path(p: str | Path) -> Path:
    """Normalise to a path under allowed data roots."""
    raw = str(p).strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Path is required")

    rel = raw[len("backend/") :] if raw.startswith("backend/") else raw

    candidates: list[Path] = []
    in_path = Path(rel)
    if in_path.is_absolute():
        candidates.append(in_path)
    else:
        candidates.extend(
            [
                settings.project_root / rel,
                settings.backend_dir / rel,
                Path(rel),
            ]
        )

    safe_candidates: list[Path] = []
    for candidate in candidates:
        resolved = candidate.expanduser().resolve(strict=False)
        if _is_within_roots(resolved):
            safe_candidates.append(resolved)

    if not safe_candidates:
        raise HTTPException(
            status_code=400,
            detail=f"Path '{p}' must be within data directories",
        )

    existing = next((c for c in safe_candidates if c.exists()), None)
    return existing or safe_candidates[0]


def normalise_or_404(path: str | Path) -> str:  # fastapi-style helper
    p = normalise_path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return str(p)

# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def ensure_output_dir(label: Literal["generated", "cleaned", "final", "output", "uploads"]):
    if label not in {"generated", "cleaned", "final", "output", "uploads"}:
        raise ValueError(f"Invalid output dir label: {label}")
    dir_ = settings.data_dir / label
    dir_.mkdir(parents=True, exist_ok=True)
    return dir_.resolve()


def infer_output_path(out_dir: Path, input_path: str | Path, qa_type: str):
    base = Path(input_path).stem.replace(" ", "_")
    return out_dir / f"{base}_{qa_type}_pairs.json"

# ---------------------------------------------------------------------------
# File‑type + PDF→TXT
# ---------------------------------------------------------------------------

def get_file_type(filename: str) -> str:
    return ALLOWED_EXT.get(Path(filename).suffix.lower(), "unknown")


def convert_pdf_to_text(pdf_path: str | Path, out_path: str | Path) -> bool:
    pdf_path, out_path = Path(pdf_path), Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1️⃣ poppler ‑ pdftotext
    try:
        subprocess.run(["pdftotext", str(pdf_path), str(out_path)], check=True)
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception:
        pass

    # 2️⃣ pure‑python fallback (PyPDF2)
    try:
        from PyPDF2 import PdfReader
        txt = "".join(p.extract_text() or "" for p in PdfReader(str(pdf_path)).pages)
        out_path.write_text(txt, encoding="utf-8")
        return out_path.stat().st_size > 0
    except Exception:
        return False
