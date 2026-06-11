import sys
import os
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QMenuBar, QMenu,
    QFileDialog, QDialog, QFormLayout, QLineEdit, QComboBox, QListWidget,
    QListWidgetItem, QScrollArea, QMessageBox, QFrame, QCheckBox, QSplitter,
    QGraphicsDropShadowEffect, QRubberBand,
    QCompleter, QTableWidget, QTableWidgetItem, QHeaderView,
    QRadioButton
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QRect, QTimer, QPoint, QThreadPool
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QDrag, QColor, QPalette, QFont, QUndoStack, QUndoCommand

try:
    from config import load_settings, save_settings, load_voice_groups_config, get_valid_voice_groups, get_voice_group_color, get_data_dir, clear_color_cache
except ImportError:
    def load_settings(): return {"theme": "standard"}
    def save_settings(s): return True
    def load_voice_groups_config(): return []
    def get_valid_voice_groups(): return []
    def get_voice_group_color(v): return "#cccccc"
    def get_data_dir(): return "."
    def clear_color_cache(): pass

try:
    from singer_model import Singer, VoiceGroup, voice_group_color
    from storage import FormationStorage
    from pdf_export import PDFExporter
    from core.optimizer import FormationOptimizer
    from core.grid_engine import GridEngine, GridConfig
    from ui.optimizer_dialog import OptimizerDialog
    from ui.dialogs import AddSingerDialog, AffinityDialog, VoicingConfigDialog
    from ui.theme_manager import apply_theme, build_legend
    from ui.menu_builder import build_menu
    from services.formation_file_service import FormationFileService
    from services.formation_loader import FormationLoader
except ImportError:
    from enum import Enum
    class VoiceGroup(Enum):
        SOPRAN_1 = "Sopran 1"
    def voice_group_color(vg): return "#cccccc"
    class Singer:
        def __init__(self, name, voice_group, height=0, singer_id="1"):
            self.name, self.voice_group, self.height, self.singer_id = name, voice_group, height, singer_id
    class FormationStorage:
        def load_formation(self, f): return None
        def save_formation(self, *a): return True
    class PDFExporter:
        def export_formation(self, *a): return True
    class FormationOptimizer:
        @staticmethod
        def run(*a): return None
    class OptimizerDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Optimierung nicht verfügbar")
    class GridEngine:
        def __init__(self, *a): pass

from ui.pool_widget import SingerPool, DraggableTableWidget


from ui.grid_widget import FormationGrid, SingerTile

from core.commands import QtMoveSingerCommand as MoveSingerCommand
from core.commands import QtSwapSingersCommand as SwapSingersCommand
from core.commands import QtMoveGroupCommand as MoveGroupCommand


from ui.grid_widget import FormationGrid, SingerTile


class MainWindow(QMainWindow):
    def __init__(self, chormanager_mode=False, project_name=None, event_date=None, event_name=None, db_path=None, event_id=None, event_type=None):
        super().__init__()
        
        self.chormanager_mode = chormanager_mode
        self.project_name = project_name
        self.event_date = event_date
        self.event_name = event_name
        self.db_path = db_path
        self.event_id = event_id
        self.event_type = event_type or ""
        
        self.storage = FormationStorage()
        self.pdf = PDFExporter()
        self.file = None
        self.singers = []
        self.cfg = get_valid_voice_groups()
        
        self.engine = GridEngine(GridConfig(rows=4, cols=5, staggered=False))
        
        self.is_modified = False
        self.last_manual_save_mtime = 0
        self.file_service = FormationFileService(self)
        self.formation_loader = FormationLoader(self)
        self._loaded_metadata = {
            "project": project_name or "",
            "event": event_name or "",
            "event_date": event_date or "",
            "event_type": event_type or ""
        }
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.file_service.autosave_check)
        self.autosave_timer.start(120000)

        self.threadpool = QThreadPool(self)

        self.setup_ui()
        self.resize(1100, 750)
        
        if self.chormanager_mode:
            self.formation_loader.load_from_chormanager()
        else:
            self.file_service.check_recovery()
        
        settings = load_settings()
        current_theme = settings.get("theme", "light")
        apply_theme(self, current_theme)
        
        if current_theme == "dark":
            self.actionDark.setChecked(True)
        else:
            self.actionLight.setChecked(True)

    def setup_ui(self):
        cen=QWidget(); self.setCentralWidget(cen); ml=QHBoxLayout(cen); sp=QSplitter(Qt.Orientation.Horizontal)
        lp=QWidget(); ll=QVBoxLayout(lp); self.pool=SingerPool()
        self.pool.singer_selected.connect(self.add_to_grid); self.pool.singer_added.connect(self.add_to_grid)
        self.pool.singer_edit_requested.connect(self.edit_singer)
        self.pool.place_all_requested.connect(self.place_all_singers)
        ll.addWidget(self.pool); sp.addWidget(lp)
        rp=QWidget(); rl=QVBoxLayout(rp); gh=QHBoxLayout(); gh.addWidget(QLabel("<b>Aufstellung</b>"))
        gc=QHBoxLayout(); gc.addWidget(QLabel("Reihen:")); self.rs=QComboBox()
        for i in range(1,10): self.rs.addItem(str(i)); self.rs.setCurrentText("4")
        self.rs.setMinimumWidth(50)
        self.rs.currentTextChanged.connect(self.upd_grid); gc.addWidget(self.rs)
        gc.addWidget(QLabel("Spalten:")); self.cs=QComboBox()
        for i in range(1,31): self.cs.addItem(str(i)); self.cs.setCurrentText("5")
        self.cs.setMinimumWidth(50)
        self.cs.currentTextChanged.connect(self.upd_grid); gc.addWidget(self.cs)
        self.grid_count_label = QLabel("0 Sänger")
        self.grid_count_label.setStyleSheet("color: #666; font-size: 9pt; margin-left: 10px;")
        gc.addWidget(self.grid_count_label)
        gh.addLayout(gc); gh.addStretch(); rl.addLayout(gh)
        
        raster_layout = QHBoxLayout()
        raster_layout.addWidget(QLabel("Raster:"))
        sc=QScrollArea(); sc.setWidgetResizable(False); self.grid=FormationGrid(4,5)
        self.undo_stack = QUndoStack(self)
        self.grid.set_undo_stack(self.undo_stack)
        self.grid.singer_removed_from_grid.connect(self.on_singer_removed_from_grid); self.grid.singer_edit_requested.connect(self.edit_singer); self.grid.singer_affinity_requested.connect(self.set_singer_affinity)
        self.undo_stack.canUndoChanged.connect(self.update_undo_redo)
        self.undo_stack.canRedoChanged.connect(self.update_undo_redo)
        self.grid.selection_changed.connect(self.update_swap_action)
        sc.setWidget(self.grid); rl.addWidget(sc)
        self.std_radio = QRadioButton("Standard")
        self.std_radio.setChecked(not self.grid.staggered)
        self.std_radio.toggled.connect(self.on_raster_mode_changed)
        raster_layout.addWidget(self.std_radio)
        self.stag_radio = QRadioButton("Versetzt")
        self.stag_radio.setChecked(self.grid.staggered)
        self.stag_radio.toggled.connect(self.on_raster_mode_changed)
        raster_layout.addWidget(self.stag_radio)
        raster_layout.addStretch()
        rl.addLayout(raster_layout)
        sr=QHBoxLayout(); sr.addWidget(QLabel("Suche:")); self.search_input=QLineEdit(); self.search_input.setPlaceholderText("Sänger-Name..."); self.search_input.returnPressed.connect(self.do_quick_search); sr.addWidget(self.search_input); sb=QPushButton("🔍"); sb.setFixedWidth(30); sb.clicked.connect(self.do_quick_search); sr.addWidget(sb); rl.addLayout(sr)
        self.leg=QWidget(); self.llay=QHBoxLayout(self.leg); rl.addWidget(self.leg); build_legend(self.cfg, self.llay)
        sp.addWidget(rp); sp.setSizes([250,800]); ml.addWidget(sp); build_menu(self)
        self.pool.placed_singer_ids = set()
        self.pool.singers = self.singers
        self.pool.update_singers(self.singers, self.pool.placed_singer_ids)

    def add_to_grid(self, singer):
        if not self.grid.place_singer(singer):
            QMessageBox.warning(self, "Fehler", "Keine freie Position im Raster verfügbar.")
        self.update_grid_count()

    def place_all_singers(self):
        placed = 0
        for singer in self.singers:
            if str(singer.singer_id) not in self.grid.get_placed_singer_ids():
                if self.grid.place_singer(singer):
                    placed += 1
                else:
                    break
        self.update_grid_count()
        if placed > 0:
            self.statusBar().showMessage(f"{placed} Sänger platziert", 3000)
        else:
            QMessageBox.information(self, "Info", "Alle Sänger sind bereits platziert oder das Raster ist voll.")

    def update_grid_count(self):
        placed = len(self.grid.get_placed_singer_ids())
        self.grid_count_label.setText(f"{placed} Sänger")
        self.pool.update_placed_singers(self.grid.get_placed_singer_ids())
    
    def _check_grid_capacity(self, new_rows, new_cols):
        """Check if new grid can hold all placed singers. Returns (is_ok, excess_count)."""
        grid_cells = new_rows * new_cols
        placed_count = len(self.grid.singers)
        excess = placed_count - grid_cells
        return (excess <= 0, excess)
    
    def _show_resize_warning(self, excess):
        """Show warning dialog when shrinking grid would lose singers."""
        placed = len(self.grid.singers)
        msg = (f"In das eingestellte Aufstellungsraster passen die {placed} Sänger "
               f"aus der Aufstellung nicht hinein.\n\n"
               f"{excess} überzählige Sänger müssen in den Sängerpool zurückgesetzt werden, "
               f"oder das Aufstellungsraster muss angepasst werden.")
        
        # Create custom message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Raster zu klein")
        msg_box.setText(msg)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        # Create custom buttons
        btn_pool = QPushButton("In Pool zurücksetzen")
        btn_raster = QPushButton("Raster anpassen")
        msg_box.addButton(btn_pool, QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton(btn_raster, QMessageBox.ButtonRole.ActionRole)
        msg_box.setDefaultButton(btn_raster)
        
        # Connect and exec
        msg_box.buttonClicked.connect(lambda: None)  # placeholder
        reply = msg_box.exec()
        
        # Check which button was clicked
        clicked = msg_box.clickedButton()
        if clicked == btn_pool:
            self._reset_excess_to_pool(excess)
            return True
        return False
    
    def _reset_excess_to_pool(self, count):
        """Reset excess singers (newest placed) back to pool."""
        singers_to_remove = self.grid.singers[-count:] if count > 0 else []
        for singer in singers_to_remove:
            singer.row = -1
            singer.col = -1
        # Rebuild placed list
        self.grid.singers = [s for s in self.grid.singers if s.row >= 0]
        self.grid.refresh_grid()
        self.pool.placed_singer_ids = self.grid.get_placed_singer_ids()
        self.pool.update_singers(self.singers, self.pool.placed_singer_ids)
        self.update_grid_count()
        self.is_modified = True

    def upd_grid(self):
        r = int(self.rs.currentText())
        c = int(self.cs.currentText())
        
        # Check capacity before resizing
        is_ok, excess = self._check_grid_capacity(r, c)
        if not is_ok:
            # Show warning - user chooses to cancel or reset excess
            user_proceeds = self._show_resize_warning(excess)
            if not user_proceeds:
                # Revert ComboBox to current grid values
                self.rs.blockSignals(True)
                self.rs.setCurrentText(str(self.grid.rows))
                self.rs.blockSignals(False)
                self.cs.blockSignals(True)
                self.cs.setCurrentText(str(self.grid.cols))
                self.cs.blockSignals(False)
                return
        
        self.grid.set_dimensions(r, c)

    def on_raster_mode_changed(self):
        self.grid.set_staggered(self.stag_radio.isChecked())

    def undo_last_action(self):
        self.undo_stack.undo()

    def redo_last_action(self):
        self.undo_stack.redo()

    def update_undo_redo(self):
        self.undo_action.setEnabled(self.undo_stack.canUndo())
        self.redo_action.setEnabled(self.undo_stack.canRedo())

    def swap_selected_singers(self):
        self.grid.swap_selected_singers()
        self.update_swap_action()

    def update_swap_action(self):
        self.swap_action.setEnabled(len(self.grid.selected_ids) == 2)

    def reset_formation(self):
        """Reset all placed singers back to pool."""
        r = QMessageBox.question(self, "Zurücksetzen", "Aufstellung zurücksetzen?", 
                           QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r != QMessageBox.StandardButton.Yes:
            return
        for s in self.singers:
            s.row = -1
            s.col = -1
        self.grid.refresh_grid()
        self.is_modified = True
        self.update_grid_count()

    def apply_all_affinity_proximity(self):
        processed = set()
        moved = 0
        for singer in self.singers:
            if singer.row < 0 or not singer.affinity:
                continue
            if singer.singer_id in processed:
                continue
            partner = next((s for s in self.singers if s.singer_id == singer.affinity), None)
            if not partner or partner.row < 0:
                continue
            if singer.row != partner.row:
                continue
            if abs(singer.col - partner.col) == 1:
                processed.add(singer.singer_id)
                processed.add(partner.singer_id)
                continue
            if self.grid.apply_affinity_proximity(singer):
                moved += 1
            processed.add(singer.singer_id)
            processed.add(partner.singer_id)
        if moved > 0:
            self.statusBar().showMessage(f"{moved} Singpartner nebeneinander platziert", 3000)
            self.is_modified = True
        else:
            QMessageBox.information(self, "Nähe", "Alle Singpartner sind bereits nebeneinander oder nicht in der gleichen Reihe.")

    def show_cfg(self):
        d = VoicingConfigDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            pass

    def add_singer_via_menu(self):
        s = self.pool.add_dialog()
        if s:
            self.singers.append(s)
            self.is_modified = True

    def edit_singer(self, singer):
        new_singer = self.pool.add_dialog(singer)
        if new_singer:
            idx = next((i for i, s in enumerate(self.singers) if s.singer_id == singer.singer_id), -1)
            if idx >= 0:
                self.singers[idx] = new_singer
            self.is_modified = True

    def set_singer_affinity(self, singer):
        self.pool.set_affinity(singer)

    def on_singer_removed_from_grid(self, singer):
        self.pool.update_singers(self.singers, self.grid.get_placed_singer_ids())
        self.is_modified = True
        self.update_grid_count()

    def do_quick_search(self):
        name = self.search_input.text().strip().lower()
        if not name:
            self.grid.clear_search_highlight()
            return
        for s in self.singers:
            if name in s.name.lower():
                self.grid.highlight_singer(s, self)
                return

    def show_about(self):
        QMessageBox.about(self, "Über Choraufstellung", "Choraufstellung 1.0\n\nVerwaltung von Choraufstellungen.")

    def closeEvent(self, e):
        if self.is_modified:
            r = QMessageBox.question(self, "Ungespeichert", "Änderungen speichern?", QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel)
            if r == QMessageBox.StandardButton.Save:
                self.save_f()
                e.accept()
            elif r == QMessageBox.StandardButton.Discard:
                e.accept()
            else:
                e.ignore()
        else:
            e.accept()



def main():
    import os
    event_date = os.environ.get("CHOR_EVENT_DATE", "")
    event_id = os.environ.get("CHOR_EVENT_ID", "")
    event_name = os.environ.get("CHOR_EVENT_NAME", "")
    project_name = os.environ.get("CHOR_PROJECT", "")
    event_type = os.environ.get("CHOR_EVENT_TYPE", "")
    db_path = os.environ.get("CHOR_DB_PATH", "")
    chor_file = os.environ.get("CHOR_FILE", "")
    chormanager_mode = bool(event_date or event_id or db_path or chor_file)
    
    app = QApplication(sys.argv); app.setStyle("Fusion")
    w = MainWindow(chormanager_mode=chormanager_mode, event_id=event_id, event_date=event_date, 
                  event_name=event_name, project_name=project_name, event_type=event_type)
    
    if chor_file and os.path.exists(chor_file):
        w.file = chor_file
        w.storage.filepath = chor_file
        data = w.storage.load_formation(chor_file)
        if data:
            w.formation_loader.load_formation_data(data)
    
    w.show()
    sys.exit(app.exec())