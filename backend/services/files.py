"""files.py — shared helper functions (pure python, testable)"""
from __future__ import annotations

import os, shutil, subprocess, uuid, logging
import json, os, tempfile, shutil
from typing import Any
from pathlib import Path
from typing import Literal
from functools import lru_cache

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
    """Return first existing Path variant or original Path."""
    p = Path(p)
    candidates: list[Path] = [p]

    # handle `backend/` prefix variations
    if str(p).startswith("backend/"):
        candidates.append(settings.project_root / p.relative_to("backend"))
    else:
        candidates.append(settings.backend_dir / p)

    # absolute within project root
    candidates.append(settings.project_root / p)
    candidates.append(settings.backend_dir / p)

    for c in candidates:
        if c.exists():
            return c.resolve()
    return p


def normalise_or_404(path: str | Path):  # fastapi-style helper
    from fastapi import HTTPException
    p = normalise_path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return str(p)

# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def ensure_output_dir(label: Literal["generated", "cleaned", "final", "output", "uploads"]):
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
