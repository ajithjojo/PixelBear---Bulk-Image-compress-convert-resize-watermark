from PIL import Image, ImageDraw
from . import utils
from . import fonts as font_utils


def apply_watermarks(base_rgba: Image.Image, *, items: list, opacity: int = 60) -> Image.Image:
    cw, ch = base_rgba.size
    layer = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
    alpha = max(0, min(255, int(opacity * 255 / 100)))

    for item in items:
        try:
            if item["type"] == "image":
                with Image.open(item["path"]) as wm:
                    wm = wm.convert("RGBA")
                    target_w = max(1, int(cw * item["w_frac"]))
                    ratio = target_w / wm.width
                    target_h = max(1, int(wm.height * ratio))
                    wm = wm.resize((target_w, target_h), Image.LANCZOS)
                    if alpha < 255:
                        r, g, b, a = wm.split()
                        a = a.point(lambda px: int(px * alpha / 255))
                        wm = Image.merge("RGBA", (r, g, b, a))
                    x = int(cw * item["x_frac"])
                    y = int(ch * item["y_frac"])
                    layer.paste(wm, (x, y), wm)

            elif item["type"] == "text" and item.get("text"):
                draw = ImageDraw.Draw(layer)
                size_px = max(1, int(item["font_frac"] * ch))
                font = font_utils.load_font(item.get("font_family", ""), size_px)
                color = item.get("color", (255, 255, 255))
                x = int(cw * item["x_frac"])
                y = int(ch * item["y_frac"])
                bbox = draw.textbbox((0, 0), item["text"], font=font)
                draw.text(
                    (x - bbox[0], y - bbox[1]), item["text"], font=font,
                    fill=(color[0], color[1], color[2], alpha),
                )
        except Exception:
            pass

    return Image.alpha_composite(base_rgba, layer)


def watermark_image(src: str, dest: str, *, items: list, opacity: int = 60):
    with Image.open(src) as base:
        original_format = (base.format or "PNG").upper()
        base_rgba = base.convert("RGBA")

    out = apply_watermarks(base_rgba, items=items, opacity=opacity)

    save_kwargs = {}
    fmt = original_format
    if fmt in ("JPEG", "JPG"):
        out = out.convert("RGB")
        save_kwargs.update(quality=92, optimize=True)
        fmt = "JPEG"
    out.save(dest, format=fmt, **save_kwargs)


def run_watermark_batch(files, out_root, *,
                        progress_cb=None, log_cb=None, cancel_cb=None, **kwargs):
    total = len(files)
    done = 0
    for f in files:
        if cancel_cb and cancel_cb():
            break
        try:
            dest = utils.flat_output_path(f, out_root)
            watermark_image(f, dest, **kwargs)
            if log_cb:
                log_cb(f"OK   {f}")
        except Exception as e:
            if log_cb:
                log_cb(f"FAIL {f} — {e}")
        done += 1
        if progress_cb:
            progress_cb(done, total)
    return done
