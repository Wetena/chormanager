"""Event creation/editing dialog."""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateTimeEdit, QTextEdit, QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QDateTime


class EventDialog(QDialog):
    """Dialog for creating/editing events."""

    def __init__(self, event=None, db=None, parent=None, prefilled_project_id=None):
        super().__init__(parent)
        self.event = event
        self.db = db
        self.prefilled_project_id = prefilled_project_id
        self._setup_ui(db)

        if event:
            self._populate_from_event()
        elif prefilled_project_id:
            self._select_project(prefilled_project_id)

    def _setup_ui(self, db=None):
        from chormanager.domain.repository import ProjectRepository

        self.setWindowTitle(
            "Termin hinzufügen" if not self.event else "Termin bearbeiten"
        )
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        layout.addRow("Name:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Generalprobe (GP)", "gp")
        self.type_combo.addItem("Orchesterprobe (OP)", "op")
        self.type_combo.addItem("Auftritt (SOFA)", "sofa")
        self.type_combo.addItem("Probe", "probe")
        self.type_combo.addItem("Konzert", "konzert")
        self.type_combo.addItem("Auftritt", "auftritt")
        self.type_combo.addItem("Sonstiges", "sonstiges")
        layout.addRow("Typ:", self.type_combo)

        self.date_input = QDateTimeEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDateTime(QDateTime.currentDateTime())
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        layout.addRow("Datum/Zeit:", self.date_input)

        self.project_combo = QComboBox()
        self.project_combo.addItem("(keins)", None)
        if db:
            project_repo = ProjectRepository(db)
            projects = project_repo.get_all()
            for p in projects:
                self.project_combo.addItem(p.name, p.id)
        layout.addRow("Projekt:", self.project_combo)
        self.location_input = QLineEdit()
        layout.addRow("Ort:", self.location_input)

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        layout.addRow("Beschreibung:", self.description_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _populate_from_event(self):
        self.name_input.setText(self.event.name)

        index = self.type_combo.findData(self.event.event_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        if self.event.date:
            dt = QDateTime.fromString(self.event.date, Qt.DateFormat.ISODate)
            if dt.isValid():
                self.date_input.setDateTime(dt)

        if self.event.description:
            self.description_input.setPlainText(self.event.description)

        if self.event.project_id:
            index = self.project_combo.findData(self.event.project_id)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)

        if self.event.location:
            self.location_input.setText(self.event.location)

    def _select_project(self, project_id):
        index = self.project_combo.findData(project_id)
        if index >= 0:
            self.project_combo.setCurrentIndex(index)

    def get_data(self):
        data = {
            "name": self.name_input.text().strip(),
            "event_type": self.type_combo.currentData(),
            "date": self.date_input.dateTime().toString(Qt.DateFormat.ISODate),
            "description": self.description_input.toPlainText().strip(),
            "project_id": self.project_combo.currentData(),
            "location": self.location_input.text().strip(),
        }
        return data
