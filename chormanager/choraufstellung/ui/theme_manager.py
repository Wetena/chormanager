"""Theme management for ChorAufstellung.

Loads QSS stylesheets with inline fallback.
"""

import os

from PyQt6.QtWidgets import QLabel, QVBoxLayout


def _import_config():
    """Lazy import of config functions to avoid circular imports."""
    try:
        from config import get_voice_group_color, clear_color_cache
        return get_voice_group_color, clear_color_cache
    except ImportError:
        def fallback_color(v): return "#cccccc"
        return fallback_color, lambda: None


_DARK_FALLBACK = """
    QMainWindow, QWidget { background: #2b2b2b; color: #F0F0F0; }
    QLabel { color: #F0F0F0; }
    QTableWidget { background: #3b3b3b; color: #F0F0F0; gridline-color: #555; }
    QTableWidget::item:selected { background: #4a4a4a; color: #fff; }
    QHeaderView::section { background: #3b3b3b; color: #F0F0F0; border: 1px solid #555; }
    QLineEdit, QComboBox { background: #3b3b3b; color: #F0F0F0; border: 1px solid #555; }
    QPushButton { background: #4a4a4a; color: #F0F0F0; border: 1px solid #555; padding: 4px; }
    QPushButton:hover { background: #5a5a5a; }
    QMenuBar { background: #3b3b3b; color: #F0F0F0; }
    QMenuBar::item:selected { background: #4a4a4a; }
    QMenu { background: #3b3b3b; color: #F0F0F0; border: 1px solid #555; }
    QMenu::item:selected { background: #4a4a4a; }
    QRadioButton { color: #F0F0F0; }
    QCheckBox { color: #F0F0F0; }
"""

_LIGHT_FALLBACK = """
    QMainWindow, QWidget { background: #f8f4eb; color: #1A1A1A; }
    QLabel { color: #1A1A1A; }
    QTableWidget { background: #ffffff; color: #1A1A1A; gridline-color: #d4c9b8; }
    QTableWidget::item:selected { background: #d4c9b8; color: #1A1A1A; }
    QHeaderView::section { background: #f0ebe0; color: #1A1A1A; border: 1px solid #d4c9b8; }
    QLineEdit, QComboBox { background: #ffffff; color: #1A1A1A; border: 1px solid #d4c9b8; }
    QPushButton { background: #e8e0d4; color: #1A1A1A; border: 1px solid #d4c9b8; padding: 4px; }
    QPushButton:hover { background: #d4c9b8; }
    QMenuBar { background: #f0ebe0; color: #1A1A1A; }
    QMenuBar::item:selected { background: #d4c9b8; }
    QMenu { background: #f0ebe0; color: #1A1A1A; border: 1px solid #d4c9b8; }
    QMenu::item:selected { background: #d4c9b8; }
    QRadioButton { color: #1A1A1A; }
    QCheckBox { color: #1A1A1A; }
"""


def apply_theme(widget, theme):
    """Load QSS file or fallback for the given theme.

    Args:
        widget: The QMainWindow to style.
        theme: 'light' or 'dark'.
    """
    _, clear_color_cache = _import_config()

    qss_path = os.path.join(
        os.path.dirname(__file__), "..", "themes", f"{theme}.qss"
    )
    qss_path = os.path.normpath(qss_path)

    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            widget.setStyleSheet(f.read())
    else:
        widget.setStyleSheet(_DARK_FALLBACK if theme == "dark" else _LIGHT_FALLBACK)

    clear_color_cache()
    widget.grid.refresh_grid()
    widget.pool.update_singers(widget.singers, widget.pool.placed_singer_ids)


def build_legend(voice_groups, layout):
    """Build the voice group color legend into the given layout.

    Args:
        voice_groups: List of voice group dicts or strings.
        layout: A QLayout to add labels to.
    """
    get_voice_group_color, _ = _import_config()

    while layout.count():
        w = layout.takeAt(0).widget()
        if w:
            w.deleteLater()
    for vg in voice_groups:
        if isinstance(vg, dict):
            vg_id = vg.get("id", "")
            vg_color = vg.get("color", "#cccccc")
        else:
            vg_id = vg
            vg_color = get_voice_group_color(vg)
        l = QLabel(vg_id)
        l.setStyleSheet(f"background: {vg_color}; padding: 4px; color: #000;")
        layout.addWidget(l)
    layout.addStretch()
