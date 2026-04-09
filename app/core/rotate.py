from PIL import Image
from . import utils


def rotate_image(src: str, dest: str, angle: int = 0,
                 flip_h: bool = False, flip_v: bool = False,
                 bg_color: tuple = (255, 255, 255)):
    """angle: one of 0, 90, 180, 270 (CW) — or any custom int for arbitrary rotation."""
    with Image.open(src) as im:
        original_format = (im.format or "PNG").upper()
        out = im.copy()

        if flip_h:
            out = out.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_v:
            out = out.transpose(Image.FLIP_TOP_BOTTOM)

        a = angle % 360
        if a == 90:
            out = out.transpose(Image.ROTATE_270)  # 90° clockwise
        elif a == 180:
            out = out.transpose(Image.ROTATE_180)
        elif a == 270:
            out = out.transpose(Image.ROTATE_90)   # 90° counter-clockwise
        elif a != 0:
            # arbitrary rotation — negative for clockwise in PIL
            fill = bg_color + (255,) if out.mode == "RGBA" else bg_color
            out = out.rotate(-a, resample=Image.BICUBIC, expand=True, fillcolor=fill)

        save_kwargs = {}
        fmt = original_format
        if fmt in ("JPEG", "JPG"):
            if out.mode != "RGB":
                bg = Image.new("RGB", out.size, bg_color)
                if out.mode in ("RGBA", "LA"):
                    bg.paste(out, mask=out.split()[-1])
                    out = bg
                else:
                    out = out.convert("RGB")
            save_kwargs.update(quality=92, optimize=True)
            fmt = "JPEG"
        out.save(dest, format=fmt, **save_kwargs)


def run_rotate_batch(files, out_root, angle, flip_h, flip_v, bg_color,
                     progress_cb=None, log_cb=None, cancel_cb=None):
    total = len(files)
    done = 0
    for f in files:
        if cancel_cb and cancel_cb():
            break
        try:
            dest = utils.flat_output_path(f, out_root)
            rotate_image(f, dest, angle=angle, flip_h=flip_h, flip_v=flip_v, bg_color=bg_color)
            if log_cb:
                log_cb(f"OK   {f}")
        except Exception as e:
            if log_cb:
                log_cb(f"FAIL {f} — {e}")
        done += 1
        if progress_cb:
            progress_cb(done, total)
    return done
