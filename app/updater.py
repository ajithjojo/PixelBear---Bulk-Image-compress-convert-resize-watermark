"""Lightweight update checker — fetches a JSON manifest from the web and
compares version numbers. Uses only the stdlib (urllib).

Expected manifest format (hosted at UPDATE_MANIFEST_URL):

{
    "version": "1.5.0",
    "release_notes": "- New rotate tool\\n- Faster compression",
    "mandatory": false,
    "downloads": {
        "win":   "https://pixelbear.getecz.com/downloads/PixelBear-1.5.0-Setup.exe",
        "mac":   "https://pixelbear.getecz.com/downloads/PixelBear-1.5.0.dmg",
        "linux": "https://pixelbear.getecz.com/downloads/PixelBear-1.5.0.AppImage"
    }
}

If the per-platform `downloads` map is missing, a top-level `download_url`
field is used as a fallback.
"""

import json
import sys
import urllib.request
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal, QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QPlainTextEdit
)

from app.version import APP_VERSION, UPDATE_MANIFEST_URL


# ---------- helpers ----------
def parse_version(s: str) -> tuple:
    try:
        return tuple(int(p) for p in str(s).strip().lstrip("vV").split("."))
    except Exception:
        return (0,)


def is_newer(remote: str, local: str) -> bool:
    return parse_version(remote) > parse_version(local)


def _platform_key() -> str:
    if sys.platform.startswith("win"):
        return "win"
    if sys.platform == "darwin":
        return "mac"
    return "linux"


# ---------- data ----------
@dataclass
class UpdateInfo:
    version: str
    download_url: str
    release_notes: str = ""
    mandatory: bool = False


# ---------- background checker ----------
class UpdateChecker(QThread):
    update_available = Signal(object)   # UpdateInfo
    no_update = Signal()
    error = Signal(str)

    def __init__(self, manifest_url: str = UPDATE_MANIFEST_URL,
                 current: str = APP_VERSION, parent=None):
        super().__init__(parent)
        self.manifest_url = manifest_url
        self.current = current

    def run(self):
        try:
            req = urllib.request.Request(
                self.manifest_url,
                headers={"User-Agent": f"PixelBear/{self.current}"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
        except Exception as e:
            self.error.emit(str(e))
            return

        remote = str(data.get("version", "")).strip()
        if not remote:
            self.error.emit("Manifest has no 'version' field")
            return

        if not is_newer(remote, self.current):
            self.no_update.emit()
            return

        # Resolve download URL — prefer per-platform map.
        url = ""
        downloads = data.get("downloads")
        if isinstance(downloads, dict):
            url = str(downloads.get(_platform_key(), "")).strip()
        if not url:
            url = str(data.get("download_url", "")).strip()

        if not url:
            self.error.emit("No download URL in manifest for this platform")
            return

        info = UpdateInfo(
            version=remote,
            download_url=url,
            release_notes=str(data.get("release_notes", "")),
            mandatory=bool(data.get("mandatory", False)),
        )
        self.update_available.emit(info)


# ---------- dialog ----------
class UpdateDialog(QDialog):
    def __init__(self, info: UpdateInfo, current: str, parent=None):
        super().__init__(parent)
        self.info = info
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(500)

        title = QLabel("🐻  A new version of PixelBear is available")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f1f5f9; background: transparent;")

        version_lbl = QLabel(
            f"Current: <b>v{current}</b>     →     Latest: "
            f"<b style='color:#34d399;'>v{info.version}</b>"
        )
        version_lbl.setStyleSheet("color: #94a3b8; background: transparent; padding: 4px 0;")
        version_lbl.setTextFormat(Qt.RichText)

        notes_title = QLabel("What's new")
        notes_title.setStyleSheet(
            "color: #a5b4fc; font-weight: 600; padding-top: 8px; background: transparent;"
        )

        notes = QPlainTextEdit(info.release_notes or "Bug fixes and improvements.")
        notes.setReadOnly(True)
        notes.setMaximumHeight(170)

        download_btn = QPushButton("Download Update")
        download_btn.setObjectName("primary")
        download_btn.clicked.connect(self._download)

        later_btn = QPushButton("Later")
        later_btn.clicked.connect(self.reject)

        if info.mandatory:
            later_btn.setEnabled(False)
            later_btn.setToolTip("This update is required")

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(later_btn)
        btns.addWidget(download_btn)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(10)
        lay.addWidget(title)
        lay.addWidget(version_lbl)
        lay.addWidget(notes_title)
        lay.addWidget(notes)
        lay.addLayout(btns)

    def _download(self):
        QDesktopServices.openUrl(QUrl(self.info.download_url))
        self.accept()
