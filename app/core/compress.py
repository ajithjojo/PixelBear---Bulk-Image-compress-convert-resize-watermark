import io

from PIL import Image
from . import utils


def _apply_compress_save(im: Image.Image, target, quality: int, fmt: str):
    """Shared save logic. `target` may be a path str or a file-like (BytesIO)."""
    save_kwargs = {}
    fmt_u = fmt.upper()

    if fmt_u in ("JPEG", "JPG"):
        if im.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            if im.mode == "P":
                im = im.convert("RGBA")
            bg.paste(im, mask=im.split()[-1] if im.mode in ("RGBA", "LA") else None)
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        save_kwargs.update(quality=quality, optimize=True, progressive=True)
        fmt_u = "JPEG"

    elif fmt_u == "WEBP":
        save_kwargs.update(quality=quality, method=6)

    elif fmt_u == "PNG":
        save_kwargs.update(optimize=True)

    im.save(target, format=fmt_u, **save_kwargs)


def estimate_compress_size(src: str, quality: int, fmt: str) -> int:
    """Return the byte size that compressing `src` would produce (without writing to disk)."""
    with Image.open(src) as im:
        im.load()
        buf = io.BytesIO()
        _apply_compress_save(im, buf, quality, fmt)
        return buf.tell()


def compress_image(src: str, dest: str, quality: int = 80, fmt: str = "JPEG"):
    with Image.open(src) as im:
        _apply_compress_save(im, dest, quality, fmt)


def run_compress_batch(files, out_root, quality, fmt,
                       progress_cb=None, log_cb=None, cancel_cb=None):
    ext_map = {"JPEG": ".jpg", "WEBP": ".webp", "PNG": ".png"}
    new_ext = ext_map.get(fmt.upper())
    total = len(files)
    done = 0
    for f in files:
        if cancel_cb and cancel_cb():
            break
        try:
            dest = utils.flat_output_path(f, out_root, new_ext=new_ext)
            compress_image(f, dest, quality=quality, fmt=fmt)
            if log_cb:
                log_cb(f"OK   {f}")
        except Exception as e:
            if log_cb:
                log_cb(f"FAIL {f} — {e}")
        done += 1
        if progress_cb:
            progress_cb(done, total)
    return done
