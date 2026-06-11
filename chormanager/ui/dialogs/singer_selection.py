"""Singer selection dialog - placeholder for full extraction."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QCheckBox, QDialogButtonBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from chormanager.domain.repository import SingerRepository
from chormanager.config import load_voice_groups


class SingerSelectionDialog(QDialog):
    """Dialog for selecting singers for a Besetzung."""

    def __init__(self, db, pre_selected_ids=None, besetzung_name=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.pre_selected_ids = pre_selected_ids or []
        self.selected_ids = set(self.pre_selected_ids)
        self.besetzung_name = besetzung_name or "besetzung"
        self._setup_ui()
        self._load_singers()

    def _setup_ui(self):
        self.setWindowTitle("Sänger auswählen")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)

        info_label = QLabel("Markieren Sie die Sänger, die zur Besetzung gehören sollen.")
        layout.addWidget(info_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Suchen (Name, Kurzname)...")
        self.search_box.textChanged.connect(self._load_singers)
        layout.addWidget(self.search_box)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["✓", "Name", "Kurzname", "Stimmgruppe", "Alter"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Alle auswählen")
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Alle abwählen")
        deselect_all_btn.clicked.connect(self._deselect_all)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_singers(self):
        singer_repo = SingerRepository(self.db)
        singers = singer_repo.get_all()
        self.table.setRowCount(len(singers))
        for row, singer in enumerate(singers):
            checkbox = QCheckBox()
            checkbox.setCheckState(
                Qt.CheckState.Checked if singer.id in self.selected_ids else Qt.CheckState.Unchecked
            )
            self.table.setCellWidget(row, 0, checkbox)
            self.table.setItem(row, 1, QTableWidgetItem(singer.full_name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(singer.short_name or ""))
            self.table.setItem(row, 3, QTableWidgetItem(singer.voice_group or ""))

    def _select_all(self):
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setCheckState(Qt.CheckState.Unchecked)
        self.selected_ids.clear()

    def get_selected_ids(self) -> list:
        return list(self.selected_ids)
