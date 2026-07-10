# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for PixelBear.

Build with:
    pyinstaller pixelbear.spec --noconfirm

Produces a one-file executable in dist/ suitable for both Windows (.exe)
and macOS (.app bundle inside a dist/PixelBear folder, which can then be
packaged into a .dmg by build_mac.sh).
"""

import sys
from pathlib import Path

APP_NAME = "PixelBear"
IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")

block_cipher = None

# Hidden imports — pillow_heif registers its HEIF opener at runtime,
# and some Pillow plugins aren't auto-detected.
hiddenimports = [
    "pillow_heif",
    "PIL._tkinter_finder",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("icon.png", "."),
        ("app/images/watermark.jpg", "app/images"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# On macOS, bundle into a .app
if IS_MAC:
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon="icon.icns" if Path("icon.icns").exists() else None,
        bundle_identifier="com.getecz.pixelbear",
        info_plist={
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "10.13",
        },
    )
