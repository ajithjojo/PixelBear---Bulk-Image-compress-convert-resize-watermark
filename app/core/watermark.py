from PIL import Image, ImageDraw, ImageFont
from . import utils

POSITIONS = [
    "top-left", "top-center", "top-right",
    "middle-left", "center", "middle-right",
    "bottom-left", "bottom-center", "bottom-right",
]


def _anchor_xy(canvas_w, canvas_h, wm_w, wm_h, position, margin=20):
    if "left" in position:
        x = margin
    elif "right" in position:
        x = canvas_w - wm_w - margin
    else:
        x = (canvas_w - wm_w) // 2

    if "top" in position:
        y = margin
    elif "bottom" in position:
        y = canvas_h - wm_h - margin
    else:
        y = (canvas_h - wm_h) // 2
    return x, y


def _load_font(size: int):
    candidates = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf"]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def apply_watermark(base_rgba: Image.Image, *, kind: str, text: str = "",
                    wm_image: str = "", position: str = "bottom-right",
                    opacity: int = 60, font_size: int = 36,
                    color: tuple = (255, 255, 255), wm_scale_pct: int = 20) -> Image.Image:
    cw, ch = base_rgba.size
    layer = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
    alpha = max(0, min(255, int(opacity * 255 / 100)))

    if kind == "text" and text:
        draw = ImageDraw.Draw(layer)
        font = _load_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = _anchor_xy(cw, ch, tw, th, position)
        draw.text((x - bbox[0], y - bbox[1]), text, font=font,
                  fill=(color[0], color[1], color[2], alpha))

    elif kind == "image" and wm_image:
        try:
            with Image.open(wm_image) as wm:
                wm = wm.convert("RGBA")
                target_w = max(1, int(cw * wm_scale_pct / 100))
                ratio = target_w / wm.width
                target_h = max(1, int(wm.height * ratio))
                wm = wm.resize((target_w, target_h), Image.LANCZOS)
                if alpha < 255:
                    r, g, b, a = wm.split()
                    a = a.point(lambda px: int(px * alpha / 255))
                    wm = Image.merge("RGBA", (r, g, b, a))
                x, y = _anchor_xy(cw, ch, wm.width, wm.height, position)
                layer.paste(wm, (x, y), wm)
        except Exception:
            pass

    return Image.alpha_composite(base_rgba, layer)


def apply_multi_image_watermarks(base_rgba: Image.Image, *,
                                 watermarks: list, opacity: int = 60) -> Image.Image:
    cw, ch = base_rgba.size
    layer = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
    alpha = max(0, min(255, int(opacity * 255 / 100)))

    for wm_info in watermarks:
        try:
            with Image.open(wm_info["path"]) as wm:
                wm = wm.convert("RGBA")
                target_w = max(1, int(cw * wm_info["w_frac"]))
                ratio = target_w / wm.width
                target_h = max(1, int(wm.height * ratio))
                wm = wm.resize((target_w, target_h), Image.LANCZOS)
                if alpha < 255:
                    r, g, b, a = wm.split()
                    a = a.point(lambda px: int(px * alpha / 255))
                    wm = Image.merge("RGBA", (r, g, b, a))
                x = int(cw * wm_info["x_frac"])
                y = int(ch * wm_info["y_frac"])
                layer.paste(wm, (x, y), wm)
        except Exception:
            pass

    return Image.alpha_composite(base_rgba, layer)


def watermark_image(src: str, dest: str, **kwargs):
    with Image.open(src) as base:
        original_format = (base.format or "PNG").upper()
        base_rgba = base.convert("RGBA")

    if "watermarks" in kwargs:
        out = apply_multi_image_watermarks(
            base_rgba,
            watermarks=kwargs["watermarks"],
            opacity=kwargs.get("opacity", 60),
        )
    else:
        out = apply_watermark(base_rgba, **kwargs)

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
