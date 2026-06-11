"""Main window for ChorManager."""

import sys
import json
from pathlib import Path
from PyQt6.QtCore import QSize

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMenuBar,
    QMenu,
    QToolBar,
    QLabel,
    QSizePolicy,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QSplitter,
    QStyle,
    QStackedWidget,
    QDialog,
    QDialogButtonBox,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from ..data.database import Database
from ..domain.repository import SingerRepository
from ..backup.service import AutoBackupService
from ..config import (
    load_voice_groups,
    load_fields,
    get_theme,
    set_theme,
    get_last_active_project_id,
    set_last_active_project_id,
)
from ..core.export_service import ExportService
from .export_dialog import ExportDialog
from PyQt6.QtWidgets import QFileDialog


def get_icon(icon_name: str, fallback_pixmap):
    """Load icon from system theme with fallback to Qt standard pixmap.

    Args:
        icon_name: System icon name (e.g., "document-new", "list-add")
        fallback_pixmap: QStyle.StandardPixmap to use if theme icon not found

    Returns:
        QIcon instance
    """
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication

    icon = QIcon.fromTheme(icon_name)
    if icon.isNull():
        style = QApplication.instance().style() if QApplication.instance() else None
        if style:
            icon = style.standardIcon(fallback_pixmap)
    return icon


from .singer_dialog import SingerDialog
from .version_dialog import VersionCheckDialog
from .export_handlers import ExportHandlers
from .menu_builder import create_menu_bar
from .toolbar_builder import update_context_toolbar
from .choraufstellung_launcher import launch_choraufstellung, launch_for_event
from .ui_setup import create_info_bar, create_central_widget


class MainWindow(ExportHandlers, QMainWindow):
    """Main window for ChorManager."""

    def __init__(self, db_path: str = None):
        """Initialize main window.

        Args:
            db_path: Path to database file.
        """
        super().__init__()

        self.db_path = db_path
        self.db = Database(db_path)
        try:
            self.db.connect()
            self.db.create_tables()
        except Exception:
            self.db.close()
            raise

        self.singer_repo = SingerRepository(self.db)
        self.backup_service = AutoBackupService()

        if self.db_path:
            self.backup_service.backup_on_start(self.db_path)

        self._setup_ui()

        # Initialize context toolbar after UI setup
        self._update_context_toolbar(0, None)

        # Initialize info labels
        self._update_info_labels()

        # Apply last active project filter to tabs
        if self.projects_tab.current_project:
            self._on_project_changed()

        # Load last active event
        from ..config import get_last_active_event_id

        last_event_id = get_last_active_event_id()
        if last_event_id:
            event = self.events_tab.event_repo.get_by_id(last_event_id)
            if event:
                self.current_event = event
                self._update_info_labels()
                if hasattr(self, "choraufstellung_tab"):
                    self.choraufstellung_tab.set_event(event)

        saved_theme = get_theme()
        if saved_theme == "dark":
            self._set_dark_theme()

    def _setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("ChorManager")
        self.setGeometry(100, 100, 800, 600)

        self._create_menu_bar()
        self._create_info_bar()
        self._create_tool_bar()
        self._create_central_widget()
        self._create_status_bar()

    def _create_info_bar(self):
        """Create info bar below menu bar."""
        create_info_bar(self)

    def _create_menu_bar(self):
        """Create menu bar."""
        create_menu_bar(self)

    def _create_tool_bar(self):
        """Create toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

    def _create_central_widget(self):
        """Create central widget with sidebar navigation."""
        create_central_widget(self)

    def _switch_view(self, index):
        """Switch content view."""
        titles = [
            "Projektverwaltung",
            "Sängerverwaltung",
            "Besetzungen",
            "Terminverwaltung",
            "Choraufstellung",
            "Repertoire",
        ]
        self.page_title_label.setText(titles[index])
        self.content_stack.setCurrentIndex(index)
        self.nav_projects.setChecked(index == 0)
        self.nav_singers.setChecked(index == 1)
        self.nav_besetzung.setChecked(index == 2)
        self.nav_events.setChecked(index == 3)
        self.nav_formations.setChecked(index == 4)
        self.nav_repertoire.setChecked(index == 5)
        self._emit_selection(index)

    def _emit_selection(self, tab_index):
        """Emit selection signal with current selected item for given tab.

        Args:
            tab_index: Index of tab (0-3)
        """
        selection = None
        if tab_index == 0 and self.projects_tab.current_project:
            selection = self.projects_tab.current_project
        elif tab_index == 1:
            row = self.singers_tab.table.currentRow()
            if row >= 0:
                item = self.singers_tab.table.item(row, 0)
                singer_id = item.data(Qt.ItemDataRole.UserRole)
                selection = (
                    self.singers_tab.singer_repo.get_by_id(singer_id)
                    if singer_id
                    else None
                )
        elif tab_index == 2:  # Besetzung
            row = self.besetzung_tab.table.currentRow()
            if row >= 0:
                besetzungen = self.besetzung_tab.besetzung_repo.get_all()
                selection = besetzungen[row] if row < len(besetzungen) else None
        elif tab_index == 3:  # Events
            row = self.events_tab.table.currentRow()
            if row >= 0:
                item = self.events_tab.table.item(row, 0)
                event_id = item.data(Qt.ItemDataRole.UserRole)
                selection = (
                    self.events_tab.event_repo.get_by_id(event_id) if event_id else None
                )
        elif tab_index == 4:  # Aufstellung
            row = self.choraufstellung_tab.table.currentRow()
            if row >= 0:
                filename = self.choraufstellung_tab.table.item(row, 0).text()
                selection = filename
        elif tab_index == 5:  # Repertoire
            row = self.repertoire_tab.table.currentRow()
            if row >= 0:
                title = self.repertoire_tab.table.item(row, 1).text()
                selection = title

        self._on_selection_changed(tab_index, selection)

    def _on_selection_changed(self, tab_index, selection):
        """Handle selection change from any tab to update context toolbar.

        Args:
            tab_index: Index of the tab (int)
            selection: Selected object (Project/Event/Singer) or None
        """
        self._update_context_toolbar(tab_index, selection)

    def _update_context_toolbar(self, tab_index, selection):
        """Update toolbar actions based on active tab and selection.

        Args:
            tab_index: Index of active tab.
            selection: Selected item object or None.
        """
        update_context_toolbar(self, tab_index, selection)

    def _update_info_labels(self):
        """Update the info labels in the info bar."""
        # Update project info label
        if self.projects_tab.current_project:
            project = self.projects_tab.current_project
            self.project_info_label.setText(f"{project.name}")
        else:
            self.project_info_label.setText("Keines")

        # Update event info label
        if self.current_event:
            event = self.current_event
            self.event_info_label.setText(f"{event.name} ({event.date[:10]})")
        else:
            self.event_info_label.setText("Keiner")

    def _on_project_changed(self):
        """Handle project selection change."""
        project = self.projects_tab.current_project
        self._update_info_labels()
        self.current_project = project

        if project:
            set_last_active_project_id(project.id)

        if hasattr(self, "events_tab"):
            self.events_tab.set_project_filter(project)
        if hasattr(self, "besetzung_tab"):
            self.besetzung_tab.set_project(project)
        if hasattr(self, "choraufstellung_tab"):
            self.choraufstellung_tab.set_project(project)

        self._refresh_tabs()

    def _on_event_selected(self, event):
        """Handle event selection."""
        self.current_event = event
        self._update_info_labels()
        if hasattr(self, "choraufstellung_tab"):
            self.choraufstellung_tab.set_event(event)

        if event:
            self.event_info_label.setText(
                f"<b>Ausgewählter Termin:</b> {event.name} am {event.date[:10]}"
            )
            self.event_info_label.setVisible(True)
        else:
            self.event_info_label.setVisible(False)

    def _on_besetzung_changed(self, besetzung):
        """Handle active besetzung change."""
        if besetzung:
            self.besetzung_info_label.setText(f"<b>{besetzung.name}</b>")
            self.besetzung_info_label.setVisible(True)
        else:
            self.besetzung_info_label.setText("Keine")
            self.besetzung_info_label.setVisible(False)

    def _create_status_bar(self):
        """Create status bar."""
        self.statusBar().showMessage("Bereit")

    def _refresh_tabs(self):
        """Refresh all tabs."""
        if hasattr(self, "projects_tab"):
            self.projects_tab._load_projects()
        if hasattr(self, "singers_tab"):
            self.singers_tab._load_singers()
        if hasattr(self, "besetzung_tab"):
            self.besetzung_tab._load_besetzungen()
        if hasattr(self, "events_tab"):
            self.events_tab._load_events()
        if hasattr(self, "repertoire_tab"):
            self.repertoire_tab._load_repertoire()

    def _add_singer(self):
        """Add new singer."""
        self.singers_tab._add_singer()

    def _edit_singer(self):
        """Edit selected singer."""
        self.singers_tab._edit_singer()

    def _delete_singer(self):
        self.singers_tab._delete_singer()

    def _edit_event(self):
        self.events_tab._edit_event()

    def _delete_event(self):
        self.events_tab._delete_event()

    def _duplicate_event(self):
        self.events_tab._duplicate_event()

    def _manage_availability(self):
        self.events_tab._manage_availability()

    def _open_choraufstellung_for_event(self, event):
        """Open ChorAufstellung with event data via temp file."""
        launch_for_event(self, event)

    def _edit_formation(self):
        self.choraufstellung_tab._edit_formation()

    def _duplicate_formation(self):
        self.choraufstellung_tab._duplicate_formation()

    def _delete_formation(self):
        self.choraufstellung_tab._delete_formation()

    def _new_formation(self):
        self.choraufstellung_tab._new_formation()

    def _set_light_theme(self):
        """Set professional light theme."""
        from pathlib import Path
        theme_file = Path(__file__).parent / "themes" / "light.qss"
        self.setStyleSheet(theme_file.read_text())
        set_theme("light")
        self.statusBar().showMessage("Helles Theme aktiviert")

    def _set_dark_theme(self):
        """Set professional dark theme."""
        from pathlib import Path
        theme_file = Path(__file__).parent / "themes" / "dark.qss"
        self.setStyleSheet(theme_file.read_text())
        set_theme("dark")
        self.statusBar().showMessage("Dunkles Theme aktiviert")

    def _new_event(self):
        """Create a new event."""
        from .dialogs import EventDialog
        from ..domain.repository import EventRepository

        prefilled_project_id = self.current_project.id if self.current_project else None
        dialog = EventDialog(db=self.db, parent=self, prefilled_project_id=prefilled_project_id)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            if not data.get("name"):
                QMessageBox.warning(self, "Fehler", "Name ist erforderlich")
                return

            repo = EventRepository(self.db)
            repo.create(**data)
            if hasattr(self, 'projects_tab'):
                self.projects_tab._load_projects()
            if hasattr(self, 'events_tab'):
                self.events_tab._load_events()

            self.statusBar().showMessage("Termin erstellt")

    def _manage_availability(self):
        """Manage availability for events."""
        self.events_tab._manage_availability()

    def _list_events(self):
        """List all events."""
        from .dialogs import EventDialog
        from ..domain.repository import EventRepository
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox

        repo = EventRepository(self.db)
        events = repo.get_all()

        if not events:
            QMessageBox.information(self, "Termine", "Keine Termine vorhanden")
            return

        # Show events in a simple dialog
        event_text = "Vorhandene Termine:\n\n"
        for event in events:
            event_text += f"- {event.name} ({event.date}) [{event.event_type}]\n"

        QMessageBox.information(self, "Termine", event_text)

    def _export_all_sync(self):
        """Export all sync files to default location."""
        from PyQt6.QtWidgets import QMessageBox
        from ..export.sync import export_all_sync

        try:
            result = export_all_sync(self.db)

            output_text = "Exportierte Dateien:\n\n"
            for export_type, path in result.items():
                output_text += f"{export_type}: {path}\n"

            self.statusBar().showMessage("Alle Sync-Dateien exportiert")
            QMessageBox.information(self, "Sync-Export", output_text)
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Export fehlgeschlagen:\n{str(e)}")

    def _new_projekt(self):
        """Create new project."""
        self.projects_tab._add_project()

    def _edit_project(self):
        """Edit selected project."""
        self.projects_tab._edit_project()

    def _delete_project(self):
        """Delete selected project."""
        self.projects_tab._delete_project()

    def _duplicate_project(self):
        """Duplicate selected project."""
        self.projects_tab._duplicate_project()

    def _save_projekt(self):
        """Save current project."""
        from PyQt6.QtWidgets import QMessageBox

        project = self.projects_tab.current_project
        if project:
            QMessageBox.information(
                self, "Speichern", f"Projekt '{project.name}' ist bereits gespeichert."
            )
        else:
            QMessageBox.warning(self, "Speichern", "Kein Projekt ausgewählt.")

    def _open_projekt(self):
        """Open existing project."""
        self.content_stack.setCurrentIndex(0)
        QMessageBox.information(
            self, "Öffnen", "Bitte wählen Sie ein Projekt aus der Liste aus."
        )

    def _show_config(self):
        """Show configuration dialog."""
        from .dialogs import ConfigDialog

        dialog = ConfigDialog(self.db, self)
        dialog.exec()

    def _show_about(self):
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        import subprocess
        from datetime import datetime

        try:
            from ..config import get_app_dir
            app_dir = str(get_app_dir())
            git_hash = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=7", "--always", "--dirty"],
                cwd=app_dir,
                text=True,
            ).strip()
            commit_date = subprocess.check_output(
                ["git", "log", "-1", "--format=%cd", "--date=short"],
                cwd=app_dir,
                text=True,
            ).strip()
        except Exception:
            git_hash = "dev"
            commit_date = "unbekannt"

        QMessageBox.about(
            self,
            "Über ChorManager",
            f"<h3>ChorManager</h3>"
            f"<p>Desktop-Anwendung zur Verwaltung eines Chors</p>"
            f"<p>Version: {git_hash} ({commit_date})</p>",
        )

    def _show_selbstdarstellung(self):
        """Show selbstdarstellung dialog."""
        from .dialogs import SelbstdarstellungDialog

        dialog = SelbstdarstellungDialog(self.db, self)
        dialog.exec()

    def _open_choraufstellung(self):
        """Open Choraufstellung app with current project/event data."""
        launch_choraufstellung(self)

    def _open_choraufstellung_file(self, filepath: str = None):
        """Open ChorAufstellung app, optionally with a specific file."""
        launch_choraufstellung(self, filepath=filepath)

    def _open_backup_restore(self):
        """Open Backup & Restore dialog."""
        from ..export.backup_service import ApplicationBackupService
        from ..ui.dialogs import BackupRestoreDialog
        from pathlib import Path

        app_root = Path(__file__).parent.parent.parent
        service = ApplicationBackupService(app_root)

        dialog = BackupRestoreDialog(self)
        dialog.service = service
        if dialog.exec():
            if dialog.restored:
                self._reload_after_restore()

    def _reload_after_restore(self):
        """Reload database and all tabs after backup restore."""
        try:
            self.db.close()
            self.db = Database(self.db_path)
            self.db.connect()
            
            self.singer_repo = SingerRepository(self.db)
            
            for tab_attr in ['projects_tab', 'singers_tab', 'besetzung_tab', 'events_tab']:
                if hasattr(self, tab_attr):
                    tab = getattr(self, tab_attr)
                    if hasattr(tab, 'db'):
                        tab.db = self.db
                    if hasattr(tab, 'singer_repo'):
                        tab.singer_repo = self.singer_repo
                    if hasattr(tab, 'project_repo'):
                        from ..domain.repository import ProjectRepository
                        tab.project_repo = ProjectRepository(self.db)
                    if hasattr(tab, 'event_repo'):
                        from ..domain.repository import EventRepository
                        tab.event_repo = EventRepository(self.db)
                    if hasattr(tab, 'besetzung_repo'):
                        from ..domain.repository import BesetzungRepository
                        tab.besetzung_repo = BesetzungRepository(self.db)
            
            if hasattr(self, 'projects_tab'):
                self.projects_tab._load_projects()
            if hasattr(self, 'singers_tab'):
                self.singers_tab._load_singers()
            if hasattr(self, 'events_tab'):
                self.events_tab._load_events()
            if hasattr(self, 'besetzung_tab'):
                self.besetzung_tab._load_besetzungen()
            
            self.statusBar().showMessage("Datenbank nach Backup-Restore neu geladen.", 3000)
        except Exception as e:
            QMessageBox.critical(
                self, "Fehler", f"Fehler beim Neuladen der Datenbank:\n{str(e)}"
            )


    def _get_data_dir(self):
        """Get current data directory."""
        from pathlib import Path
        from ..config import load_app_config

        config = load_app_config()
        return Path(
            config.get("app", {}).get("data_dir", "~/.local/share/chormanager")
        ).expanduser()

    def closeEvent(self, event):
        """Handle window close."""
        if self.db_path:
            self.backup_service.backup_before_save(self.db_path)

        self.db.close()
        event.accept()




    def _check_version(self):
        """Open version check dialog."""
        dialog = VersionCheckDialog(self)
        dialog.exec()

