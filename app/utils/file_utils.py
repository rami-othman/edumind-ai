"""Shared file utilities."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import UploadFile


def sanitize_filename(filename: str) -> str:
    """Return a safe basename for a user-provided filename."""

    safe_name = Path(filename).name
    safe_name = re.sub(r"[^\w.\-]+", "_", safe_name, flags=re.UNICODE)
    safe_name = safe_name.strip("._")
    if not safe_name:
        raise ValueError("uploaded filename is invalid")

    return safe_name


def build_unique_upload_path(upload_dir: str | Path, filename: str) -> Path:
    """Build a path under upload_dir without overwriting an existing file."""

    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(filename)
    candidate = upload_path / safe_name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        next_candidate = upload_path / f"{stem}_{counter}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        counter += 1


def save_upload_file_chunked(upload_file: UploadFile, destination: str | Path) -> Path:
    """Save an uploaded file in chunks and return the destination path."""

    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    with destination_path.open("wb") as output_file:
        while chunk := upload_file.file.read(1024 * 1024):
            output_file.write(chunk)

    return destination_path
