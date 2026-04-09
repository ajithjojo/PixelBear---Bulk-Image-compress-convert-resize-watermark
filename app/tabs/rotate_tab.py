from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QSpinBox,
    QPushButton, QMessageBox, QGroupBox, QCheckBox, QStackedWidget
)

from app.tabs.base_tab import FolderPicker, LogPanel
from app.widgets.file_queue import FileQueue
from app.worker import BatchWorker
from app.core import rotate as core_rotate


class RotateTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: BatchWorker | None = None

        self.queue = FileQueue()
        self.out_picker = FolderPicker("Output folder")

        self.preset = QComboBox()
        self.preset.addItems([
            "90° Clockwise",
            "90° Counter-clockwise",
            "180°",
            "Custom angle",
            "No rotation",
        ])
        self.preset.currentIndexChanged.connect(self._preset_changed)

        self.custom_angle = QSpinBox()
        self.custom_angle.setRange(-360, 360)
        self.custom_angle.setValue(45)
        self.custom_angle.setSuffix(" °")
        self.custom_angle.setEnabled(False)

        self.flip_h = QCheckBox("Flip horizontally")
        self.flip_v = QCheckBox("Flip vertically")

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Rotation:", self.preset)
        form.addRow("Custom angle:", self.custom_angle)
        form.addRow("", self.flip_h)
        form.addRow("", self.flip_v)

        opts = QGroupBox("Rotate Options")
        opts.setLayout(form)

        self.start_btn = QPushButton("Start Rotate")
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

    def _preset_changed(self, idx):
        self.custom_angle.setEnabled(idx == 3)

    def _resolve_angle(self) -> int:
        idx = self.preset.currentIndex()
        if idx == 0:
            return 90
        if idx == 1:
            return 270
        if idx == 2:
            return 180
        if idx == 3:
            return self.custom_angle.value() % 360
        return 0

    def start(self):
        files = self.queue.files()
        out = self.out_picker.path()
        if not files:
            QMessageBox.warning(self, "No images", "Please add images to the queue.")
            return
        if not out:
            QMessageBox.warning(self, "Missing", "Please select an output folder.")
            return

        angle = self._resolve_angle()
        flip_h = self.flip_h.isChecked()
        flip_v = self.flip_v.isChecked()

        if angle == 0 and not flip_h and not flip_v:
            QMessageBox.warning(self, "No change", "Choose a rotation or flip.")
            return

        self.log_panel.reset()
        self.log_panel.append(f"Rotating {len(files)} image(s)…")

        self.worker = BatchWorker(
            core_rotate.run_rotate_batch,
            files, out, angle, flip_h, flip_v, (255, 255, 255),
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
