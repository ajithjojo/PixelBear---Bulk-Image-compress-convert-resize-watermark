import io

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QSpinBox, QSlider,
    QLineEdit, QPushButton, QMessageBox, QGroupBox, QStackedWidget, QLabel,
    QColorDialog
)

from PIL import Image

from app.tabs.base_tab import FolderPicker, FilePicker, LogPanel
from app.widgets.file_queue import FileQueue
from app.worker import BatchWorker
from app.core import watermark as core_wm


class WatermarkTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: BatchWorker | None = None
        self._color = (255, 255, 255)

        # ---------- widgets ----------
        self.queue = FileQueue()
        self.out_picker = FolderPicker("Output folder")

        self.kind = QComboBox()
        self.kind.addItems(["Text", "Image"])
        self.kind.currentIndexChanged.connect(lambda i: self.stack.setCurrentIndex(i))

        # Text watermark
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

        text_form = QFormLayout()
        text_form.setSpacing(10)
        text_form.addRow("Text:", self.text)
        text_form.addRow("Font size:", self.font_size)
        color_row = QHBoxLayout()
        color_row.addWidget(self.color_btn)
        color_row.addWidget(self.color_preview)
        color_row.addStretch(1)
        cw = QWidget(); cw.setLayout(color_row)
        text_form.addRow("Color:", cw)
        text_widget = QWidget(); text_widget.setLayout(text_form)

        # Image watermark
        self.wm_file = FilePicker("Watermark image", "Images (*.png *.jpg *.jpeg *.webp)")
        self.wm_scale = QSpinBox()
        self.wm_scale.setRange(1, 100)
        self.wm_scale.setValue(25)
        self.wm_scale.setSuffix(" %")
        img_form = QFormLayout()
        img_form.setSpacing(10)
        img_form.addRow(self.wm_file)
        img_form.addRow("Size (% of base width):", self.wm_scale)
        img_widget = QWidget(); img_widget.setLayout(img_form)

        self.stack = QStackedWidget()
        self.stack.addWidget(text_widget)
        self.stack.addWidget(img_widget)

        self.position = QComboBox()
        self.position.addItems(core_wm.POSITIONS)
        self.position.setCurrentText("bottom-right")

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
        common_form.addRow(self.stack)
        common_form.addRow("Position:", self.position)
        common_form.addRow("Opacity:", op_row)

        opts = QGroupBox("Watermark Options")
        opts.setLayout(common_form)
        opts.setMinimumWidth(360)

        # ---------- Preview panel ----------
        self.preview_label = QLabel("Add an image to see live preview")
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setAlignment(Qt.AlignCenter)

        preview_box_layout = QVBoxLayout()
        preview_box_layout.addWidget(self.preview_label, 1)
        preview_box = QGroupBox("Live Preview")
        preview_box.setLayout(preview_box_layout)

        # Options + preview side-by-side
        opts_row = QHBoxLayout()
        opts_row.setSpacing(14)
        opts_row.addWidget(opts, 0)
        opts_row.addWidget(preview_box, 1)

        # ---------- Buttons ----------
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

        # ---------- Main layout ----------
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.queue)
        layout.addWidget(self.out_picker)
        layout.addLayout(opts_row)
        layout.addLayout(btns)
        layout.addWidget(self.log_panel)

        # ---------- Preview debounce ----------
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(200)
        self._preview_timer.timeout.connect(self._update_preview)
        self._wire_preview_signals()

    # ---------- preview ----------
    def _wire_preview_signals(self):
        self.text.textChanged.connect(self._schedule_preview)
        self.font_size.valueChanged.connect(self._schedule_preview)
        self.opacity.valueChanged.connect(self._schedule_preview)
        self.position.currentIndexChanged.connect(self._schedule_preview)
        self.kind.currentIndexChanged.connect(self._schedule_preview)
        self.wm_file.edit.textChanged.connect(self._schedule_preview)
        self.wm_scale.valueChanged.connect(self._schedule_preview)
        self.queue.countChanged.connect(self._schedule_preview)

    def _schedule_preview(self, *args):
        self._preview_timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_preview()

    def _update_preview(self):
        files = self.queue.files()
        if not files:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Add an image to see live preview")
            return

        src = files[0]
        try:
            with Image.open(src) as base:
                base_rgba = base.convert("RGBA")

            # Fit into the preview box while preserving aspect ratio.
            # Use actual label size so preview always fills available area.
            box_w = max(320, self.preview_label.width() - 16)
            box_h = max(240, self.preview_label.height() - 16)

            orig_w = base_rgba.width
            ratio = min(box_w / base_rgba.width, box_h / base_rgba.height)
            new_w = max(1, int(base_rgba.width * ratio))
            new_h = max(1, int(base_rgba.height * ratio))
            base_rgba = base_rgba.resize((new_w, new_h), Image.LANCZOS)

            # Recompute ratio from actual scale so font/size match output proportionally
            ratio = new_w / orig_w

            kind = "text" if self.kind.currentIndex() == 0 else "image"
            scaled_font = max(6, int(self.font_size.value() * ratio))

            out = core_wm.apply_watermark(
                base_rgba,
                kind=kind,
                text=self.text.text(),
                wm_image=self.wm_file.path(),
                position=self.position.currentText(),
                opacity=self.opacity.value(),
                font_size=scaled_font,
                color=self._color,
                wm_scale_pct=self.wm_scale.value(),
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
        if kind == "text" and not self.text.text().strip():
            QMessageBox.warning(self, "Missing", "Enter watermark text.")
            return
        if kind == "image" and not self.wm_file.path():
            QMessageBox.warning(self, "Missing", "Pick a watermark image.")
            return

        self.log_panel.reset()
        self.log_panel.append(f"Applying watermark to {len(files)} image(s)…")

        self.worker = BatchWorker(
            core_wm.run_watermark_batch,
            files, out,
            kind=kind,
            text=self.text.text(),
            wm_image=self.wm_file.path(),
            position=self.position.currentText(),
            opacity=self.opacity.value(),
            font_size=self.font_size.value(),
            color=self._color,
            wm_scale_pct=self.wm_scale.value(),
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
