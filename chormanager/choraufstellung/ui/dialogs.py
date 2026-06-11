"""Reusable dialogs for ChorAufstellung.

Extracted from main.py for separation of concerns.
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox, QWidget,
)
from PyQt6.QtCore import Qt, QCompleter


def _import_singer():
    """Lazy import of Singer and VoiceGroup to avoid circular imports."""
    try:
        from singer_model import Singer, VoiceGroup
        return Singer, VoiceGroup
    except ImportError:
        from enum import Enum
        class VoiceGroup(Enum):
            SOPRAN_1 = "Sopran 1"
        class Singer:
            def __init__(self, name, voice_group, height=0, singer_id="1"):
                self.name, self.voice_group, self.height, self.singer_id = name, voice_group, height, singer_id
        return Singer, VoiceGroup


def _import_config():
    """Lazy import of load_voice_groups_config."""
    try:
        from config import load_voice_groups_config
        return load_voice_groups_config
    except ImportError:
        return lambda: []


class AddSingerDialog(QDialog):
    """Dialog for adding or editing a singer."""

    def __init__(self, p=None, singer=None):
        super().__init__(p)
        self.singer = singer
        Singer, VoiceGroup = _import_singer()
        self.Singer = Singer
        self.VoiceGroup = VoiceGroup
        self.setWindowTitle("Sänger bearbeiten" if singer else "Sänger hinzufügen")
        l = QFormLayout(self)
        self.n = QLineEdit()
        self.n.setPlaceholderText("Nachname, Vorname")
        if singer:
            self.n.setText(singer.name)
        l.addRow("Name:", self.n)
        self.v = QComboBox()
        for vg in self.VoiceGroup:
            self.v.addItem(vg.value if hasattr(vg, 'value') else str(vg), vg)
        if singer:
            vg_val = singer.voice_group.value if hasattr(singer.voice_group, 'value') else str(singer.voice_group)
            idx = self.v.findText(vg_val)
            if idx >= 0:
                self.v.setCurrentIndex(idx)
        l.addRow("Stimmgruppe:", self.v)
        self.h = QLineEdit()
        if singer and singer.height > 0:
            self.h.setText(str(singer.height))
        l.addRow("Größe (cm):", self.h)
        bl = QHBoxLayout()
        bl.addWidget(QPushButton("Speichern", clicked=self.accept))
        bl.addWidget(QPushButton("Abbrechen", clicked=self.reject))
        l.addRow(bl)

    def get_singer(self):
        n = self.n.text().strip()
        if not n:
            return None
        h = 0
        try:
            h = int(self.h.text().strip()) if self.h.text().strip() else 0
        except Exception:
            pass
        if self.singer:
            return self.Singer(n, self.v.currentData(), h, self.singer.singer_id)
        return self.Singer(n, self.v.currentData(), h)


class AffinityDialog(QDialog):
    """Dialog for setting a singer's affinity partner."""

    def __init__(self, p=None, singer=None, all_singers=None):
        super().__init__(p)
        self.singer = singer
        self.all_singers = all_singers or []
        self.setWindowTitle(f"Nähe setzen für {singer.name}")
        self.setMinimumWidth(350)
        l = QVBoxLayout(self)
        l.addWidget(QLabel(f"Singpartner für <b>{singer.name}</b> auswählen:"))

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.lineEdit().setPlaceholderText("Name eingeben oder auswählen...")

        other_singers = [s for s in self.all_singers if s.singer_id != singer.singer_id]
        for s in other_singers:
            self.combo.addItem(s.name, s.singer_id)

        if singer.affinity:
            idx = self.combo.findData(singer.affinity)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)

        completer = QCompleter([s.name for s in other_singers], self)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.combo.setCompleter(completer)

        l.addWidget(self.combo)

        clear_btn = QPushButton("Keine Nähe")
        clear_btn.clicked.connect(self.clear_affinity)
        l.addWidget(clear_btn)

        bl = QHBoxLayout()
        bl.addWidget(QPushButton("Speichern", clicked=self.accept))
        bl.addWidget(QPushButton("Abbrechen", clicked=self.reject))
        l.addLayout(bl)

    def clear_affinity(self):
        self.combo.setCurrentIndex(-1)
        self.combo.setCurrentText("")

    def get_affinity_singer_id(self):
        text = self.combo.currentText().strip()
        data = self.combo.currentData()
        if data:
            return data
        for s in self.all_singers:
            if s.name == text:
                return s.singer_id
        return ""


class VoicingConfigDialog(QDialog):
    """Dialog for configuring active voice groups."""

    def __init__(self, p=None):
        super().__init__(p)
        load_voice_groups_config = _import_config()
        self.setStyleSheet("QDialog { background: #f9f6f0; }")
        self.setWindowTitle("Besatzung konfigurieren")
        self.resize(300, 350)
        l = QVBoxLayout(self)
        l.addWidget(QLabel("Aktive Stimmgruppen:"))
        s = QScrollArea()
        s.setWidgetResizable(True)
        l.addWidget(s)
        c = QWidget()
        self.vl = QVBoxLayout(c)
        s.setWidget(c)
        self.chk = {}
        for vg in load_voice_groups_config():
            cb = QCheckBox(vg["id"])
            color = vg["color"]
            cb.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid {color};
                    background-color: white;
                    border-radius: 3px;
                }}
                QCheckBox::indicator:hover {{
                    background-color: #f8f8f8;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {color};
                    border: 2px solid {color};
                    color: white;
                }}
                QCheckBox {{
                    spacing: 12px;
                    font-size: 10pt;
                }}
            """)
            self.chk[vg["id"]] = cb
            self.vl.addWidget(cb)
        bl = QHBoxLayout()
        bl.addWidget(QPushButton("OK", clicked=self.accept))
        bl.addWidget(QPushButton("Abbrechen", clicked=self.reject))
        l.addLayout(bl)

    def set_active(self, act):
        for g, c in self.chk.items():
            c.setChecked(g in act)

    def get_active(self):
        return [g for g, c in self.chk.items() if c.isChecked()]
