from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QComboBox,
    QPushButton, QMessageBox, QGroupBox, QCheckBox, QStackedWidget
)

from app.tabs.base_tab import FolderPicker, LogPanel
from app.widgets.file_queue import FileQueue
from app.worker import BatchWorker, EstimateWorker
from app.core import resize as core_resize


class ResizeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: BatchWorker | None = None
        self._estimate_worker: EstimateWorker | None = None

        self.queue = FileQueue()
        self.out_picker = FolderPicker("Output folder")

        self.mode = QComboBox()
        self.mode.addItems(["Dimensions (px)", "Percent (%)"])
        self.mode.currentIndexChanged.connect(lambda i: self.stack.setCurrentIndex(i))

        self.width = QSpinBox()
        self.width.setRange(0, 20000)
        self.width.setValue(1920)
        self.height = QSpinBox()
        self.height.setRange(0, 20000)
        self.height.setValue(0)
        self.keep_aspect = QCheckBox("Keep aspect ratio")
        self.keep_aspect.setChecked(True)

        dim_form = QFormLayout()
        dim_form.setSpacing(10)
        dim_form.addRow("Width:", self.width)
        dim_form.addRow("Height:", self.height)
        dim_form.addRow("", self.keep_aspect)
        dim_widget = QWidget(); dim_widget.setLayout(dim_form)

        self.percent = QSpinBox()
        self.percent.setRange(1, 1000)
        self.percent.setValue(50)
        self.percent.setSuffix(" %")
        pct_form = QFormLayout()
        pct_form.setSpacing(10)
        pct_form.addRow("Scale:", self.percent)
        pct_widget = QWidget(); pct_widget.setLayout(pct_form)

        self.stack = QStackedWidget()
        self.stack.addWidget(dim_widget)
        self.stack.addWidget(pct_widget)

        opts_form = QFormLayout()
        opts_form.setSpacing(10)
        opts_form.addRow("Mode:", self.mode)
        opts_form.addRow(self.stack)
        opts = QGroupBox("Resize Options")
        opts.setLayout(opts_form)

        self.start_btn = QPushButton("Start Resize")
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

        self.mode.currentIndexChanged.connect(lambda _: self._estimate_timer.start())
        self.width.valueChanged.connect(lambda _: self._estimate_timer.start())
        self.height.valueChanged.connect(lambda _: self._estimate_timer.start())
        self.percent.valueChanged.connect(lambda _: self._estimate_timer.start())
        self.keep_aspect.stateChanged.connect(lambda _: self._estimate_timer.start())
        self.queue.countChanged.connect(lambda _: self._estimate_timer.start())

    def _run_estimate(self):
        files = self.queue.files()
        if not files:
            return

        if self._estimate_worker and self._estimate_worker.isRunning():
            self._estimate_worker.cancel()

        if self.mode.currentIndex() == 0:
            mode = "dimensions"
            w = self.width.value() or None
            h = self.height.value() or None
            pct = None
            if not w and not h:
                return
        else:
            mode = "percent"
            w = h = None
            pct = self.percent.value()

        keep_aspect = self.keep_aspect.isChecked()

        def estimator(src):
            return core_resize.estimate_resize_size(src, mode, w, h, pct, keep_aspect)

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

        if self.mode.currentIndex() == 0:
            mode = "dimensions"
            w = self.width.value() or None
            h = self.height.value() or None
            pct = None
            if not w and not h:
                QMessageBox.warning(self, "Invalid", "Set width and/or height.")
                return
        else:
            mode = "percent"
            w = h = None
            pct = self.percent.value()

        self.log_panel.reset()
        self.log_panel.append(f"Starting resize of {len(files)} image(s)…")

        self.worker = BatchWorker(
            core_resize.run_resize_batch,
            files, out, mode, w, h, pct, self.keep_aspect.isChecked(),
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
