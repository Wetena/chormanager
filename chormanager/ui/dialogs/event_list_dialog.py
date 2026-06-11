"""Event list dialog - placeholder for full extraction."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QSizePolicy, QDialogButtonBox,
)
from PyQt6.QtCore import Qt

from chormanager.domain.repository import SingerRepository, EventRepository, AvailabilityRepository


class EventListDialog(QDialog):
    """Dialog showing events and their availability."""

    def __init__(self, db, parent=None, active_event_id=None):
        super().__init__(parent)
        self.db = db
        self.active_event_id = active_event_id
        self._setup_ui()
        self._load_events()

    def _setup_ui(self):
        self.setWindowTitle("Verfügbarkeit verwalten")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        self.event_combo = QComboBox()
        self.event_combo.currentIndexChanged.connect(self._on_event_changed)
        layout.addWidget(self.event_combo)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Sänger", "Stimmgruppe", "Status"])
        layout.addWidget(self.table)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _load_events(self):
        repo = EventRepository(self.db)
        if self.active_event_id:
            event = repo.get_by_id(self.active_event_id)
            if event:
                self.event_combo.addItem(f"{event.name} ({event.date})", event.id)
                self.event_combo.setCurrentIndex(0)
        else:
            events = repo.get_all()
            for event in events:
                self.event_combo.addItem(f"{event.name} ({event.date})", event.id)

    def _on_event_changed(self, index):
        event_id = self.event_combo.currentData()
        if not event_id:
            return
        self._load_availability(event_id)

    def _load_availability(self, event_id: str):
        singer_repo = SingerRepository(self.db)
        avail_repo = AvailabilityRepository(self.db)
        singers = singer_repo.get_all()
        self.table.setRowCount(len(singers))
        for row, singer in enumerate(singers):
            self.table.setItem(row, 0, QTableWidgetItem(singer.full_name or ""))
            self.table.setItem(row, 1, QTableWidgetItem(singer.voice_group or ""))
        self.table.resizeColumnsToContents()
