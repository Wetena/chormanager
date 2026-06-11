"""Availability-related dialogs."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QDialogButtonBox, QStyledItemDelegate,
)
from PyQt6.QtCore import Qt


AVAILABILITY_STATUS = [
    ("yes", "✓ Verfügbar / Zusage", "yes"),
    ("no", "✗ Nicht verfügbar / Absage", "no"),
    ("none", "○ Keine Rückmeldung", "none"),
    ("conditional", "✓? Zusage unter Vorbehalt", "conditional"),
    ("unknown", "? Weiß nicht", "unknown"),
    ("maybe", "~ Vielleicht", "maybe"),
]


class AvailabilityDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        for status_code, status_label, short_label in AVAILABILITY_STATUS:
            combo.addItem(status_label, status_code)
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        if value is None:
            value = "none"
        i = editor.findData(value)
        if i >= 0:
            editor.setCurrentIndex(i)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentData(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class AvailabilityDialog(QDialog):
    """Dialog for managing singer availability."""

    def __init__(self, singer_id: str, event_id: str, parent=None):
        super().__init__(parent)
        self.singer_id = singer_id
        self.event_id = event_id
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Verfügbarkeit")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        self.status_combo = QComboBox()
        self.status_combo.addItem("✓ Verfügbar / Zusage", "yes")
        self.status_combo.addItem("✗ Nicht verfügbar / Absage", "no")
        self.status_combo.addItem("○ Keine Rückmeldung", "none")
        self.status_combo.addItem("✓? Zusage unter Vorbehalt", "conditional")
        self.status_combo.addItem("? Weiß nicht", "unknown")
        self.status_combo.addItem("Vielleicht", "maybe")

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_combo)
        layout.addLayout(status_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_status(self):
        return self.status_combo.currentData()

    def accept(self):
        from chormanager.domain.repository import AvailabilityRepository
        from chormanager.data.database import Database

        db = Database()
        db.connect()
        avail_repo = AvailabilityRepository(db)
        avail_repo.update(self.singer_id, self.event_id, self.get_status())
        db.close()
        super().accept()
