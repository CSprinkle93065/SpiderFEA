import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, '.')

from unittest.mock import MagicMock
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QPushButton, QDialog, QMessageBox, QApplication
from src.main_window import MainWindow

import src.api as api
api.gmsh = MagicMock()
import subprocess
subprocess.run = MagicMock(return_value=MagicMock(returncode=0))

app = QApplication.instance() or QApplication(sys.argv)
window = MainWindow()
buttons = window.findChildren(QPushButton)
print(f"Found {len(buttons)} buttons")

for btn in buttons:
    print(f"Clicking {btn.objectName()}...")
    def dismiss():
        for dlg in window.findChildren(QDialog):
            dlg.reject()
        for top in QApplication.topLevelWidgets():
            if isinstance(top, (QDialog, QMessageBox)):
                top.reject()
    QTimer.singleShot(200, dismiss)
    QTest.mouseClick(btn, Qt.MouseButton.LeftButton)
    print(f"  {btn.objectName()} clicked OK")

window.close()
print("All buttons clicked successfully")
