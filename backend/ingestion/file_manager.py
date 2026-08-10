from pathlib import Path
import shutil

from backend.config import ALLOWED_FILES, DEMO_DATA_DIR, MAX_UPLOAD_SIZE_MB, UPLOAD_DIR


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)


def list_sources() -> list[str]:
    ensure_dirs()
    return sorted(path.name for path in UPLOAD_DIR.glob("*.csv") if path.name in ALLOWED_FILES)


def source_dir() -> Path:
    ensure_dirs()
    if not list_sources():
        reset_to_demo()
    return UPLOAD_DIR


def save_upload(filename: str, content: bytes) -> dict[str, str]:
    ensure_dirs()
    safe_name = Path(filename).name
    if safe_name not in ALLOWED_FILES:
        raise ValueError(f"Unsupported file '{safe_name}'. Allowed files: {sorted(ALLOWED_FILES)}")
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValueError(f"{safe_name} exceeds MAX_UPLOAD_SIZE_MB={MAX_UPLOAD_SIZE_MB}")
    (UPLOAD_DIR / safe_name).write_bytes(content)
    return {"filename": safe_name, "status": "added_to_source_collection"}


def remove_upload(filename: str) -> dict[str, str]:
    ensure_dirs()
    safe_name = Path(filename).name
    if safe_name not in ALLOWED_FILES:
        raise ValueError(f"Unsupported file '{safe_name}'")
    path = UPLOAD_DIR / safe_name
    if path.exists():
        path.unlink()
    return {"filename": safe_name, "status": "removed_from_source_collection"}


def reset_to_demo() -> list[str]:
    ensure_dirs()
    for path in UPLOAD_DIR.glob("*.csv"):
        path.unlink()
    for path in DEMO_DATA_DIR.glob("*.csv"):
        if path.name in ALLOWED_FILES:
            shutil.copy2(path, UPLOAD_DIR / path.name)
    return list_sources()
