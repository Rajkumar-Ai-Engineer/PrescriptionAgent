import base64
import mimetypes
from pathlib import Path

SUPPORTED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
SUPPORTED_PDF_EXT = {".pdf"}


def encode_file(path: Path) -> tuple[str, str]:
    """Read a file and return (base64_data, media_type)."""
    media_type, _ = mimetypes.guess_type(str(path))
    if media_type is None:
        media_type = "application/pdf" if path.suffix.lower() == ".pdf" else "image/png"
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def build_content_block(path: Path) -> dict:
    """Build a litellm-compatible message content block for an image or PDF file."""
    data, media_type = encode_file(path)
    ext = path.suffix.lower()
    if ext in SUPPORTED_IMAGE_EXT:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{media_type};base64,{data}"},
        }
    if ext in SUPPORTED_PDF_EXT:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:application/pdf;base64,{data}"},
        }
    raise ValueError(f"Unsupported file type: {ext}")


def gather_files(input_path: Path) -> list[Path]:
    """Return a list of supported image/PDF files from a file path or directory."""
    exts = SUPPORTED_IMAGE_EXT | SUPPORTED_PDF_EXT
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(
            p for p in input_path.iterdir() if p.suffix.lower() in exts and p.is_file()
        )
    raise FileNotFoundError(f"No such file or directory: {input_path}")
