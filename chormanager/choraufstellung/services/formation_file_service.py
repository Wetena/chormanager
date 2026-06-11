"""Formation file service — handles file I/O, autosave, PDF export, optimizer.

Extracted from MainWindow to reduce its size.
"""

import os
import time

from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox, QPushButton, QDialog
)


def _import_deps():
    """Lazy imports to avoid circular dependencies."""
    try:
        from config import get_data_dir
    except ImportError:
        get_data_dir = lambda: os.path.expanduser("~/.local/share/choraufstellung")
    try:
        from workers import PDFExportWorker, OptimizerWorker
    except ImportError:
        PDFExportWorker = OptimizerWorker = None
    try:
        from pdf_export_dialog import PDFExportDialog
    except ImportError:
        PDFExportDialog = None
    try:
        from ui.optimizer_dialog import OptimizerDialog
    except ImportError:
        OptimizerDialog = None
    return get_data_dir, PDFExportWorker, OptimizerWorker, PDFExportDialog, OptimizerDialog


class FormationFileService:
    """Delegates file I/O operations that were on MainWindow."""

    def __init__(self, main_window):
        self._mw = main_window

    def new_file(self):
        mw = self._mw
        if mw.is_modified:
            r = QMessageBox.question(
                mw, "Ungespeichert", "Änderungen speichern?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if r == QMessageBox.StandardButton.Save:
                self.save_file()
            elif r == QMessageBox.StandardButton.Cancel:
                return
        mw.grid.singers = []
        mw.grid.refresh_grid()
        mw.singers = []
        mw.file = None
        mw.is_modified = False
        mw.update_grid_count()

    def open_file(self):
        fp, _ = QFileDialog.getOpenFileName(self._mw, "Öffnen", "", "JSON (*.json);;Alle (*)")
        if fp:
            self._open_file(fp)

    def _open_file(self, fp):
        mw = self._mw
        data = mw.storage.load_formation(fp)
        if not data:
            return
        mw.singers = data.get("singers", [])
        for s in mw.singers:
            if not hasattr(s, 'affinity'):
                s.affinity = ""
        mw.grid.singers = [s for s in mw.singers if s.row >= 0]
        mw.grid.refresh_grid()
        mw.pool.singers = mw.singers
        mw.pool.placed_singer_ids = mw.grid.get_placed_singer_ids()
        mw.pool.update_singers(mw.singers, mw.pool.placed_singer_ids)
        mw.file = fp
        mw.is_modified = False
        mw.update_grid_count()
        mw._loaded_metadata = data.get("metadata", {})

    def save_file(self):
        mw = self._mw
        grid_cells = mw.grid.rows * mw.grid.cols
        placed = len(mw.grid.singers)
        if placed > grid_cells:
            excess = placed - grid_cells
            msg_box = QMessageBox(mw)
            msg_box.setWindowTitle("Zu viele Sänger")
            msg_box.setText(f"Die Aufstellung hat {placed} Sänger im Raster, aber nur {grid_cells} Plätze.")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            btn_resize = QPushButton("Raster vergrößern")
            btn_pool = QPushButton("In Pool zurücksetzen")
            msg_box.addButton(btn_resize, QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton(btn_pool, QMessageBox.ButtonRole.ActionRole)
            reply = msg_box.exec()
            if reply == btn_pool:
                mw._reset_excess_to_pool(excess)
                return self._save_to_path(mw.file, metadata=mw._loaded_metadata)
            return False
        if not mw.file:
            return self.save_as_file()
        return self._save_to_path(mw.file, metadata=mw._loaded_metadata)

    def save_as_file(self):
        get_data_dir, _, _, _, _ = _import_deps()
        mw = self._mw
        data_dir = get_data_dir()
        auto_name = self.generate_filename(
            mw._loaded_metadata.get("event_date", ""),
            mw._loaded_metadata.get("event", "")
        )
        fp, _ = QFileDialog.getSaveFileName(mw, "Speichern", os.path.join(data_dir, auto_name), "JSON (*.json)")
        if not fp:
            return False
        if not fp.endswith(".json"):
            fp += ".json"
        grid_cells = mw.grid.rows * mw.grid.cols
        placed = len(mw.grid.singers)
        if placed > grid_cells:
            excess = placed - grid_cells
            msg_box = QMessageBox(mw)
            msg_box.setWindowTitle("Zu viele Sänger")
            msg_box.setText(f"Die Aufstellung hat {placed} Sänger im Raster, aber nur {grid_cells} Plätze.")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            btn_resize = QPushButton("Raster vergrößern")
            btn_pool = QPushButton("In Pool zurücksetzen")
            msg_box.addButton(btn_resize, QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton(btn_pool, QMessageBox.ButtonRole.ActionRole)
            reply = msg_box.exec()
            if reply == btn_pool:
                mw._reset_excess_to_pool(excess)
            else:
                return False
        return self._save_to_path(fp, metadata=mw._loaded_metadata)

    def _save_to_path(self, fp, metadata=None):
        mw = self._mw
        placed = mw.grid.get_placed_singers()
        singers = mw.singers
        rows = mw.grid.rows
        cols = mw.grid.cols
        staggered = mw.grid.staggered
        if mw.storage.save_formation(singers, rows, cols, fp, placed, staggered, metadata=metadata):
            mw.file = fp
            mw.is_modified = False
            mw.last_manual_save_mtime = time.time()
            return True
        return False

    @staticmethod
    def generate_filename(event_date, event_name=None):
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        name_part = event_name.replace(" ", "-") if event_name else "event"
        if event_date:
            try:
                date_part = datetime.fromisoformat(event_date).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                date_part = event_date[:10] if len(event_date) >= 10 else today
        else:
            date_part = today
        return f"choraufstellung-{date_part}-version-{today}.json"

    def autosave_check(self):
        mw = self._mw
        if not mw.is_modified or not mw.file:
            return
        placed = mw.grid.get_placed_singer_ids()
        data = {
            "version": "1.0",
            "rows": mw.grid.rows,
            "cols": mw.grid.cols,
            "staggered": mw.grid.staggered,
            "singers": [
                {"name": s.name, "voice_group": s.voice_group.value if hasattr(s.voice_group, 'value') else str(s.voice_group),
                 "height": s.height, "singer_id": s.singer_id, "row": s.row, "col": s.col, "affinity": s.affinity}
                for s in mw.singers
            ],
            "placed": list(placed)
        }
        from workers import AutosaveWorker
        worker = AutosaveWorker(mw.storage, data)
        worker.signals.error.connect(lambda msg: print(f"Autosave error: {msg}"))
        mw.threadpool.start(worker)

    def check_recovery(self):
        mw = self._mw
        latest = mw.storage.get_latest_autosave_path()
        if not latest:
            return
        if mw.storage.get_latest_autosave_mtime() <= mw.last_manual_save_mtime:
            return
        r = QMessageBox.question(
            mw, "Wiederherstellen",
            "Es wurde eine automatisch gespeicherte Aufstellung gefunden, die neuer ist als Ihre letzte manuelle Speicherung.\n\n"
            "Möchten Sie die automatisch gespeicherte Version wiederherstellen?\n"
            "(Ihre manuell gespeicherte Version bleibt erhalten.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r != QMessageBox.StandardButton.Yes:
            return
        data = mw.storage.load_formation(latest)
        if data:
            mw._load_formation_data(data)
            mw.file = latest
            mw.is_modified = True

    def export_pdf(self):
        get_data_dir, PDFExportWorker, _, PDFExportDialog, _ = _import_deps()
        if not PDFExportWorker or not PDFExportDialog:
            return
        mw = self._mw
        event_date = os.environ.get("CHOR_EVENT_DATE", "") or mw.event_date or ""
        event_name = os.environ.get("CHOR_EVENT_NAME", "") or mw.event_name or ""
        project_name = os.environ.get("CHOR_PROJECT", "") or mw.project_name or ""

        if event_date:
            try:
                from datetime import datetime
                event_date = datetime.fromisoformat(event_date).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                event_date = event_date[:10] if len(event_date) >= 10 else ""

        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        date_part = event_date if event_date else today
        default_filename = f"choraufstellung-{date_part}-version-{today}.pdf"

        event_info = ""
        if event_name:
            event_info = event_name
        if event_date:
            event_info += f" ({event_date})"
        if project_name:
            event_info = f"{project_name}: {event_info}" if event_info else project_name

        data_dir = get_data_dir()
        workdir = os.path.join(os.path.dirname(data_dir), "workdir")
        os.makedirs(workdir, exist_ok=True)

        dlg = PDFExportDialog(mw, default_filename=default_filename, event_info=event_info)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        settings = dlg.get_settings()
        fp = os.path.join(workdir, settings["filename"])
        if not fp.endswith(".pdf"):
            fp += ".pdf"

        title = "Choraufstellung"
        subtitle = ""
        if event_name:
            subtitle = event_name
        if event_date:
            subtitle += f" - {event_date}"
        if project_name:
            subtitle = f"{project_name}: {subtitle}" if subtitle else project_name

        mw.statusBar().showMessage("PDF wird exportiert...")
        worker = PDFExportWorker(
            mw.pdf, mw.singers, mw.grid.rows, mw.grid.cols, fp,
            title=title, subtitle=subtitle, staggered=mw.grid.staggered,
            orientation=settings["orientation"], color_mode=settings["color_mode"],
            text_rotation=settings["text_rotation"]
        )
        worker.signals.finished.connect(self._on_pdf_done)
        worker.signals.error.connect(self._on_pdf_error)
        mw.threadpool.start(worker)

    def _on_pdf_done(self, success, message):
        mw = self._mw
        mw.statusBar().showMessage("")
        if success:
            QMessageBox.information(mw, "PDF Export", f"PDF exportiert nach:\n{message}")
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(message)))
        else:
            QMessageBox.warning(mw, "Fehler", message)

    def _on_pdf_error(self, error_msg):
        mw = self._mw
        mw.statusBar().showMessage("")
        QMessageBox.critical(mw, "Fehler", f"PDF-Export fehlgeschlagen:\n{error_msg}")

    def run_optimizer(self):
        _, _, OptimizerWorker, _, OptimizerDialog = _import_deps()
        if not OptimizerWorker or not OptimizerDialog:
            return
        mw = self._mw
        d = OptimizerDialog(mw)
        if d.exec() == QDialog.DialogCode.Accepted:
            rules = d.get_selected_rules()
            if rules:
                primary = d.get_primary_rule()
                refinement = d.get_refinement_rules()
                mw.statusBar().showMessage("Optimierung läuft...")
                worker = OptimizerWorker(mw.grid, primary, refinement)
                worker.signals.finished.connect(self._on_optimizer_done)
                worker.signals.error.connect(self._on_optimizer_error)
                mw.threadpool.start(worker)

    def _on_optimizer_done(self, success, message):
        mw = self._mw
        mw.statusBar().showMessage("")
        if success:
            QMessageBox.information(mw, "Optimierung", message)
        else:
            QMessageBox.warning(mw, "Optimierung", message)

    def _on_optimizer_error(self, error_msg):
        mw = self._mw
        mw.statusBar().showMessage("")
        QMessageBox.critical(mw, "Fehler", f"Optimierung fehlgeschlagen:\n{error_msg}")
