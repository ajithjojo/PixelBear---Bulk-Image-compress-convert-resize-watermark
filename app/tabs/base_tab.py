from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, QFileDialog,
    QPlainTextEdit, QProgressBar, QLabel
)


class FolderPicker(QWidget):
    def __init__(self, label: str = "Output folder"):
        super().__init__()
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(label)
        btn = QPushButton("Browse…")
        btn.clicked.connect(self._browse)
        lbl = QLabel(label)
        lbl.setFixedWidth(110)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(lbl)
        lay.addWidget(self.edit, 1)
        lay.addWidget(btn)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select folder")
        if d:
            self.edit.setText(d)

    def path(self) -> str:
        return self.edit.text().strip()


class FilePicker(QWidget):
    def __init__(self, label: str, file_filter: str = "All Files (*.*)"):
        super().__init__()
        self.filter = file_filter
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(label)
        btn = QPushButton("Browse…")
        btn.clicked.connect(self._browse)
        lbl = QLabel(label)
        lbl.setFixedWidth(110)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(lbl)
        lay.addWidget(self.edit, 1)
        lay.addWidget(btn)

    def _browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select file", "", self.filter)
        if f:
            self.edit.setText(f)

    def path(self) -> str:
        return self.edit.text().strip()


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.status = QLabel("Idle")
        self.status.setStyleSheet("color: #6b7280; font-weight: 500;")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(140)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(self.status)
        lay.addWidget(self.progress)
        lay.addWidget(self.log, 1)

    def append(self, msg: str):
        self.log.appendPlainText(msg)

    def set_progress(self, done: int, total: int):
        if total <= 0:
            self.progress.setValue(0)
            self.status.setText("Idle")
            return
        pct = int(done * 100 / total)
        self.progress.setValue(pct)
        self.status.setText(f"Processing  {done} / {total}")

    def reset(self):
        self.log.clear()
        self.progress.setValue(0)
        self.status.setText("Idle")
