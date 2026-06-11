"""Menu bar builder for ChorAufstellung.

Extracts the ~80-line menu() method from main.py into a standalone function.
"""

from PyQt6.QtGui import QAction, QActionGroup


def _import_theme():
    """Lazy import of theme functions to avoid circular imports."""
    try:
        from ui.theme_manager import apply_theme
        return apply_theme
    except ImportError:
        return lambda w, t: None


def build_menu(main_window):
    """Build the full menu bar on main_window.

    Sets up main_window.swap_action, undo_action, redo_action, theme_group,
    actionLight, actionDark for later programmatic access.
    """
    apply_theme = _import_theme()
    m = main_window.menuBar()

    # Datei
    f = m.addMenu("Datei")
    f.addAction(QAction("Neu", main_window, shortcut="Ctrl+N", triggered=main_window.file_service.new_file))
    f.addAction(QAction("Öffnen...", main_window, shortcut="Ctrl+O", triggered=main_window.file_service.open_file))
    f.addAction(QAction("Speichern", main_window, shortcut="Ctrl+S", triggered=main_window.file_service.save_file))
    f.addAction(QAction("Speichern unter...", main_window, shortcut="Ctrl+Shift+S", triggered=main_window.file_service.save_as_file))
    f.addSeparator()
    f.addAction(QAction("PDF Export...", main_window, shortcut="Ctrl+E", triggered=main_window.file_service.export_pdf))
    f.addSeparator()
    f.addAction(QAction("Beenden", main_window, shortcut="Ctrl+Q", triggered=main_window.close))

    # Bearbeiten
    e = m.addMenu("Bearbeiten")
    e.addAction(QAction("Sänger hinzufügen", main_window, shortcut="Ctrl+Shift+A", triggered=main_window.add_singer_via_menu))
    main_window.swap_action = QAction("Positionen tauschen", main_window, shortcut="Ctrl+T", triggered=main_window.swap_selected_singers)
    main_window.swap_action.setEnabled(False)
    e.addAction(main_window.swap_action)
    main_window.undo_action = QAction("Rückgängig", main_window, shortcut="Ctrl+Z", triggered=main_window.undo_last_action)
    main_window.redo_action = QAction("Wiederholen", main_window, shortcut="Ctrl+Y", triggered=main_window.redo_last_action)
    main_window.undo_action.setEnabled(False)
    main_window.redo_action.setEnabled(False)
    e.addAction(main_window.undo_action)
    e.addAction(main_window.redo_action)

    # Aufstellen
    a = m.addMenu("Aufstellen")
    size_action = QAction("Aufstellung nach Größe", main_window)
    size_action.triggered.connect(main_window.grid.auto_arrange_by_height)
    a.addAction(size_action)
    men_action = QAction("Männer geteilt außen", main_window)
    men_action.triggered.connect(main_window.grid.auto_arrange_men_outer)
    a.addAction(men_action)
    satb_action = QAction("SATB", main_window)
    satb_action.triggered.connect(main_window.grid.auto_arrange_satb)
    a.addAction(satb_action)
    sbta_action = QAction("SBTA", main_window)
    sbta_action.triggered.connect(main_window.grid.auto_arrange_sbta)
    a.addAction(sbta_action)
    s1s2_action = QAction("S1 S2 B2 B1 T2 T1 A2 A1", main_window)
    s1s2_action.triggered.connect(main_window.grid.auto_arrange_s1s2b2b1t2t1a2a1)
    a.addAction(s1s2_action)
    s1s2a1a2_action = QAction("S1 S2 A1 A2 T1 T2 B1 B2", main_window)
    s1s2a1a2_action.triggered.connect(main_window.grid.auto_arrange_s1s2a1a2t1t2b1b2)
    a.addAction(s1s2a1a2_action)
    s1s2b1b2_action = QAction("S1 S2 B1 B2 T1 T2 A1 A2", main_window)
    s1s2b1b2_action.triggered.connect(main_window.grid.auto_arrange_s1s2b1b2t1t2a1a2)
    a.addAction(s1s2b1b2_action)
    a.addSeparator()
    affinity_action = QAction("Nähe (Singpartner)", main_window)
    affinity_action.triggered.connect(main_window.apply_all_affinity_proximity)
    a.addAction(affinity_action)
    a.addSeparator()
    reset_action = QAction("Aufstellung zurücksetzen", main_window)
    reset_action.triggered.connect(main_window.reset_formation)
    a.addAction(reset_action)
    a.addSeparator()
    opt_action = QAction("Optimiert aufstellen...", main_window)
    opt_action.triggered.connect(main_window.file_service.run_optimizer)
    a.addAction(opt_action)

    # Konfigurieren
    k = m.addMenu("Konfigurieren")
    cfg_action = QAction("Besetzung konfigurieren...", main_window)
    cfg_action.setEnabled(True)
    cfg_action.triggered.connect(main_window.show_cfg)
    k.addAction(cfg_action)

    # Ansicht (Themen)
    v = m.addMenu("&Ansicht")
    main_window.theme_group = QActionGroup(main_window)
    main_window.theme_group.setExclusive(True)
    main_window.actionLight = QAction("Light", main_window)
    main_window.actionLight.setCheckable(True)
    main_window.actionLight.triggered.connect(lambda: apply_theme(main_window, "light"))
    v.addAction(main_window.actionLight)
    main_window.theme_group.addAction(main_window.actionLight)
    main_window.actionDark = QAction("Dark", main_window)
    main_window.actionDark.setCheckable(True)
    main_window.actionDark.triggered.connect(lambda: apply_theme(main_window, "dark"))
    v.addAction(main_window.actionDark)
    main_window.theme_group.addAction(main_window.actionDark)

    # Hilfe
    h = m.addMenu("&Hilfe")
    h.addAction(QAction("Über", main_window, triggered=main_window.show_about))
