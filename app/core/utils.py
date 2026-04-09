import os
from pathlib import Path

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif"}


def list_images(folder: str, recursive: bool = False):
    """Return a list of image file paths inside `folder`."""
    p = Path(folder)
    if not p.exists() or not p.is_dir():
        return []
    it = p.rglob("*") if recursive else p.glob("*")
    return [str(f) for f in it if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS]


def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def flat_output_path(src: str, out_root: str, new_ext: str | None = None) -> str:
    """Place file inside out_root using its basename. If name collides, append _1, _2..."""
    ensure_dir(out_root)
    stem = Path(src).stem
    ext = new_ext if new_ext else Path(src).suffix
    if not ext.startswith("."):
        ext = "." + ext
    dest = Path(out_root) / f"{stem}{ext}"
    i = 1
    while dest.exists():
        dest = Path(out_root) / f"{stem}_{i}{ext}"
        i += 1
    return str(dest)
