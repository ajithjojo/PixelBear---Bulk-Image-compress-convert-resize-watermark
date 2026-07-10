import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.styles import STYLESHEET
from app.resources import resource_path


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PixelBear")
    app.setOrganizationName("PixelBear")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    icon_path = resource_path("icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
