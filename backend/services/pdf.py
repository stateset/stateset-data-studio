from __future__ import annotations

"""PDF → text helper used by ingest flow.

Try *pdftotext* first (Poppler); fall back to **PyPDF2**.  Returns
`(output_path, err)` – where `err is None` on success.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional

log = logging.getLogger(__name__)

__all__ = ["convert_pdf_to_text"]

DEFAULT_TIMEOUT = 120  # seconds


def _run_pdftotext(pdf: Path, out: Path) -> bool:
    """Return True if poppler's pdftotext succeeds and writes a non-empty file."""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf), str(out)],
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT,
            check=True,
        )
        if out.exists() and out.stat().st_size > 0:
            return True
        log.warning("pdftotext produced no output – stderr: %s", result.stderr.strip())
        return False
    except FileNotFoundError:
        log.debug("pdftotext not installed")
    except subprocess.TimeoutExpired:
        log.warning("pdftotext timed-out after %ss", DEFAULT_TIMEOUT)
    except subprocess.CalledProcessError as e:
        log.warning("pdftotext failed (exit=%s): %s", e.returncode, e.stderr.strip())
    except Exception as exc:
        log.exception("pdftotext unexpected error: %s", exc)
    return False


def _run_pypdf2(pdf: Path, out: Path) -> bool:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        log.debug("PyPDF2 not available")
        return False

    try:
        reader = PdfReader(str(pdf))
        text_parts: list[str] = []
        for page in reader.pages:
            try:
                txt = page.extract_text() or ""
            except Exception as page_err:  # pragma: no cover
                log.debug("extract_text error on page: %s", page_err)
                txt = "[page-error]"
            text_parts.append(txt.strip())
        content = "\n\n".join(text_parts).strip()
        if not content:
            return False
        out.write_text(content, encoding="utf-8")
        return True
    except Exception as exc:
        log.exception("PyPDF2 failed: %s", exc)
        return False


def convert_pdf_to_text(pdf_path: str | Path, output_txt_path: str | Path) -> Tuple[Optional[str], Optional[str]]:
    pdf = Path(pdf_path)
    out = Path(output_txt_path)

    if not pdf.exists():
        return None, f"Input PDF not found: {pdf}"

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return None, f"Cannot create output directory {out.parent}: {e}"

    if _run_pdftotext(pdf, out) or _run_pypdf2(pdf, out):
        log.info("PDF → text ok: %s", out)
        return str(out), None

    log.error("Failed to extract text from %s", pdf)
    return None, "Failed with both pdftotext and PyPDF2"