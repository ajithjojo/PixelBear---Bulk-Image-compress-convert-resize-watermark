# 🐻 PixelBear — Bulk Image Toolkit

A fast, modern desktop app for bulk image processing. Compress, resize, convert, rotate, and watermark hundreds of images in seconds — with a clean dark UI and real-time output size preview.

**Works on Windows, macOS, and Linux.**

[![Download Latest Release](https://img.shields.io/badge/Download-Latest%20Release-34d399?style=for-the-badge&logo=github)](https://github.com/ajithjojo/PixelBear---Bulk-Image-compress-convert-resize-watermark/releases/tag/Release)

---

## Download

👉 **[Download PixelBear (Windows / macOS)](https://github.com/ajithjojo/PixelBear---Bulk-Image-compress-convert-resize-watermark/releases/tag/Release)**

---

## Screenshots

> _Coming soon_

---

## Features

### 🗜️ Bulk Compress
- Compress images to **JPEG**, **WebP**, or **PNG**
- Quality slider (1–100) with **real-time output size preview** per file
- See exactly how much space you'll save before processing (green = smaller, amber = larger)

### 📐 Bulk Resize
- Resize by **exact dimensions** (width, height, or both) or by **percentage**
- Keep aspect ratio toggle
- Live estimated output file size per image

### 🔄 Bulk Convert
- Convert between **JPEG**, **PNG**, and **WebP**
- Quality control for lossy formats
- Background color picker for transparent images → JPEG (no more black backgrounds)

### 🔁 Bulk Rotate & Flip
- **90° clockwise**, **90° counter-clockwise**, **180°**, or **custom angle**
- **Flip horizontally** and **vertically** (can combine with rotation)
- Lossless rotation for standard angles

### 💧 Bulk Watermark
- **Text watermark** — custom text, font size, and color picker
- **Image watermark** — use any PNG/JPG as a watermark, adjustable size (% of base image)
- **9 position anchors** — top-left, center, bottom-right, etc.
- **Opacity slider** (0–100%)
- **Live preview panel** — see exactly how the watermark will look before processing, updates in real-time as you tweak settings

### 🎯 Common Features (All Tools)
- **Drag & drop** files or folders directly into the app
- **Multi-select file picker** — add images from anywhere
- **File queue** with per-file original size display
- **Real-time estimated output size** (Compress & Resize tabs) with percentage change
- **Progress bar** with per-file status log
- **Cancel** any batch job mid-process
- **Non-blocking UI** — all processing runs on background threads

### 🔄 Auto-Update
- Checks for updates on startup (non-blocking)
- Manual "Check for updates" button in sidebar
- Shows release notes + one-click download when a new version is available

---

## Supported Formats

| Format | Read | Write |
|--------|------|-------|
| JPEG (.jpg, .jpeg) | ✅ | ✅ |
| PNG (.png) | ✅ | ✅ |
| WebP (.webp) | ✅ | ✅ |
| BMP (.bmp) | ✅ | ✅ |
| TIFF (.tiff, .tif) | ✅ | ✅ |
| HEIC / HEIF (.heic, .heif) | ✅ (via pillow-heif) | — |

---

## Run from Source

### Requirements
- Python 3.10+
- pip

### Setup
```bash
git clone https://github.com/ajithjojo/PixelBear---Bulk-Image-compress-convert-resize-watermark.git
cd PixelBear---Bulk-Image-compress-convert-resize-watermark
pip install -r requirements.txt
python main.py
```

### Dependencies
- **PySide6** — Qt6 GUI framework (cross-platform native widgets)
- **Pillow** — image processing engine
- **pillow-heif** — HEIC/HEIF support (optional)

---

## Build Installers

### Windows (.exe installer)
```bash
pip install pyinstaller
pyinstaller pixelbear.spec --noconfirm
# Then compile the installer with Inno Setup:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
# Output: dist/PixelBear-1.0.0-Setup.exe
```

### macOS (.dmg)
```bash
brew install create-dmg
pip install pyinstaller
chmod +x build_mac.sh
./build_mac.sh
# Output: dist/PixelBear-1.0.0.dmg
```

### CI/CD (GitHub Actions)
Push a version tag to automatically build both platforms:
```bash
git tag v1.0.0
git push origin v1.0.0
```
The `.github/workflows/build.yml` workflow will build the Windows `.exe` and macOS `.dmg`, then create a GitHub Release with both attached.

---

## Project Structure

```
PixelBear/
├── main.py                     # App entry point
├── requirements.txt
├── pixelbear.spec              # PyInstaller build spec
├── installer.iss               # Inno Setup installer script
├── icon.png / icon.ico         # App icon
├── build_win.bat               # Windows build script
├── build_mac.sh                # macOS build script
├── .github/workflows/build.yml # CI build pipeline
└── app/
    ├── main_window.py          # Sidebar + stacked tool pages
    ├── version.py              # APP_VERSION + update URL
    ├── updater.py              # Auto-update checker + dialog
    ├── resources.py            # PyInstaller-safe resource paths
    ├── styles.py               # Dark theme QSS stylesheet
    ├── tools_registry.py       # Tool registration (add new tools here)
    ├── worker.py               # BatchWorker + EstimateWorker threads
    ├── widgets/
    │   └── file_queue.py       # Drag-drop queue with size estimates
    ├── tabs/
    │   ├── base_tab.py         # Shared widgets (pickers, log panel)
    │   ├── compress_tab.py
    │   ├── resize_tab.py
    │   ├── convert_tab.py
    │   ├── rotate_tab.py
    │   └── watermark_tab.py
    └── core/
        ├── utils.py            # File listing, output paths
        ├── compress.py         # Compression engine + estimator
        ├── resize.py           # Resize engine + estimator
        ├── convert.py          # Format conversion engine
        ├── rotate.py           # Rotation/flip engine
        └── watermark.py        # Watermark engine + preview renderer
```

---

## Adding New Tools

PixelBear is designed as an extensible toolkit. To add a new tool:

1. Create the processing logic in `app/core/my_tool.py`
2. Create the UI tab in `app/tabs/my_tool_tab.py`
3. Register it in `app/tools_registry.py`:
```python
Tool(
    key="my_tool",
    name="My Tool",
    subtitle="Description shown below the title",
    factory=MyToolTab,
),
```
It automatically appears in the sidebar.

---

## License

MIT

---

## Credits

Built with [Python](https://python.org), [PySide6](https://doc.qt.io/qtforpython/), and [Pillow](https://pillow.readthedocs.io/).
