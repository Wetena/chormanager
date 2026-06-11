"""Menu bar construction for MainWindow."""

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QStyle


def get_icon(icon_name: str, fallback_pixmap):
    """Load icon from system theme with fallback."""
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication

    icon = QIcon.fromTheme(icon_name)
    if icon.isNull():
        style = QApplication.instance().style() if QApplication.instance() else None
        if style:
            icon = style.standardIcon(fallback_pixmap)
    return icon


def create_menu_bar(window):
    """Create the complete menu bar for the main window.

    Args:
        window: MainWindow instance to connect actions to.
    """
    menubar = window.menuBar()

    _create_file_menu(menubar, window)
    _create_projekt_menu(menubar, window)
    _create_saenger_menu(menubar, window)
    _create_besetzung_menu(menubar, window)
    _create_termin_menu(menubar, window)
    _create_aufstellung_menu(menubar, window)
    _create_repertoire_menu(menubar, window)
    _create_view_menu(menubar, window)
    _create_konfig_menu(menubar, window)
    _create_marketing_menu(menubar, window)
    _create_hilfe_menu(menubar, window)


def _create_file_menu(menubar, window):
    menu = menubar.addMenu("&Datei")
    menu.addSeparator()

    action = QAction("Backup & Restore...", window)
    action.setIcon(get_icon("media-floppy", QStyle.StandardPixmap.SP_DriveFDIcon))
    action.triggered.connect(window._open_backup_restore)
    menu.addAction(action)

    action = QAction("Beenden", window)
    action.setIcon(get_icon("application-exit", QStyle.StandardPixmap.SP_DialogCloseButton))
    action.setShortcut(QKeySequence.StandardKey.Quit)
    action.triggered.connect(window.close)
    menu.addAction(action)


def _create_projekt_menu(menubar, window):
    menu = menubar.addMenu("&Projekt")

    action = QAction("Neu...", window)
    action.setIcon(get_icon("document-new", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._new_projekt)
    menu.addAction(action)

    action = QAction("Speichern", window)
    action.setIcon(get_icon("document-save", QStyle.StandardPixmap.SP_DialogSaveButton))
    action.triggered.connect(window._save_projekt)
    menu.addAction(action)

    action = QAction("Öffnen...", window)
    action.setIcon(get_icon("document-open", QStyle.StandardPixmap.SP_DialogOpenButton))
    action.triggered.connect(window._open_projekt)
    menu.addAction(action)

    action = QAction("Bearbeiten...", window)
    action.setIcon(get_icon("document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView))
    action.triggered.connect(window._edit_project)
    menu.addAction(action)

    action = QAction("Löschen", window)
    action.setIcon(get_icon("edit-delete", QStyle.StandardPixmap.SP_TrashIcon))
    action.triggered.connect(window._delete_project)
    menu.addAction(action)

    menu.addSeparator()

    export_menu = menu.addMenu("Export")

    action = QAction("LibreOffice exportieren...", window)
    action.setIcon(get_icon("x-office-document", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._export_project_libreoffice)
    export_menu.addAction(action)

    action = QAction("CSV exportieren...", window)
    action.setIcon(get_icon("x-office-spreadsheet", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._export_project_csv)
    export_menu.addAction(action)


def _create_saenger_menu(menubar, window):
    menu = menubar.addMenu("Sänger")

    action = QAction("Hinzufügen...", window)
    action.setIcon(get_icon("list-add", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(lambda: window.singers_tab._add_singer() if hasattr(window, "singers_tab") else None)
    menu.addAction(action)

    action = QAction("Bearbeiten...", window)
    action.setIcon(get_icon("document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView))
    action.triggered.connect(lambda: window.singers_tab._edit_singer() if hasattr(window, "singers_tab") else None)
    menu.addAction(action)

    action = QAction("Löschen", window)
    action.setIcon(get_icon("edit-delete", QStyle.StandardPixmap.SP_TrashIcon))
    action.triggered.connect(lambda: window.singers_tab._delete_singer() if hasattr(window, "singers_tab") else None)
    menu.addAction(action)

    menu.addSeparator()

    export_menu = menu.addMenu("Export")
    action = QAction("LibreOffice exportieren...", window)
    action.triggered.connect(lambda: window._export_tab(1))
    export_menu.addAction(action)
    action = QAction("CSV exportieren...", window)
    action.triggered.connect(lambda: window._export_tab_csv(1))
    export_menu.addAction(action)


def _create_besetzung_menu(menubar, window):
    menu = menubar.addMenu("Besetzung")

    action = QAction("Hinzufügen...", window)
    action.setIcon(get_icon("list-add", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(lambda: window.besetzung_tab._new_besetzung() if hasattr(window, "besetzung_tab") else None)
    menu.addAction(action)

    action = QAction("Bearbeiten...", window)
    action.setIcon(get_icon("document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView))
    action.triggered.connect(lambda: window.besetzung_tab._edit_besetzung() if hasattr(window, "besetzung_tab") else None)
    menu.addAction(action)

    action = QAction("Löschen", window)
    action.setIcon(get_icon("edit-delete", QStyle.StandardPixmap.SP_TrashIcon))
    action.triggered.connect(lambda: window.besetzung_tab._delete_besetzung() if hasattr(window, "besetzung_tab") else None)
    menu.addAction(action)

    menu.addSeparator()

    export_menu = menu.addMenu("Export")
    action = QAction("LibreOffice exportieren...", window)
    action.triggered.connect(window._export_besetzung)
    export_menu.addAction(action)
    action = QAction("CSV exportieren...", window)
    action.triggered.connect(window._export_besetzung)
    export_menu.addAction(action)


def _create_termin_menu(menubar, window):
    menu = menubar.addMenu("&Termine")

    action = QAction("Neuer Termin...", window)
    action.setIcon(get_icon("list-add", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._new_event)
    menu.addAction(action)

    action = QAction("Bearbeiten...", window)
    action.setIcon(get_icon("document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView))
    action.triggered.connect(window._edit_event)
    menu.addAction(action)

    action = QAction("Löschen", window)
    action.setIcon(get_icon("edit-delete", QStyle.StandardPixmap.SP_TrashIcon))
    action.triggered.connect(window._delete_event)
    menu.addAction(action)

    menu.addSeparator()

    action = QAction("Verfügbarkeit verwalten...", window)
    action.setIcon(get_icon("view-calendar", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._manage_availability)
    menu.addAction(action)

    menu.addSeparator()

    action = QAction("Terminliste anzeigen...", window)
    action.setIcon(get_icon("x-office-spreadsheet", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._list_events)
    menu.addAction(action)

    menu.addSeparator()
    export_menu = menu.addMenu("Export")
    action = QAction("LibreOffice exportieren...", window)
    action.triggered.connect(window._export_termine)
    export_menu.addAction(action)
    action = QAction("CSV exportieren...", window)
    action.triggered.connect(window._export_termine)
    export_menu.addAction(action)


def _create_aufstellung_menu(menubar, window):
    menu = menubar.addMenu("Aufstellung")

    action = QAction("In Aufstellung öffnen...", window)
    action.setIcon(get_icon("media-playback-start", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._open_choraufstellung)
    menu.addAction(action)

    menu.addSeparator()
    export_menu = menu.addMenu("Export")
    action = QAction("LibreOffice exportieren...", window)
    action.triggered.connect(window._export_aufstellung)
    export_menu.addAction(action)
    action = QAction("CSV exportieren...", window)
    action.triggered.connect(window._export_aufstellung)
    export_menu.addAction(action)


def _create_repertoire_menu(menubar, window):
    menu = menubar.addMenu("Repertoire")

    action = QAction("Hinzufügen...", window)
    action.setIcon(get_icon("list-add", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(lambda: window.repertoire_tab._add_repertoire() if hasattr(window, "repertoire_tab") else None)
    menu.addAction(action)

    action = QAction("Bearbeiten...", window)
    action.setIcon(get_icon("document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView))
    action.triggered.connect(lambda: window.repertoire_tab._edit_repertoire() if hasattr(window, "repertoire_tab") else None)
    menu.addAction(action)

    action = QAction("Löschen", window)
    action.setIcon(get_icon("edit-delete", QStyle.StandardPixmap.SP_TrashIcon))
    action.triggered.connect(lambda: window.repertoire_tab._delete_repertoire() if hasattr(window, "repertoire_tab") else None)
    menu.addAction(action)


def _create_view_menu(menubar, window):
    menu = menubar.addMenu("&Ansicht")

    action = QAction("Hell", window)
    action.setIcon(get_icon("weather-clear", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._set_light_theme)
    menu.addAction(action)

    action = QAction("Dunkel", window)
    action.setIcon(get_icon("weather-night", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._set_dark_theme)
    menu.addAction(action)


def _create_konfig_menu(menubar, window):
    menu = menubar.addMenu("Konfiguration")

    action = QAction("Einstellungen...", window)
    action.setIcon(get_icon("preferences-system", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._show_config)
    menu.addAction(action)


def _create_marketing_menu(menubar, window):
    menu = menubar.addMenu("Marketing")

    action = QAction("Selbstdarstellung...", window)
    action.setIcon(get_icon("x-office-document", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._show_selbstdarstellung)
    menu.addAction(action)


def _create_hilfe_menu(menubar, window):
    menu = menubar.addMenu("&Hilfe")

    action = QAction("Version prüfen", window)
    action.setIcon(get_icon("system-software-update", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._check_version)
    menu.addAction(action)

    menu.addSeparator()

    action = QAction("Über", window)
    action.setIcon(get_icon("help-about", QStyle.StandardPixmap.SP_FileIcon))
    action.triggered.connect(window._show_about)
    menu.addAction(action)
