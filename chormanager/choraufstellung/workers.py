"""Background workers for ChorAufstellung.

QRunnable workers for PDF export, optimization, and autosave
to prevent blocking the Qt event loop.
"""

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal


class WorkerSignals(QObject):
    """Signals for background workers."""
    finished = pyqtSignal(bool, str)  # success, message or filepath
    error = pyqtSignal(str)


class PDFExportWorker(QRunnable):
    """Run PDF export in a background thread."""

    def __init__(self, pdf_exporter, singers, rows, cols, filename,
                 title="Choraufstellung", subtitle="",
                 staggered=False, orientation="landscape",
                 color_mode="color", text_rotation="horizontal"):
        super().__init__()
        self.pdf_exporter = pdf_exporter
        self.singers = singers
        self.rows = rows
        self.cols = cols
        self.filename = filename
        self.title = title
        self.subtitle = subtitle
        self.staggered = staggered
        self.orientation = orientation
        self.color_mode = color_mode
        self.text_rotation = text_rotation
        self.signals = WorkerSignals()

    def run(self):
        try:
            success = self.pdf_exporter.export_formation(
                self.singers, self.rows, self.cols, self.filename,
                title=self.title, subtitle=self.subtitle,
                staggered=self.staggered, orientation=self.orientation,
                color_mode=self.color_mode, text_rotation=self.text_rotation
            )
            if success:
                self.signals.finished.emit(True, self.filename)
            else:
                self.signals.finished.emit(False, "PDF-Export fehlgeschlagen.")
        except Exception as e:
            self.signals.error.emit(str(e))


class OptimizerWorker(QRunnable):
    """Run formation optimization in a background thread."""

    def __init__(self, grid, primary_rule=None, refinement_rules=None):
        super().__init__()
        self.grid = grid
        self.primary_rule = primary_rule
        self.refinement_rules = refinement_rules or []
        self.signals = WorkerSignals()

    def run(self):
        try:
            from core.optimizer import FormationOptimizer
            rule_ids = []
            if self.primary_rule:
                rule_ids.append(self.primary_rule)
            if self.refinement_rules:
                rule_ids.extend(self.refinement_rules)

            if not rule_ids:
                self.signals.finished.emit(False, "Keine Regeln ausgewählt.")
                return

            cmd = FormationOptimizer.run(self.grid, rule_ids)
            if cmd:
                self.signals.finished.emit(True, f"Optimierung abgeschlossen ({cmd.elapsed_ms}ms, {cmd.swap_count} Tausch)")
            else:
                self.signals.finished.emit(True, "Optimierung abgeschlossen")
        except Exception as e:
            self.signals.error.emit(str(e))


class AutosaveWorker(QRunnable):
    """Run autosave in a background thread."""

    def __init__(self, storage, data, max_keep=5):
        super().__init__()
        self.storage = storage
        self.data = data
        self.max_keep = max_keep
        self.signals = WorkerSignals()

    def run(self):
        try:
            success = self.storage.save_autosave(self.data, self.max_keep)
            self.signals.finished.emit(success, "")
        except Exception as e:
            self.signals.error.emit(str(e))
