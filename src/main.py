"""
SpiderFEA — Application Entry Point
"""

import multiprocessing
import sys
from pathlib import Path

# Ensure src is on path when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtWidgets import QApplication

from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SpiderFEA")
    app.setApplicationVersion("0.1.4")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
