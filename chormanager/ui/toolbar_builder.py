"""Context toolbar construction for MainWindow."""

from PyQt6.QtGui import QAction
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


def update_context_toolbar(window, tab_index, selection):
    """Update toolbar actions based on active tab and selection.

    Args:
        window: MainWindow instance.
        tab_index: Index of active tab.
        selection: Selected item object or None.
    """
    if not hasattr(window, "context_toolbar"):
        return
    window.context_toolbar.clear()

    builders = {
        0: _build_projects_toolbar,
        1: _build_singers_toolbar,
        2: _build_besetzung_toolbar,
        3: _build_events_toolbar,
        4: _build_formation_toolbar,
        5: _build_repertoire_toolbar,
    }

    builder = builders.get(tab_index)
    if builder:
        builder(window, selection)


def _add_action(toolbar, label, icon_name, fallback, handler):
    action = QAction(label, toolbar.parent())
    action.setIcon(get_icon(icon_name, fallback))
    action.triggered.connect(handler)
    toolbar.addAction(action)
    return action


def _build_projects_toolbar(window, selection):
    tb = window.context_toolbar
    _add_action(tb, "Hinzufügen", "list-add", QStyle.StandardPixmap.SP_FileIcon, window._new_projekt)
    _add_action(tb, "Aktualisieren", "view-refresh", QStyle.StandardPixmap.SP_BrowserReload, window._refresh_tabs)

    if selection:
        _add_action(tb, "Als aktives Projekt setzen", "folder-remote", QStyle.StandardPixmap.SP_DirLinkIcon, window.projects_tab._set_active)
        _add_action(tb, "Bearbeiten", "document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView, window._edit_project)
        _add_action(tb, "Duplizieren", "edit-copy", QStyle.StandardPixmap.SP_FileIcon, window._duplicate_project)
        _add_action(tb, "Löschen", "edit-delete", QStyle.StandardPixmap.SP_TrashIcon, window._delete_project)


def _build_singers_toolbar(window, selection):
    tb = window.context_toolbar
    _add_action(tb, "Hinzufügen", "list-add", QStyle.StandardPixmap.SP_FileIcon, window._add_singer)
    _add_action(tb, "Aktualisieren", "view-refresh", QStyle.StandardPixmap.SP_BrowserReload, window._refresh_tabs)

    if selection:
        _add_action(tb, "Bearbeiten", "document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView, window._edit_singer)
        _add_action(tb, "Löschen", "edit-delete", QStyle.StandardPixmap.SP_TrashIcon, window._delete_singer)


def _build_besetzung_toolbar(window, selection):
    tb = window.context_toolbar
    _add_action(tb, "Neue Besetzung", "list-add", QStyle.StandardPixmap.SP_FileIcon, window.besetzung_tab._new_besetzung)
    _add_action(tb, "Aktualisieren", "view-refresh", QStyle.StandardPixmap.SP_BrowserReload, window._refresh_tabs)

    if selection:
        _add_action(tb, "Bearbeiten", "document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView, window.besetzung_tab._edit_besetzung)
        _add_action(tb, "Als aktiv setzen", "folder-remote", QStyle.StandardPixmap.SP_DirLinkIcon, window.besetzung_tab._set_active_besetzung)
        _add_action(tb, "Löschen", "edit-delete", QStyle.StandardPixmap.SP_TrashIcon, window.besetzung_tab._delete_besetzung)


def _build_events_toolbar(window, selection):
    tb = window.context_toolbar
    _add_action(tb, "Neuer Termin", "list-add", QStyle.StandardPixmap.SP_FileIcon, window._new_event)
    _add_action(tb, "Aktualisieren", "view-refresh", QStyle.StandardPixmap.SP_BrowserReload, window._refresh_tabs)

    if selection:
        _add_action(tb, "Verfügbarkeit erfassen", "view-calendar", QStyle.StandardPixmap.SP_FileIcon, window._manage_availability)

        formation_exists = False
        if hasattr(window, "choraufstellung_tab"):
            formation_exists = window.choraufstellung_tab.has_formation_for_event(selection)

        if formation_exists:
            _add_action(tb, "Aufstellung bearbeiten", "document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView,
                       lambda checked=False, ev=selection: window._open_choraufstellung_for_event(ev))
        else:
            _add_action(tb, "Aufstellung öffnen", "document-open", QStyle.StandardPixmap.SP_DialogOpenButton,
                       lambda checked=False, ev=selection: window._open_choraufstellung_for_event(ev))

        _add_action(tb, "Als aktiven Termin setzen", "x-office-calendar", QStyle.StandardPixmap.SP_FileIcon, window.events_tab._set_selected_event)

        tb.addSeparator()

        _add_action(tb, "Bearbeiten", "document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView, window._edit_event)
        _add_action(tb, "Duplizieren", "edit-copy", QStyle.StandardPixmap.SP_FileIcon, window._duplicate_event)
        _add_action(tb, "Löschen", "edit-delete", QStyle.StandardPixmap.SP_TrashIcon, window._delete_event)


def _build_formation_toolbar(window, selection):
    tb = window.context_toolbar
    _add_action(tb, "Neue Aufstellung", "list-add", QStyle.StandardPixmap.SP_FileIcon, window._new_formation)

    if selection:
        _add_action(tb, "Bearbeiten", "document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView, window._edit_formation)
        _add_action(tb, "Duplizieren", "edit-copy", QStyle.StandardPixmap.SP_FileIcon, window._duplicate_formation)
        _add_action(tb, "Löschen", "edit-delete", QStyle.StandardPixmap.SP_TrashIcon, window._delete_formation)


def _build_repertoire_toolbar(window, selection):
    if not hasattr(window, "repertoire_tab"):
        return
    tb = window.context_toolbar
    _add_action(tb, "Hinzufügen", "list-add", QStyle.StandardPixmap.SP_FileIcon, window.repertoire_tab._add_repertoire)

    if window.repertoire_tab.table.currentRow() >= 0:
        _add_action(tb, "Bearbeiten", "document-edit", QStyle.StandardPixmap.SP_FileDialogDetailedView, window.repertoire_tab._edit_repertoire)
        _add_action(tb, "Löschen", "edit-delete", QStyle.StandardPixmap.SP_TrashIcon, window.repertoire_tab._delete_repertoire)
