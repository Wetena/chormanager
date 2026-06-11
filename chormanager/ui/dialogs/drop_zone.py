"""File drop zone widget."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DropZone(QFrame):
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(300, 80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.label = QLabel("Backup-Datei hierher ziehen\noder klicken zum Auswählen")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #888; font-size: 13px;")
        layout.addWidget(self.label)
        self.file_path = None

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        if e.mimeData().hasUrls():
            url = e.mimeData().urls()[0]
            self.file_path = url.toLocalFile()
            self.label.setText(f"Ausgewählt:\n{self.file_path}")
            self.label.setStyleSheet("color: #333; font-size: 13px;")
            self.file_selected.emit(self.file_path)

    def mousePressEvent(self, event):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Backup-Datei auswählen", "", "ZIP Dateien (*.zip)"
        )
        if filename:
            self.file_path = filename
            self.label.setText(f"Ausgewählt:\n{filename}")
            self.label.setStyleSheet("color: #333; font-size: 13px;")
            self.file_selected.emit(filename)
