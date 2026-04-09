from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSlider, QComboBox,
    QPushButton, QMessageBox, QLabel, QGroupBox
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog

from app.tabs.base_tab import FolderPicker, LogPanel
from app.widgets.file_queue import FileQueue
from app.worker import BatchWorker
from app.core import convert as core_convert


class ConvertTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: BatchWorker | None = None
        self._bg = (255, 255, 255)

        self.queue = FileQueue()
        self.out_picker = FolderPicker("Output folder")

        self.format = QComboBox()
        self.format.addItems(["JPEG", "PNG", "WEBP"])
        self.format.currentIndexChanged.connect(self._format_changed)

        self.quality = QSlider(Qt.Horizontal)
        self.quality.setRange(1, 100)
        self.quality.setValue(90)
        self.quality_label = QLabel("90")
        self.quality_label.setFixedWidth(30)
        self.quality.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))

        q_row = QHBoxLayout()
        q_row.addWidget(self.quality, 1)
        q_row.addWidget(self.quality_label)

        self.bg_btn = QPushButton("Pick color…")
        self.bg_btn.clicked.connect(self._pick_bg)
        self.bg_preview = QLabel("  ")
        self.bg_preview.setStyleSheet(
            "background-color: white; border: 1px solid #3b456a; border-radius: 4px;"
        )
        self.bg_preview.setFixedSize(28, 22)
        bg_row = QHBoxLayout()
        bg_row.addWidget(self.bg_btn)
        bg_row.addWidget(self.bg_preview)
        bg_row.addStretch(1)
        bg_widget = QWidget(); bg_widget.setLayout(bg_row)

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Target format:", self.format)
        form.addRow("Quality:", q_row)
        self.bg_label = QLabel("Background:")
        form.addRow(self.bg_label, bg_widget)
        self.bg_label_field = bg_widget

        opts = QGroupBox("Convert Options")
        opts.setLayout(form)

        self.start_btn = QPushButton("Start Convert")
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.queue)
        layout.addWidget(self.out_picker)
        layout.addWidget(opts)
        layout.addLayout(btns)
        layout.addWidget(self.log_panel)

        self._format_changed(0)

    def _format_changed(self, idx):
        fmt = self.format.currentText().upper()
        is_jpeg = fmt == "JPEG"
        # Quality only relevant for JPEG and WEBP
        self.quality.setEnabled(fmt in ("JPEG", "WEBP"))
        # Background only relevant for JPEG (no alpha)
        self.bg_btn.setEnabled(is_jpeg)
        self.bg_preview.setEnabled(is_jpeg)

    def _pick_bg(self):
        c = QColorDialog.getColor(QColor(*self._bg), self, "Pick background color")
        if c.isValid():
            self._bg = (c.red(), c.green(), c.blue())
            self.bg_preview.setStyleSheet(
                f"background-color: rgb{self._bg}; border: 1px solid #3b456a; border-radius: 4px;"
            )

    def start(self):
        files = self.queue.files()
        out = self.out_picker.path()
        if not files:
            QMessageBox.warning(self, "No images", "Please add images to the queue.")
            return
        if not out:
            QMessageBox.warning(self, "Missing", "Please select an output folder.")
            return

        self.log_panel.reset()
        self.log_panel.append(f"Converting {len(files)} image(s) to {self.format.currentText()}…")

        self.worker = BatchWorker(
            core_convert.run_convert_batch,
            files, out, self.format.currentText(), self.quality.value(), self._bg,
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
