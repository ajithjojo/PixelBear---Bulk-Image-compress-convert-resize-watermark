import io

from PIL import Image
from . import utils


def compute_new_size(ow: int, oh: int, mode: str, width: int | None, height: int | None,
                     percent: int | None, keep_aspect: bool) -> tuple[int, int]:
    if mode == "percent" and percent:
        return max(1, int(ow * percent / 100)), max(1, int(oh * percent / 100))
    if keep_aspect:
        if width and not height:
            return width, max(1, int(oh * width / ow))
        if height and not width:
            return max(1, int(ow * height / oh)), height
        if width and height:
            ratio = min(width / ow, height / oh)
            return max(1, int(ow * ratio)), max(1, int(oh * ratio))
        return ow, oh
    return width or ow, height or oh


def _apply_resize_save(im: Image.Image, target, mode, width, height, percent, keep_aspect):
    nw, nh = compute_new_size(im.width, im.height, mode, width, height, percent, keep_aspect)
    resized = im.resize((nw, nh), Image.LANCZOS)
    save_kwargs = {}
    fmt = (im.format or "PNG").upper()
    if fmt in ("JPEG", "JPG"):
        if resized.mode != "RGB":
            resized = resized.convert("RGB")
        save_kwargs.update(quality=92, optimize=True)
    resized.save(target, format=fmt, **save_kwargs)


def estimate_resize_size(src: str, mode: str, width: int | None, height: int | None,
                         percent: int | None, keep_aspect: bool) -> int:
    with Image.open(src) as im:
        im.load()
        buf = io.BytesIO()
        _apply_resize_save(im, buf, mode, width, height, percent, keep_aspect)
        return buf.tell()


def resize_image(src: str, dest: str, mode: str, width: int | None, height: int | None,
                 percent: int | None, keep_aspect: bool = True):
    with Image.open(src) as im:
        _apply_resize_save(im, dest, mode, width, height, percent, keep_aspect)


def run_resize_batch(files, out_root, mode, width, height, percent, keep_aspect,
                     progress_cb=None, log_cb=None, cancel_cb=None):
    total = len(files)
    done = 0
    for f in files:
        if cancel_cb and cancel_cb():
            break
        try:
            dest = utils.flat_output_path(f, out_root)
            resize_image(f, dest, mode, width, height, percent, keep_aspect)
            if log_cb:
                log_cb(f"OK   {f}")
        except Exception as e:
            if log_cb:
                log_cb(f"FAIL {f} — {e}")
        done += 1
        if progress_cb:
            progress_cb(done, total)
    return done
