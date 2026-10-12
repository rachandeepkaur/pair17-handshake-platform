import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import BadRequestError, NotFoundError

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
RESUME_DIR = UPLOAD_ROOT / "resumes"
PICTURE_DIR = UPLOAD_ROOT / "profile_pictures"

MAX_PICTURE_BYTES = 2 * 1024 * 1024

# Checked against the file's leading bytes, not the client-supplied
# content type, so a renamed non-image file is rejected.
_IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
}


def ensure_upload_dirs() -> None:
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    PICTURE_DIR.mkdir(parents=True, exist_ok=True)


def _image_extension(data: bytes) -> str | None:
    for signature, extension in _IMAGE_SIGNATURES.items():
        if data.startswith(signature):
            return extension
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


async def save_profile_picture(upload: UploadFile) -> str:
    """Validate and store an image; return its path relative to UPLOAD_ROOT."""

    data = await upload.read(MAX_PICTURE_BYTES + 1)
    if not data:
        raise BadRequestError("The uploaded file is empty")
    if len(data) > MAX_PICTURE_BYTES:
        raise BadRequestError("Profile picture must be 2 MB or smaller")

    extension = _image_extension(data)
    if extension is None:
        raise BadRequestError("Profile picture must be a JPEG, PNG, or WebP image")

    ensure_upload_dirs()
    filename = f"{uuid.uuid4().hex}{extension}"
    (PICTURE_DIR / filename).write_bytes(data)
    return f"profile_pictures/{filename}"


def delete_upload(relative_path: str | None) -> None:
    if not relative_path:
        return
    path = (UPLOAD_ROOT / relative_path).resolve()
    if path.is_relative_to(UPLOAD_ROOT) and path.is_file():
        path.unlink()


def picture_url(relative_path: str | None) -> str | None:
    return f"/uploads/{relative_path}" if relative_path else None


def resolve_resume(relative_path: str) -> Path:
    """Return the absolute resume path, refusing anything outside RESUME_DIR."""

    path = (UPLOAD_ROOT / relative_path).resolve()
    if not path.is_relative_to(RESUME_DIR.resolve()) or not path.is_file():
        raise NotFoundError("Resume file not found")
    return path
