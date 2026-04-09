import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame, QScrollArea, QPushButton
)

from app.tools_registry import TOOLS
from app.version import APP_VERSION
from app.updater import UpdateChecker, UpdateDialog
from app.resources import resource_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PixelBear — Image Toolkit")
        self.resize(1100, 800)
        self.setMinimumSize(900, 640)

        icon_path = resource_path("icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        root = QWidget()
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        root_lay.addWidget(self._build_sidebar())
        root_lay.addWidget(self._build_content(), 1)

        self.setCentralWidget(root)
        self.statusBar().showMessage("Ready")

        # Select first tool
        self.nav.setCurrentRow(0)

        # Update checker state
        self._update_checker: UpdateChecker | None = None
        self._manual_update_check = False

        # Auto-check for updates shortly after the window shows
        QTimer.singleShot(1500, self._check_for_updates)

    # ---------- Sidebar ----------
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 12)
        lay.setSpacing(0)

        title = QLabel("🐻 PixelBear")
        title.setObjectName("appTitle")
        subtitle = QLabel("IMAGE TOOLKIT")
        subtitle.setObjectName("appSubtitle")

        section = QLabel("TOOLS")
        section.setObjectName("sectionLabel")

        self.nav = QListWidget()
        self.nav.setObjectName("navList")
        self.nav.setFrameShape(QFrame.NoFrame)
        self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for tool in TOOLS:
            item = QListWidgetItem(tool.name)
            item.setToolTip(tool.subtitle)
            self.nav.addItem(item)

        self.nav.currentRowChanged.connect(self._on_nav_changed)

        self.update_btn = QPushButton("Check for updates")
        self.update_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #64748b;"
            " text-align: left; padding: 6px 18px; font-size: 11px; }"
            "QPushButton:hover { color: #a5b4fc; }"
        )
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(self._manual_check_for_updates)

        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet("color: #475569; font-size: 10px; padding: 2px 18px 4px 18px;")
        version.setAlignment(Qt.AlignLeft)

        lay.addWidget(title)
        lay.addWidget(subtitle)
        lay.addWidget(section)
        lay.addWidget(self.nav, 1)
        lay.addWidget(self.update_btn)
        lay.addWidget(version)

        return sidebar

    # ---------- Content area ----------
    def _build_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("contentArea")

        outer = QVBoxLayout(content)
        outer.setContentsMargins(28, 24, 28, 20)
        outer.setSpacing(14)

        # Page header (updated when nav changes)
        self.page_title = QLabel("")
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel("")
        self.page_subtitle.setObjectName("pageSubtitle")

        header = QVBoxLayout()
        header.setSpacing(2)
        header.addWidget(self.page_title)
        header.addWidget(self.page_subtitle)

        # Stacked widget holds all tool pages
        self.stack = QStackedWidget()
        for tool in TOOLS:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setWidget(tool.factory())
            self.stack.addWidget(scroll)

        outer.addLayout(header)
        outer.addWidget(self.stack, 1)

        return content

    def _on_nav_changed(self, row: int):
        if row < 0 or row >= len(TOOLS):
            return
        tool = TOOLS[row]
        self.page_title.setText(tool.name)
        self.page_subtitle.setText(tool.subtitle)
        self.stack.setCurrentIndex(row)
        self.statusBar().showMessage(f"{tool.name} — ready")

    # ---------- Update check ----------
    def _manual_check_for_updates(self):
        self._manual_update_check = True
        self.statusBar().showMessage("Checking for updates…")
        self._check_for_updates()

    def _check_for_updates(self):
        if self._update_checker and self._update_checker.isRunning():
            return
        self._update_checker = UpdateChecker(parent=self)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.no_update.connect(self._on_no_update)
        self._update_checker.error.connect(self._on_update_error)
        self._update_checker.start()

    def _on_update_available(self, info):
        self.statusBar().showMessage(f"Update available: v{info.version}")
        dlg = UpdateDialog(info, APP_VERSION, self)
        dlg.exec()
        self._manual_update_check = False

    def _on_no_update(self):
        self.statusBar().showMessage(f"You're on the latest version (v{APP_VERSION})")
        if self._manual_update_check:
            QMessageBox.information(
                self, "Up to date",
                f"You're already running the latest version (v{APP_VERSION}).",
            )
        self._manual_update_check = False

    def _on_update_error(self, msg: str):
        self.statusBar().showMessage(f"Update check failed: {msg}")
        if self._manual_update_check:
            QMessageBox.warning(
                self, "Update check failed",
                f"Could not check for updates:\n\n{msg}",
            )
        self._manual_update_check = False
