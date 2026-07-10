import os
import sys
import glob

from PIL import ImageFont

_FALLBACK_CANDIDATES = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf"]

_windows_font_map = None
_unix_font_map = None


def _build_windows_font_map():
    import winreg

    fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    mapping = {}
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        )
    except OSError:
        return mapping

    with key:
        i = 0
        while True:
            try:
                name, filename, _ = winreg.EnumValue(key, i)
            except OSError:
                break
            i += 1
            display = name
            for suffix in (" (TrueType)", " (OpenType)"):
                if display.endswith(suffix):
                    display = display[: -len(suffix)]
            path = filename if os.path.isabs(filename) else os.path.join(fonts_dir, filename)
            mapping[display.strip().lower()] = path

    return mapping


def _build_unix_font_map():
    search_dirs = [
        "/System/Library/Fonts",
        "/Library/Fonts",
        os.path.expanduser("~/Library/Fonts"),
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        os.path.expanduser("~/.fonts"),
    ]
    mapping = {}
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for path in glob.glob(os.path.join(d, "**", "*.[to]tf"), recursive=True):
            stem = os.path.splitext(os.path.basename(path))[0]
            key = stem.replace("-", " ").replace("_", " ").strip().lower()
            mapping.setdefault(key, path)
    return mapping


def resolve_font_path(family: str) -> str | None:
    if not family:
        return None

    global _windows_font_map, _unix_font_map
    key = family.strip().lower()

    if sys.platform.startswith("win"):
        if _windows_font_map is None:
            _windows_font_map = _build_windows_font_map()
        mapping = _windows_font_map
    else:
        if _unix_font_map is None:
            _unix_font_map = _build_unix_font_map()
        mapping = _unix_font_map

    if key in mapping:
        return mapping[key]

    for cand_key, path in mapping.items():
        if cand_key.startswith(key) or key.startswith(cand_key):
            return path

    return None


def load_font(family: str, size_px: int) -> ImageFont.FreeTypeFont:
    size_px = max(1, int(size_px))

    path = resolve_font_path(family)
    if path:
        try:
            return ImageFont.truetype(path, size_px)
        except Exception:
            pass

    for candidate in _FALLBACK_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size_px)
        except Exception:
            continue

    return ImageFont.load_default()
