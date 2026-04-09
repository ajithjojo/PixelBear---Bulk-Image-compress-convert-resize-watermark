from PIL import Image
from . import utils


def convert_image(src: str, dest: str, fmt: str, quality: int = 90,
                  bg_color: tuple = (255, 255, 255)):
    fmt_u = fmt.upper()
    if fmt_u == "JPG":
        fmt_u = "JPEG"

    with Image.open(src) as im:
        save_kwargs = {}

        if fmt_u == "JPEG":
            if im.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", im.size, bg_color)
                if im.mode == "P":
                    im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1] if im.mode in ("RGBA", "LA") else None)
                im = bg
            elif im.mode != "RGB":
                im = im.convert("RGB")
            save_kwargs.update(quality=quality, optimize=True, progressive=True)

        elif fmt_u == "WEBP":
            save_kwargs.update(quality=quality, method=6)

        elif fmt_u == "PNG":
            if im.mode == "P":
                im = im.convert("RGBA")
            save_kwargs.update(optimize=True)

        im.save(dest, format=fmt_u, **save_kwargs)


def run_convert_batch(files, out_root, fmt, quality, bg_color,
                      progress_cb=None, log_cb=None, cancel_cb=None):
    ext_map = {"JPEG": ".jpg", "WEBP": ".webp", "PNG": ".png"}
    new_ext = ext_map.get(fmt.upper(), ".jpg")
    total = len(files)
    done = 0
    for f in files:
        if cancel_cb and cancel_cb():
            break
        try:
            dest = utils.flat_output_path(f, out_root, new_ext=new_ext)
            convert_image(f, dest, fmt=fmt, quality=quality, bg_color=bg_color)
            if log_cb:
                log_cb(f"OK   {f}")
        except Exception as e:
            if log_cb:
                log_cb(f"FAIL {f} — {e}")
        done += 1
        if progress_cb:
            progress_cb(done, total)
    return done
