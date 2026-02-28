from pathlib import Path

import pytest
from fastapi import HTTPException

from backend.services import files
from backend.settings import settings


@pytest.fixture
def isolated_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project_root = tmp_path / "repo"
    backend_dir = project_root / "backend"
    data_dir = project_root / "data"

    (data_dir / "output").mkdir(parents=True, exist_ok=True)
    (backend_dir / "data").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "project_root", project_root)
    monkeypatch.setattr(settings, "backend_dir", backend_dir)
    monkeypatch.setattr(settings, "data_dir", data_dir)

    return {
        "project_root": project_root,
        "backend_dir": backend_dir,
        "data_dir": data_dir,
    }


def test_normalise_or_404_accepts_supported_data_paths(isolated_paths):
    target = isolated_paths["data_dir"] / "output" / "example.txt"
    target.write_text("ok", encoding="utf-8")

    resolved = files.normalise_or_404("backend/data/output/example.txt")
    assert resolved == str(target.resolve())


def test_normalise_or_404_rejects_paths_outside_data_roots(isolated_paths):
    with pytest.raises(HTTPException) as exc:
        files.normalise_or_404("/etc/passwd")
    assert exc.value.status_code == 400


def test_sanitise_filename_removes_traversal_and_invalid_chars():
    assert files.sanitise_filename("../unsafe?.txt") == "unsafe_.txt"
    assert files.sanitise_filename("") == "upload.txt"
