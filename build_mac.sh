#!/usr/bin/env bash
# Build PixelBear macOS .app and package it into a .dmg
#
# Run this script on a Mac (it will not work on Windows or Linux).
# Requirements:
#   - Python 3.10+
#   - pip
#   - create-dmg (brew install create-dmg)  — optional but recommended

set -euo pipefail

APP_NAME="PixelBear"
VERSION="1.0.0"

echo "=== Cleaning previous build ==="
rm -rf build dist

echo "=== Installing dependencies ==="
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

echo "=== Building ${APP_NAME}.app ==="
python3 -m PyInstaller pixelbear.spec --noconfirm

APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "${APP_PATH}" ]; then
    echo "ERROR: ${APP_PATH} was not produced by PyInstaller."
    exit 1
fi

DMG_PATH="dist/${APP_NAME}-${VERSION}.dmg"
rm -f "${DMG_PATH}"

echo "=== Creating ${DMG_PATH} ==="
if command -v create-dmg >/dev/null 2>&1; then
    create-dmg \
        --volname "${APP_NAME} ${VERSION}" \
        --window-pos 200 120 \
        --window-size 600 340 \
        --icon-size 96 \
        --icon "${APP_NAME}.app" 170 160 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 430 160 \
        "${DMG_PATH}" \
        "${APP_PATH}"
else
    echo "create-dmg not found — falling back to hdiutil (plain dmg)."
    echo "   (Install prettier installer with: brew install create-dmg)"
    hdiutil create -volname "${APP_NAME} ${VERSION}" \
        -srcfolder "${APP_PATH}" \
        -ov -format UDZO \
        "${DMG_PATH}"
fi

echo
echo "==========================================="
echo "Build complete:"
echo "  App:  ${APP_PATH}"
echo "  DMG:  ${DMG_PATH}"
echo "==========================================="
