from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontDatabase
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QSlider,
    QLineEdit, QPushButton, QMessageBox, QGroupBox, QStackedWidget, QLabel,
    QColorDialog, QFileDialog, QFrame,
)

from PIL import Image

from app.tabs.base_tab import FolderPicker, LogPanel
from app.widgets.file_queue import FileQueue
from app.widgets.watermark_canvas import WatermarkCanvas
from app.worker import BatchWorker
from app.core import watermark as core_wm
from app.resources import resource_path

SAMPLE_PREVIEW_IMAGE = resource_path("app/images/watermark.jpg")


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("background-color: #1e2740; max-height: 1px; border: none;")
    return line


class WatermarkTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: BatchWorker | None = None
        self._color = (255, 255, 255)
        self._editing_text_item = None

        self.queue = FileQueue()
        self.out_picker = FolderPicker("Output folder")

        # ---- Image watermark (primary) ----
        img_header = QLabel("Image Watermark")
        img_header.setStyleSheet("color: #c7d2fe; font-size: 15px; font-weight: 700;")

        self.add_wm_btn = QPushButton("Add Watermark Image…")
        self.add_wm_btn.setObjectName("primary")
        self.add_wm_btn.clicked.connect(self._add_watermark_images)
        self.remove_wm_btn = QPushButton("Remove Selected")
        self.remove_wm_btn.clicked.connect(self._remove_selected_watermarks)
        self.clear_wm_btn = QPushButton("Clear All")
        self.clear_wm_btn.setObjectName("danger")
        self.clear_wm_btn.clicked.connect(self._clear_watermarks)

        img_btn_row = QHBoxLayout()
        img_btn_row.addWidget(self.add_wm_btn)
        img_btn_row.addWidget(self.remove_wm_btn)
        img_btn_row.addWidget(self.clear_wm_btn)

        self.wm_hint = QLabel("Drag any watermark to move · Drag corners to resize · Del to remove")
        self.wm_hint.setStyleSheet("color: #64748b; font-size: 11px;")

        # ---- Text watermark (secondary) ----
        text_header = QLabel("Text Watermark")
        text_header.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")

        self.text = QLineEdit()
        self.text.setPlaceholderText("Watermark text")
        self.text.setText("© PixelBear")

        self.font_combo = QComboBox()
        families = sorted(f for f in QFontDatabase.families() if not f.startswith("@"))
        self.font_combo.addItems(families)
        default_idx = self.font_combo.findText("Arial")
        if default_idx >= 0:
            self.font_combo.setCurrentIndex(default_idx)

        self.color_btn = QPushButton("Pick color…")
        self.color_btn.clicked.connect(self._pick_color)
        self.color_preview = QLabel("  ")
        self.color_preview.setStyleSheet(
            "background-color: white; border: 1px solid #3b456a; border-radius: 4px;"
        )
        self.color_preview.setFixedSize(28, 22)
        color_row = QHBoxLayout()
        color_row.addWidget(self.color_btn)
        color_row.addWidget(self.color_preview)
        color_row.addStretch(1)
        color_row_w = QWidget()
        color_row_w.setLayout(color_row)

        text_form = QFormLayout()
        text_form.setSpacing(10)
        text_form.addRow("Text:", self.text)
        text_form.addRow("Font:", self.font_combo)
        text_form.addRow("Color:", color_row_w)

        self.add_text_btn = QPushButton("Add Text Watermark")
        self.add_text_btn.clicked.connect(self._add_or_update_text_watermark)
        self.cancel_edit_btn = QPushButton("Cancel Edit")
        self.cancel_edit_btn.setVisible(False)
        self.cancel_edit_btn.clicked.connect(self._cancel_text_edit)

        text_btn_row = QHBoxLayout()
        text_btn_row.addWidget(self.add_text_btn, 1)
        text_btn_row.addWidget(self.cancel_edit_btn)

        # ---- Shared opacity ----
        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.setValue(70)
        self.opacity_lbl = QLabel("70")
        self.opacity_lbl.setFixedWidth(30)
        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("Opacity:"))
        op_row.addWidget(self.opacity, 1)
        op_row.addWidget(self.opacity_lbl)

        opts_layout = QVBoxLayout()
        opts_layout.setSpacing(10)
        opts_layout.addWidget(img_header)
        opts_layout.addLayout(img_btn_row)
        opts_layout.addWidget(self.wm_hint)
        opts_layout.addWidget(_divider())
        opts_layout.addWidget(text_header)
        opts_layout.addLayout(text_form)
        opts_layout.addLayout(text_btn_row)
        opts_layout.addWidget(_divider())
        opts_layout.addLayout(op_row)
        opts_layout.addStretch(1)

        opts = QGroupBox("Watermark Options")
        opts.setLayout(opts_layout)
        opts.setMinimumWidth(340)

        # ---- Preview: interactive canvas ----
        self.canvas = WatermarkCanvas()
        self.canvas.setMinimumSize(420, 280)

        self.canvas_placeholder = QLabel("Add images to the queue,\nthen add a watermark")
        self.canvas_placeholder.setObjectName("previewLabel")
        self.canvas_placeholder.setAlignment(Qt.AlignCenter)

        canvas_stack_layout = QVBoxLayout()
        canvas_stack_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_stack = QStackedWidget()
        self.canvas_stack.addWidget(self.canvas_placeholder)
        self.canvas_stack.addWidget(self.canvas)
        canvas_stack_layout.addWidget(self.canvas_stack, 1)
        canvas_widget = QWidget()
        canvas_widget.setLayout(canvas_stack_layout)

        preview_box_layout = QVBoxLayout()
        preview_box_layout.addWidget(canvas_widget, 1)
        preview_box = QGroupBox("Live Preview")
        preview_box.setLayout(preview_box_layout)

        opts_row = QHBoxLayout()
        opts_row.setSpacing(14)
        opts_row.addWidget(opts, 0)
        opts_row.addWidget(preview_box, 1)

        # ---- Action buttons ----
        self.start_btn = QPushButton("Apply Watermark")
        self.start_btn.setObjectName("primary")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start)
        self.cancel_btn.clicked.connect(self.cancel)

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.start_btn)

        self.log_panel = LogPanel()

        # ---- Main layout ----
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.queue)
        layout.addWidget(self.out_picker)
        layout.addLayout(opts_row)
        layout.addLayout(btns)
        layout.addWidget(self.log_panel)

        self.opacity.valueChanged.connect(self._on_opacity_changed)
        self.queue.countChanged.connect(self._on_queue_changed)
        self.canvas.textSelectionChanged.connect(self._on_text_selection_changed)
        self.text.textChanged.connect(self._live_update_text)
        self.font_combo.currentTextChanged.connect(self._live_update_text)

        self._update_canvas_base()

    # ---------- signals ----------
    def _on_opacity_changed(self, value):
        self.opacity_lbl.setText(str(value))
        self.canvas.set_items_opacity(value)

    def _on_queue_changed(self):
        self._update_canvas_base()

    # ---------- canvas ----------
    def _update_canvas_base(self):
        files = self.queue.files()
        source = files[0] if files else SAMPLE_PREVIEW_IMAGE

        try:
            with Image.open(source) as base:
                base_rgba = base.convert("RGBA")
            self.canvas.set_base_image(base_rgba)
            self.canvas.set_items_opacity(self.opacity.value())
            self.canvas_stack.setCurrentIndex(1)
        except Exception:
            self.canvas.clear_base()
            self.canvas_stack.setCurrentIndex(0)

    def _ensure_canvas_ready(self):
        if self.canvas._scene_w < 1:
            self._update_canvas_base()
            if self.canvas._scene_w < 1:
                QMessageBox.information(
                    self, "No base image",
                    "Add images to the queue first so the canvas has a base to display."
                )
                return False
        return True

    def _add_watermark_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select watermark images", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif)"
        )
        if not files:
            return
        if not self._ensure_canvas_ready():
            return

        for path in files:
            self.canvas.add_watermark_image(path)
        self.canvas.set_items_opacity(self.opacity.value())

    def _add_or_update_text_watermark(self):
        text = self.text.text().strip()
        if not text:
            QMessageBox.warning(self, "Missing", "Enter watermark text.")
            return

        if self._editing_text_item is not None:
            self.canvas.update_text_watermark(
                self._editing_text_item, text, self.font_combo.currentText(), self._color
            )
            return

        if not self._ensure_canvas_ready():
            return

        item = self.canvas.add_text_watermark(text, self.font_combo.currentText(), self._color)
        if item:
            self.canvas.set_items_opacity(self.opacity.value())

    def _on_text_selection_changed(self, item):
        self._editing_text_item = None
        if item is None:
            self.add_text_btn.setText("Add Text Watermark")
            self.add_text_btn.setVisible(True)
            self.cancel_edit_btn.setVisible(False)
            return

        self.text.setText(item.text)
        idx = self.font_combo.findText(item.font_family)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)
        self._color = item.color
        self.color_preview.setStyleSheet(
            f"background-color: rgb{self._color}; border: 1px solid #3b456a; border-radius: 4px;"
        )
        # set after populating fields so the syncing above doesn't self-apply
        self._editing_text_item = item
        self.add_text_btn.setVisible(False)
        self.cancel_edit_btn.setText("Done Editing")
        self.cancel_edit_btn.setVisible(True)

    def _cancel_text_edit(self):
        self.canvas._scene.clearSelection()

    def _live_update_text(self, *_args):
        if self._editing_text_item is None:
            return
        text = self.text.text().strip()
        if not text:
            return
        self.canvas.update_text_watermark(
            self._editing_text_item, text, self.font_combo.currentText(), self._color
        )

    def _remove_selected_watermarks(self):
        self.canvas.remove_selected()

    def _clear_watermarks(self):
        self.canvas.clear_watermarks()

    # ---------- color ----------
    def _pick_color(self):
        c = QColorDialog.getColor(QColor(*self._color), self, "Pick text color")
        if c.isValid():
            self._color = (c.red(), c.green(), c.blue())
            self.color_preview.setStyleSheet(
                f"background-color: rgb{self._color}; border: 1px solid #3b456a; border-radius: 4px;"
            )
            self._live_update_text()

    # ---------- run ----------
    def start(self):
        files = self.queue.files()
        out = self.out_picker.path()
        if not files:
            QMessageBox.warning(self, "No images", "Please add images to the queue.")
            return
        if not out:
            QMessageBox.warning(self, "Missing", "Please select an output folder.")
            return

        items = self.canvas.get_placements()
        if not items:
            QMessageBox.warning(
                self, "No watermarks",
                "Add at least one watermark (image or text) to the canvas."
            )
            return

        self.log_panel.reset()
        self.log_panel.append(f"Applying watermark to {len(files)} image(s)…")

        self.worker = BatchWorker(
            core_wm.run_watermark_batch,
            files, out,
            items=items,
            opacity=self.opacity.value(),
        )
        self.worker.progress.connect(self.log_panel.set_progress)
        self.worker.log.connect(self.log_panel.append)
        self.worker.finished_ok.connect(self._done)
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.worker.start()

    def cancel(self):
        if self.worker:
            self.worker.cancel()
            self.log_panel.append("Cancelling…")

    def _done(self, n: int):
        self.log_panel.append(f"Finished. Processed {n} image(s).")
        self.log_panel.status.setText(f"Done — {n} processed")
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
