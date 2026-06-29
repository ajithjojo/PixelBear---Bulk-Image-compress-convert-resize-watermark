import io
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QSpinBox, QSlider,
    QLineEdit, QPushButton, QMessageBox, QGroupBox, QStackedWidget, QLabel,
    QColorDialog, QFileDialog,
)

from PIL import Image

from app.tabs.base_tab import FolderPicker, LogPanel
from app.widgets.file_queue import FileQueue
from app.widgets.watermark_canvas import WatermarkCanvas
from app.worker import BatchWorker
from app.core import watermark as core_wm


class WatermarkTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: BatchWorker | None = None
        self._color = (255, 255, 255)

        self.queue = FileQueue()
        self.out_picker = FolderPicker("Output folder")

        self.kind = QComboBox()
        self.kind.addItems(["Text", "Image"])
        self.kind.currentIndexChanged.connect(self._on_kind_changed)

        # ---- Text watermark options ----
        self.text = QLineEdit()
        self.text.setPlaceholderText("Watermark text")
        self.text.setText("© PixelBear")
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 500)
        self.font_size.setValue(64)
        self.color_btn = QPushButton("Pick color…")
        self.color_btn.clicked.connect(self._pick_color)
        self.color_preview = QLabel("  ")
        self.color_preview.setStyleSheet(
            "background-color: white; border: 1px solid #3b456a; border-radius: 4px;"
        )
        self.color_preview.setFixedSize(28, 22)

        self.position = QComboBox()
        self.position.addItems(core_wm.POSITIONS)
        self.position.setCurrentText("bottom-right")

        text_form = QFormLayout()
        text_form.setSpacing(10)
        text_form.addRow("Text:", self.text)
        text_form.addRow("Font size:", self.font_size)
        color_row = QHBoxLayout()
        color_row.addWidget(self.color_btn)
        color_row.addWidget(self.color_preview)
        color_row.addStretch(1)
        cw = QWidget()
        cw.setLayout(color_row)
        text_form.addRow("Color:", cw)
        text_form.addRow("Position:", self.position)
        text_widget = QWidget()
        text_widget.setLayout(text_form)

        # ---- Image watermark options ----
        self.add_wm_btn = QPushButton("Add Watermark Image…")
        self.add_wm_btn.clicked.connect(self._add_watermark_images)
        self.remove_wm_btn = QPushButton("Remove Selected")
        self.remove_wm_btn.clicked.connect(self._remove_selected_watermarks)
        self.clear_wm_btn = QPushButton("Clear All")
        self.clear_wm_btn.setObjectName("danger")
        self.clear_wm_btn.clicked.connect(self._clear_watermarks)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.add_wm_btn)
        btn_row.addWidget(self.remove_wm_btn)
        btn_row.addWidget(self.clear_wm_btn)
        btn_row.addStretch(1)

        self.wm_hint = QLabel("Drag to move · Corners to resize · Del to remove")
        self.wm_hint.setStyleSheet("color: #64748b; font-size: 11px;")

        img_form = QVBoxLayout()
        img_form.setSpacing(10)
        img_form.addLayout(btn_row)
        img_form.addWidget(self.wm_hint)
        img_form.addStretch(1)
        img_widget = QWidget()
        img_widget.setLayout(img_form)

        self.opts_stack = QStackedWidget()
        self.opts_stack.addWidget(text_widget)
        self.opts_stack.addWidget(img_widget)

        # ---- Shared opacity ----
        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.setValue(70)
        self.opacity_lbl = QLabel("70")
        self.opacity_lbl.setFixedWidth(30)
        self.opacity.valueChanged.connect(lambda v: self.opacity_lbl.setText(str(v)))
        op_row = QHBoxLayout()
        op_row.addWidget(self.opacity, 1)
        op_row.addWidget(self.opacity_lbl)

        common_form = QFormLayout()
        common_form.setSpacing(10)
        common_form.addRow("Type:", self.kind)
        common_form.addRow(self.opts_stack)
        common_form.addRow("Opacity:", op_row)

        opts = QGroupBox("Watermark Options")
        opts.setLayout(common_form)
        opts.setMinimumWidth(340)

        # ---- Preview: text mode (QLabel) ----
        self.preview_label = QLabel("Add an image to see live preview")
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setAlignment(Qt.AlignCenter)

        text_preview_layout = QVBoxLayout()
        text_preview_layout.setContentsMargins(0, 0, 0, 0)
        text_preview_layout.addWidget(self.preview_label, 1)
        text_preview_widget = QWidget()
        text_preview_widget.setLayout(text_preview_layout)

        # ---- Preview: image mode (interactive canvas) ----
        self.canvas = WatermarkCanvas()
        self.canvas.setMinimumSize(420, 280)

        self.canvas_placeholder = QLabel("Add images to the queue,\nthen add watermark images")
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

        # ---- Preview stack (text vs image mode) ----
        self.preview_stack = QStackedWidget()
        self.preview_stack.addWidget(text_preview_widget)
        self.preview_stack.addWidget(canvas_widget)

        preview_box_layout = QVBoxLayout()
        preview_box_layout.addWidget(self.preview_stack, 1)
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

        # ---- Preview debounce (text mode) ----
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(200)
        self._preview_timer.timeout.connect(self._update_preview)
        self._wire_preview_signals()

    # ---------- signals ----------
    def _wire_preview_signals(self):
        self.text.textChanged.connect(self._schedule_preview)
        self.font_size.valueChanged.connect(self._schedule_preview)
        self.opacity.valueChanged.connect(self._on_opacity_changed)
        self.position.currentIndexChanged.connect(self._schedule_preview)
        self.kind.currentIndexChanged.connect(self._schedule_preview)
        self.queue.countChanged.connect(self._on_queue_changed)

    def _schedule_preview(self, *_):
        self._preview_timer.start()

    def _on_kind_changed(self, index):
        self.opts_stack.setCurrentIndex(index)
        self.preview_stack.setCurrentIndex(index)
        if index == 1:
            self._update_canvas_base()

    def _on_opacity_changed(self, value):
        self.opacity_lbl.setText(str(value))
        if self.kind.currentIndex() == 1:
            self.canvas.set_items_opacity(value)
        else:
            self._schedule_preview()

    def _on_queue_changed(self):
        if self.kind.currentIndex() == 1:
            self._update_canvas_base()
        self._schedule_preview()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.kind.currentIndex() == 0:
            self._schedule_preview()

    # ---------- text preview ----------
    def _update_preview(self):
        if self.kind.currentIndex() != 0:
            return
        files = self.queue.files()
        if not files:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Add an image to see live preview")
            return

        src = files[0]
        try:
            with Image.open(src) as base:
                base_rgba = base.convert("RGBA")

            box_w = max(320, self.preview_label.width() - 16)
            box_h = max(240, self.preview_label.height() - 16)
            orig_w = base_rgba.width
            ratio = min(box_w / base_rgba.width, box_h / base_rgba.height)
            new_w = max(1, int(base_rgba.width * ratio))
            new_h = max(1, int(base_rgba.height * ratio))
            base_rgba = base_rgba.resize((new_w, new_h), Image.LANCZOS)
            ratio = new_w / orig_w
            scaled_font = max(6, int(self.font_size.value() * ratio))

            out = core_wm.apply_watermark(
                base_rgba,
                kind="text",
                text=self.text.text(),
                wm_image="",
                position=self.position.currentText(),
                opacity=self.opacity.value(),
                font_size=scaled_font,
                color=self._color,
                wm_scale_pct=25,
            )

            buf = io.BytesIO()
            out.save(buf, format="PNG")
            pix = QPixmap()
            pix.loadFromData(buf.getvalue())
            self.preview_label.setText("")
            self.preview_label.setPixmap(pix)
        except Exception as e:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(f"Preview error:\n{e}")

    # ---------- canvas (image mode) ----------
    def _update_canvas_base(self):
        files = self.queue.files()
        if not files:
            self.canvas.clear_base()
            self.canvas_stack.setCurrentIndex(0)
            return

        try:
            with Image.open(files[0]) as base:
                base_rgba = base.convert("RGBA")
            self.canvas.set_base_image(base_rgba)
            self.canvas.set_items_opacity(self.opacity.value())
            self.canvas_stack.setCurrentIndex(1)
        except Exception:
            self.canvas_stack.setCurrentIndex(0)

    def _add_watermark_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select watermark images", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif)"
        )
        if not files:
            return
        if self.canvas._scene_w < 1:
            self._update_canvas_base()
            if self.canvas._scene_w < 1:
                QMessageBox.information(
                    self, "No base image",
                    "Add images to the queue first so the canvas has a base to display."
                )
                return

        for path in files:
            self.canvas.add_watermark(path)
        self.canvas.set_items_opacity(self.opacity.value())

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
            self._schedule_preview()

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

        kind = "text" if self.kind.currentIndex() == 0 else "image"

        if kind == "text":
            if not self.text.text().strip():
                QMessageBox.warning(self, "Missing", "Enter watermark text.")
                return
            kwargs = dict(
                kind="text",
                text=self.text.text(),
                wm_image="",
                position=self.position.currentText(),
                opacity=self.opacity.value(),
                font_size=self.font_size.value(),
                color=self._color,
                wm_scale_pct=25,
            )
        else:
            placements = self.canvas.get_placements()
            if not placements:
                QMessageBox.warning(
                    self, "No watermarks",
                    "Add at least one watermark image to the canvas."
                )
                return
            kwargs = dict(
                watermarks=placements,
                opacity=self.opacity.value(),
            )

        self.log_panel.reset()
        self.log_panel.append(f"Applying watermark to {len(files)} image(s)…")

        self.worker = BatchWorker(
            core_wm.run_watermark_batch,
            files, out,
            **kwargs,
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
