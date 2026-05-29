"""
SpiderFEA — UI Dialogs
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class AboutDialog(QDialog):
    """Simple About dialog showing version and credits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About SpiderFEA")
        self.setMinimumSize(300, 150)

        layout = QVBoxLayout(self)

        title = QLabel("<h2>SpiderFEA</h2>")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        version = QLabel("<p>Version 0.1.0</p>")
        layout.addWidget(version)

        credits = QLabel(
            "<p>A graphical frontend for 2D axisymmetric FEA of loudspeaker spiders.</p>"
            "<p>Powered by ElmerFEM and Gmsh.</p>"
        )
        credits.setWordWrap(True)
        layout.addWidget(credits)

        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("btn_ok")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
