"""UI setup helpers for MainWindow."""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSplitter, QStackedWidget, QToolBar, QStyle,
)


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


def create_info_bar(window):
    """Create the info bar below menu bar."""
    from PyQt6.QtWidgets import QStyle

    info_bar = QWidget()
    info_bar.setObjectName("infoBarWidget")
    info_bar.setMinimumHeight(45)
    info_bar.setStyleSheet("""
        QWidget {
            background-color: #e8f4f8;
            border-bottom: 2px solid #4a90d9;
            padding: 5px;
        }
        QLabel {
            font-weight: bold;
            color: #2c3e50;
            padding: 4px 12px;
            border-radius: 4px;
        }
        QLabel#projectInfoLabel {
            background-color: #4a90d9;
            color: white;
        }
        QLabel#eventInfoLabel {
            background-color: #e67e22;
            color: white;
        }
    """)

    info_layout = QHBoxLayout(info_bar)
    info_layout.setContentsMargins(15, 8, 15, 8)
    info_layout.setSpacing(15)

    label = QLabel("Aktives Projekt:")
    label.setStyleSheet("font-weight: normal; color: #666;")
    info_layout.addWidget(label)

    window.project_info_label = QLabel("Keines")
    window.project_info_label.setObjectName("projectInfoLabel")
    window.project_info_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
    info_layout.addWidget(window.project_info_label)

    label = QLabel("Aktive Besetzung:")
    label.setStyleSheet("font-weight: normal; color: #666;")
    info_layout.addWidget(label)

    window.besetzung_info_label = QLabel("Keine")
    window.besetzung_info_label.setObjectName("besetzungInfoLabel")
    window.besetzung_info_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
    info_layout.addWidget(window.besetzung_info_label)

    info_layout.addStretch()

    label = QLabel("Aktiver Termin:")
    label.setStyleSheet("font-weight: normal; color: #666;")
    info_layout.addWidget(label)

    window.event_info_label = QLabel("Keiner")
    window.event_info_label.setObjectName("eventInfoLabel")
    window.event_info_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
    info_layout.addWidget(window.event_info_label)

    info_layout.addStretch()

    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    main_layout.addWidget(window.menuBar())
    main_layout.addWidget(info_bar)

    menu_container = QWidget()
    menu_container.setLayout(main_layout)
    window.setMenuWidget(menu_container)


def create_central_widget(window):
    """Create the central widget with sidebar and content area."""
    central = QWidget()
    window.setCentralWidget(central)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    layout = QHBoxLayout(central)
    layout.addWidget(splitter)
    layout.setContentsMargins(0, 0, 0, 0)

    sidebar = _create_sidebar(window)
    splitter.addWidget(sidebar)

    content_area = _create_content_area(window)
    splitter.addWidget(content_area)
    splitter.setStretchFactor(1, 1)


def _create_sidebar(window):
    """Create the sidebar navigation."""
    sidebar = QWidget()
    sidebar.setMinimumWidth(140)
    sidebar.setMaximumWidth(140)
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(5, 10, 5, 10)
    sidebar_layout.setSpacing(5)

    nav_items = [
        ("Projekte", "folder", 0, "nav_projects"),
        ("Sänger", "user-info", 1, "nav_singers"),
        ("Besetzung", "system-users", 2, "nav_besetzung"),
        ("Termine", "x-office-calendar", 3, "nav_events"),
        ("Aufstellung", "audio-volume-high", 4, "nav_formations"),
        ("Repertoire", "view-list", 5, "nav_repertoire"),
    ]

    for label, icon, index, attr_name in nav_items:
        btn = QPushButton(label)
        btn.setIcon(get_icon(icon, QStyle.StandardPixmap.SP_DirClosedIcon))
        btn.setCheckable(True)
        if index == 0:
            btn.setChecked(True)
        btn.clicked.connect(lambda checked, idx=index: window._switch_view(idx))
        setattr(window, attr_name, btn)
        sidebar_layout.addWidget(btn)

    sidebar_layout.addStretch()
    return sidebar


def _create_content_area(window):
    """Create the content area with title, toolbar, and tab stack."""
    from PyQt6.QtWidgets import QToolBar

    content_area = QWidget()
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(0)

    window.page_title_label = QLabel("Projektverwaltung")
    window.page_title_label.setObjectName("pageTitle")
    content_layout.addWidget(window.page_title_label)

    window.context_toolbar = QToolBar("Aktionen")
    window.context_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    window.context_toolbar.setMovable(False)
    window.context_toolbar.setIconSize(QSize(16, 16))
    content_layout.addWidget(window.context_toolbar)

    window.current_event = None

    from .views.projects_tab import ProjectsTab
    from .views.singers_tab import SingersTab
    from .views.events_tab import EventsTab
    from .views.besetzung_tab import BesetzungTab
    from .views.choraufstellung_tab import ChorAufstellungTab
    from .views.repertoire_tab import RepertoireTab

    window.projects_tab = ProjectsTab(window.db)
    window.projects_tab.current_project_changed.connect(window._on_project_changed)
    window.projects_tab._load_active_project()

    window.singers_tab = SingersTab(window.db)

    window.events_tab = EventsTab(window.db)
    window.events_tab.event_selected.connect(window._on_event_selected)
    window.events_tab._restore_active_event()

    window.besetzung_tab = BesetzungTab(window.db)
    window.besetzung_tab.active_besetzung_changed.connect(window._on_besetzung_changed)
    window.besetzung_tab._restore_active_besetzung()

    window.choraufstellung_tab = ChorAufstellungTab(window.db)

    window.repertoire_tab = RepertoireTab(window.db)

    window.content_stack = QStackedWidget()
    window.content_stack.addWidget(window.projects_tab)
    window.content_stack.addWidget(window.singers_tab)
    window.content_stack.addWidget(window.besetzung_tab)
    window.content_stack.addWidget(window.events_tab)
    window.content_stack.addWidget(window.choraufstellung_tab)
    window.content_stack.addWidget(window.repertoire_tab)

    content_layout.addWidget(window.content_stack)

    window._update_context_toolbar(0, window.projects_tab.current_project)

    window.projects_tab.table.selectionModel().selectionChanged.connect(
        lambda: window._emit_selection(0)
    )
    window.singers_tab.table.selectionModel().selectionChanged.connect(
        lambda: window._emit_selection(1)
    )
    window.besetzung_tab.table.selectionModel().selectionChanged.connect(
        lambda: window._emit_selection(2)
    )
    window.events_tab.table.selectionModel().selectionChanged.connect(
        lambda: window._emit_selection(3)
    )
    window.choraufstellung_tab.table.selectionModel().selectionChanged.connect(
        lambda: window._emit_selection(4)
    )

    return content_area
