"""Version check dialog."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QDialogButtonBox, QApplication,
)


class VersionCheckDialog(QDialog):
    """Dialog for checking application version."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Version prüfen")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout(self)

        self.info_label = QLabel("Aktuelle Version: Unbekannt")
        self.info_label.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(self.info_label)

        self.status_label = QLabel("Bereit zur Prüfung...")
        self.status_label.setStyleSheet("padding: 10px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        button_box = QDialogButtonBox()
        self.check_btn = QPushButton("Auf neue Version prüfen")
        self.check_btn.clicked.connect(self._check_version)
        button_box.addButton(self.check_btn, QDialogButtonBox.ButtonRole.ActionRole)

        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.reject)
        button_box.addButton(close_btn, QDialogButtonBox.ButtonRole.RejectRole)

        layout.addWidget(button_box)

    def _check_version(self):
        self.status_label.setText("Prüfe GitHub Repository...")
        QApplication.processEvents()

        try:
            import urllib.request
            import json
            import subprocess

            url = "https://api.github.com/repos/asb-42/chormanager/branches/0.4"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'ChorManager')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                remote_sha = data['commit']['sha'].strip()[:7]

                from chormanager.config import get_app_dir
                result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    capture_output=True, text=True, cwd=str(get_app_dir())
                )
                local_sha = result.stdout.strip()[:7]

                self.info_label.setText(f"Lokal: {local_sha} | Remote: {remote_sha}")

                if remote_sha != local_sha:
                    self.status_label.setText(f"Update verfügbar: {remote_sha}")
                    self.check_btn.setText("Update durchführen")
                    self.check_btn.clicked.disconnect()
                    self.check_btn.clicked.connect(self._do_update)
                else:
                    self.status_label.setText("Code ist aktuell")

        except Exception as e:
            self.status_label.setText(f"Fehler bei der Prüfung: {str(e)}")

    def _do_update(self):
        self.status_label.setText("Aktualisiere von GitHub...")
        QApplication.processEvents()

        try:
            import subprocess
            from chormanager.config import get_app_dir
            result = subprocess.run(
                ['git', 'pull', 'origin', '0.4'],
                capture_output=True, text=True, cwd=str(get_app_dir())
            )

            if result.returncode == 0:
                self.status_label.setText("Aktualisierung erfolgreich! Bitte App neu starten.")
                self.check_btn.setEnabled(False)
            else:
                self.status_label.setText(f"Update fehlgeschlagen: {result.stderr}")
        except Exception as e:
            self.status_label.setText(f"Update fehlgeschlagen: {str(e)}")
