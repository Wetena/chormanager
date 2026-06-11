"""Event availability dialog - placeholder for full extraction."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QSizePolicy, QDialogButtonBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from chormanager.domain.repository import SingerRepository, AvailabilityRepository
from chormanager.config import load_voice_groups
from .availability import AVAILABILITY_STATUS


class EventAvailabilityDialog(QDialog):
    """Dialog for managing availability for a specific event."""

    def __init__(self, db, event, parent=None, besetzung_ids=None,
                 besetzung_name=None, besetzung_count=0):
        super().__init__(parent)
        self.db = db
        self.event = event
        self.besetzung_ids = besetzung_ids
        self.besetzung_name = besetzung_name
        self.besetzung_count = besetzung_count
        self.singer_repo = SingerRepository(db)
        self.avail_repo = AvailabilityRepository(db)
        self._setup_ui()
        self._load_availability()

    def _setup_ui(self):
        self.setWindowTitle(f"Verfügbarkeit: {self.event.name}")
        self.setMinimumSize(900, 600)
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Kurzname", "Stimmgruppe", "Status"])
        layout.addWidget(self.table)

        self.summary_label = QLabel("")
        layout.addWidget(self.summary_label)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_availability(self):
        singers = self.singer_repo.get_active()
        if self.besetzung_ids is not None:
            singers = [s for s in singers if s.id in self.besetzung_ids]

        self.table.setRowCount(len(singers))
        for row, singer in enumerate(singers):
            self.table.setItem(row, 0, QTableWidgetItem(singer.short_name or singer.full_name or ""))
            self.table.setItem(row, 1, QTableWidgetItem(singer.voice_group or ""))

            avail = self.avail_repo.get_by_ids(singer.id, self.event.id)
            current_status = avail.status if avail else None

            status_combo = QComboBox()
            for status_code, status_label, short_label in AVAILABILITY_STATUS:
                status_combo.addItem(f"{status_label}", status_code)

            idx = status_combo.findData(current_status or "none")
            if idx >= 0:
                status_combo.setCurrentIndex(idx)

            self.table.setCellWidget(row, 2, status_combo)
            self.table.setRowHeight(row, 60)

        self.table.resizeColumnsToContents()

    def accept(self):
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if not name_item:
                continue
            status_widget = self.table.cellWidget(row, 2)
            if isinstance(status_widget, QComboBox):
                status_code = status_widget.currentData()
                if status_code is not None:
                    self.avail_repo.update(name_item.data(Qt.ItemDataRole.UserRole), self.event.id, status_code)
        super().accept()
