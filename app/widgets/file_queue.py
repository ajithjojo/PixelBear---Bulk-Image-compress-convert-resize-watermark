import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QLabel, QSizePolicy
)

from app.core.utils import SUPPORTED_EXTS


def _format_size(size: int) -> str:
    if size < 0:
        return "error"
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    if size >= 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size} B"


class DropList(QListWidget):
    """QListWidget that accepts file drag-and-drop."""
    filesDropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("dropList")
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setAlternatingRowColors(False)
        self.setMinimumHeight(140)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setProperty("dragging", "true")
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragLeaveEvent(self, e):
        self.setProperty("dragging", "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, e: QDropEvent):
        self.setProperty("dragging", "false")
        self.style().unpolish(self)
        self.style().polish(self)

        paths = []
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if not p:
                continue
            if os.path.isdir(p):
                for root, _, fnames in os.walk(p):
                    for fn in fnames:
                        if Path(fn).suffix.lower() in SUPPORTED_EXTS:
                            paths.append(os.path.join(root, fn))
            elif Path(p).suffix.lower() in SUPPORTED_EXTS:
                paths.append(p)
        if paths:
            self.filesDropped.emit(paths)
        e.acceptProposedAction()


class QueueItemWidget(QWidget):
    """Three-column row widget: name · orig size · → est size (±%)."""

    def __init__(self, path: str, orig_size: int):
        super().__init__()
        self.path = path
        self.orig_size = orig_size

        self.setObjectName("queueItem")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(40)

        self.name_lbl = QLabel(os.path.basename(path))
        self.name_lbl.setStyleSheet("color: #e5e7eb; background: transparent;")
        self.name_lbl.setToolTip(path)
        self.name_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.orig_lbl = QLabel(_format_size(orig_size))
        self.orig_lbl.setStyleSheet("color: #94a3b8; background: transparent;")
        self.orig_lbl.setFixedWidth(86)
        self.orig_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.arrow_lbl = QLabel("")
        self.arrow_lbl.setStyleSheet("color: #64748b; background: transparent;")
        self.arrow_lbl.setFixedWidth(22)
        self.arrow_lbl.setAlignment(Qt.AlignCenter)

        self.est_lbl = QLabel("")
        self.est_lbl.setStyleSheet("color: #94a3b8; background: transparent;")
        self.est_lbl.setFixedWidth(140)
        self.est_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(8)
        lay.addWidget(self.name_lbl, 1)
        lay.addWidget(self.orig_lbl)
        lay.addWidget(self.arrow_lbl)
        lay.addWidget(self.est_lbl)

    def set_estimate(self, size_bytes: int):
        if size_bytes < 0:
            self.arrow_lbl.setText("→")
            self.est_lbl.setText("error")
            self.est_lbl.setStyleSheet("background: transparent; color: #f87171; font-weight: 600;")
            return

        self.arrow_lbl.setText("→")
        text = _format_size(size_bytes)

        if self.orig_size > 0 and size_bytes < self.orig_size:
            pct = int(round((1 - size_bytes / self.orig_size) * 100))
            self.est_lbl.setText(f"{text}   −{pct}%")
            self.est_lbl.setStyleSheet(
                "background: transparent; color: #34d399; font-weight: 600;"
            )
        elif self.orig_size > 0 and size_bytes > self.orig_size:
            pct = int(round((size_bytes / self.orig_size - 1) * 100))
            self.est_lbl.setText(f"{text}   +{pct}%")
            self.est_lbl.setStyleSheet(
                "background: transparent; color: #fbbf24; font-weight: 600;"
            )
        else:
            self.est_lbl.setText(text)
            self.est_lbl.setStyleSheet(
                "background: transparent; color: #cbd5e1; font-weight: 600;"
            )

    def clear_estimate(self):
        self.arrow_lbl.setText("")
        self.est_lbl.setText("")
        self.est_lbl.setStyleSheet("background: transparent; color: #94a3b8;")

    def set_pending(self):
        self.arrow_lbl.setText("→")
        self.est_lbl.setText("…")
        self.est_lbl.setStyleSheet("background: transparent; color: #64748b;")


class FileQueue(QWidget):
    """Drag-and-drop image queue with add/remove/clear controls.

    Each item is rendered as a custom QueueItemWidget so we can show
    an estimated output size next to the original.
    """
    countChanged = Signal(int)

    def __init__(self):
        super().__init__()
        # items[i] = {"path", "orig_size", "widget", "list_item"}
        self._items: list[dict] = []
        self._path_index: dict[str, int] = {}

        self.header = QLabel("Drop images here or click 'Add Images' — 0 files")
        self.header.setStyleSheet("color: #94a3b8; font-weight: 500; padding: 2px 4px; background: transparent;")

        self.list = DropList()
        self.list.filesDropped.connect(self.add_files)

        self.add_btn = QPushButton("  Add Images")
        self.add_btn.clicked.connect(self._browse)
        self.remove_btn = QPushButton("  Remove Selected")
        self.remove_btn.clicked.connect(self._remove_selected)
        self.clear_btn = QPushButton("  Clear All")
        self.clear_btn.clicked.connect(self.clear)
        self.clear_btn.setObjectName("danger")

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch(1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(self.header)
        lay.addWidget(self.list, 1)
        lay.addLayout(btn_row)

    # ---------- Public API ----------
    def files(self) -> list[str]:
        return [it["path"] for it in self._items]

    def original_size(self, path: str) -> int:
        idx = self._path_index.get(path)
        if idx is None:
            return 0
        return self._items[idx]["orig_size"]

    def add_files(self, paths: list[str]):
        added = 0
        for p in paths:
            if p in self._path_index:
                continue
            try:
                orig = os.path.getsize(p)
            except OSError:
                orig = 0

            widget = QueueItemWidget(p, orig)
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 44))
            list_item.setToolTip(p)
            self.list.addItem(list_item)
            self.list.setItemWidget(list_item, widget)

            self._items.append({
                "path": p,
                "orig_size": orig,
                "widget": widget,
                "list_item": list_item,
            })
            self._path_index[p] = len(self._items) - 1
            added += 1

        if added:
            self._update_header()
            self.countChanged.emit(len(self._items))

    def clear(self):
        if not self._items:
            return
        self._items.clear()
        self._path_index.clear()
        self.list.clear()
        self._update_header()
        self.countChanged.emit(0)

    def _remove_selected(self):
        rows = sorted({self.list.row(it) for it in self.list.selectedItems()}, reverse=True)
        if not rows:
            return
        for r in rows:
            self.list.takeItem(r)
            del self._items[r]
        # rebuild path index after deletions
        self._path_index = {it["path"]: i for i, it in enumerate(self._items)}
        self._update_header()
        self.countChanged.emit(len(self._items))

    def _browse(self):
        filt = "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif *.heic *.heif)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select images", "", filt)
        if files:
            self.add_files(files)

    def _update_header(self):
        n = len(self._items)
        word = "file" if n == 1 else "files"
        total = sum(it["orig_size"] for it in self._items)
        if n:
            self.header.setText(f"{n} {word}  ·  total {_format_size(total)}")
        else:
            self.header.setText("Drop images here or click 'Add Images' — 0 files")

    # ---------- Estimate API ----------
    def set_estimate(self, path: str, size_bytes: int):
        idx = self._path_index.get(path)
        if idx is None:
            return
        self._items[idx]["widget"].set_estimate(size_bytes)

    def mark_all_pending(self):
        for it in self._items:
            it["widget"].set_pending()

    def clear_estimates(self):
        for it in self._items:
            it["widget"].clear_estimate()
