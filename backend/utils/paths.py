from pathlib import Path
from settings import settings

def normalise_path(p: str | Path) -> Path:
    """Try several variants until an existing path is found, else return original Path."""
    p = Path(p)
    variants: list[Path] = [p]

    if str(p).startswith("backend/"):
        variants.append(settings.project_root / p.relative_to("backend"))
    else:
        variants.append(settings.backend_dir / p)

    variants.append(settings.project_root / p)
    variants.append(settings.backend_dir / p)

    for candidate in variants:
        if candidate.exists():
            return candidate.resolve()

    return p  # let caller handle non-existent file
