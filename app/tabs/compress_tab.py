from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSlider, QComboBox,
    QPushButton, QMessageBox, QLabel, QGroupBox
)

from app.tabs.base_tab import FolderPicker, LogPanel
from app.widgets.file_queue import FileQueue
from app.worker import BatchWorker, EstimateWorker
from app.core import compress as core_compress


class CompressTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: BatchWorker | None = None
        self._estimate_worker: EstimateWorker | None = None

        self.queue = FileQueue()
        self.out_picker = FolderPicker("Output folder")

        self.format = QComboBox()
        self.format.addItems(["JPEG", "WEBP", "PNG"])

        self.quality = QSlider(Qt.Horizontal)
        self.quality.setRange(1, 100)
        self.quality.setValue(80)
        self.quality_label = QLabel("80")
        self.quality_label.setFixedWidth(30)
        self.quality.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))

        q_row = QHBoxLayout()
        q_row.addWidget(self.quality, 1)
        q_row.addWidget(self.quality_label)

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Format:", self.format)
        form.addRow("Quality:", q_row)

        opts = QGroupBox("Compression Options")
        opts.setLayout(form)

        self.start_btn = QPushButton("Start Compression")
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
        layout.addWidget(self.queue, 1)
        layout.addWidget(self.out_picker)
        layout.addWidget(opts)
        layout.addLayout(btns)
        layout.addWidget(self.log_panel)

        # ---------- Estimate (debounced) ----------
        self._estimate_timer = QTimer(self)
        self._estimate_timer.setSingleShot(True)
        self._estimate_timer.setInterval(400)
        self._estimate_timer.timeout.connect(self._run_estimate)

        self.quality.valueChanged.connect(lambda _: self._estimate_timer.start())
        self.format.currentIndexChanged.connect(lambda _: self._estimate_timer.start())
        self.queue.countChanged.connect(lambda _: self._estimate_timer.start())

    def _run_estimate(self):
        files = self.queue.files()
        if not files:
            return

        if self._estimate_worker and self._estimate_worker.isRunning():
            self._estimate_worker.cancel()

        quality = self.quality.value()
        fmt = self.format.currentText()

        def estimator(src):
            return core_compress.estimate_compress_size(src, quality, fmt)

        self.queue.mark_all_pending()
        self._estimate_worker = EstimateWorker(files, estimator)
        self._estimate_worker.result.connect(self.queue.set_estimate)
        self._estimate_worker.start()

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
        self.log_panel.append(f"Starting compression of {len(files)} image(s)…")

        self.worker = BatchWorker(
            core_compress.run_compress_batch,
            files, out, self.quality.value(), self.format.currentText(),
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
