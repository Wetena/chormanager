"""Backup and restore dialog."""

from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QMessageBox, QDialogButtonBox,
)
from .drop_zone import DropZone


class BackupRestoreDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Backup & Restore")
        self.setMinimumSize(550, 450)
        self.service = None
        self.pending_restore_path = None
        self.restored = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        backup_box = QGroupBox("Daten sichern")
        backup_layout = QVBoxLayout(backup_box)

        self.backup_info = QLabel(
            "Erstellt eine ZIP-Datei mit allen App-Daten:\n"
            "• Datenbank (chor.db)\n"
            "• Einstellungen (config/)\n"
            "• Choraufstellung-JSONs"
        )
        self.backup_info.setWordWrap(True)

        self.backup_btn = QPushButton("Backup erstellen...")
        self.backup_btn.clicked.connect(self._on_backup)

        backup_layout.addWidget(self.backup_info)
        backup_layout.addWidget(self.backup_btn)

        restore_box = QGroupBox("Daten wiederherstellen")
        restore_layout = QVBoxLayout(restore_box)

        restore_info = QLabel(
            "Stellt Daten aus einer Backup-Datei wieder her.\n"
            "Nur neuere Dateien werden überschrieben."
        )
        restore_info.setWordWrap(True)

        self.drop_zone = DropZone()
        self.drop_zone.file_selected.connect(self._on_file_dropped)

        self.restore_btn = QPushButton("Backup-Datei laden...")
        self.restore_btn.clicked.connect(lambda: self.drop_zone.mousePressEvent(None))

        restore_layout.addWidget(restore_info)
        restore_layout.addWidget(self.drop_zone)
        restore_layout.addWidget(self.restore_btn)

        layout.addWidget(backup_box)
        layout.addWidget(restore_box)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_backup(self):
        if self.service is None:
            return
        default_name = (
            f"chormanager-data-backup-{datetime.now().strftime('%Y-%m-%d')}.zip"
        )
        filename, _ = QFileDialog.getSaveFileName(
            self, "Backup speichern unter", default_name, "ZIP Dateien (*.zip)"
        )
        if not filename:
            return
        try:
            path = self.service.create_backup(filename)
            mb = QMessageBox(self)
            mb.setWindowTitle("Backup erstellt")
            mb.setText(f"Backup erfolgreich gespeichert:\n{path}")
            mb.setIcon(QMessageBox.Icon.Information)
            mb.exec()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Backup fehlgeschlagen:\n{e}")

    def _on_file_dropped(self, path):
        if self.service is None:
            return
        valid, msg = self.service.validate_backup(path)
        if not valid:
            QMessageBox.warning(self, "Ungültige Datei", msg)
            return
        changes = self.service.analyze_restore(path)
        total = len(changes["newer"]) + len(changes["new"]) + len(changes["older"])
        if total == 0:
            QMessageBox.information(
                self, "Restore", "Keine Dateien zum Wiederherstellen."
            )
            return
        self.pending_restore_path = path
        self._show_restore_warning(changes)

    def _show_restore_warning(self, changes):
        msg = QMessageBox(self)
        msg.setWindowTitle("Wiederherstellung bestätigen")
        msg.setIcon(QMessageBox.Icon.Warning)

        lines = []
        lines.append("Die folgenden Dateien werden überschrieben:\n")

        if changes["newer"]:
            lines.append("=== NEUERE Version aus Backup (wird überschrieben) ===")
            for c in changes["newer"]:
                lines.append(f"  {c['archive_name']}")
                lines.append(f"    Lokal:      {c['local_mtime_str']}")
                lines.append(f"    Backup:     {c['archive_mtime_str']}")
            lines.append("")

        if changes["new"]:
            lines.append("=== NEUE Dateien aus Backup (werden hinzugefügt) ===")
            for c in changes["new"]:
                lines.append(f"  {c['archive_name']}  (lokal: nicht vorhanden)")
            lines.append("")

        if changes["older"]:
            lines.append("=== LOKAL NEUER (keine Änderung) ===")
            for c in changes["older"]:
                lines.append(f"  {c['archive_name']}")
                lines.append(f"    Lokal:      {c['local_mtime_str']}")
                lines.append(f"    Backup:     {c['archive_mtime_str']}")

        msg.setText("\n".join(lines))
        msg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)

        reply = msg.exec()
        if reply == QMessageBox.StandardButton.Ok:
            self._do_restore()

    def _do_restore(self):
        if not self.pending_restore_path:
            return
        try:
            restored = self.service.restore_backup(self.pending_restore_path)
            self.restored = True
            QMessageBox.information(
                self, "Erfolgreich", f"{len(restored)} Dateien wiederhergestellt."
            )
            self.accept()
            self.drop_zone.label.setText(
                "Backup-Datei hierher ziehen\noder klicken zum Auswählen"
            )
            self.drop_zone.label.setStyleSheet("color: #888; font-size: 13px;")
            self.drop_zone.file_path = None
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Restore fehlgeschlagen:\n{e}")
