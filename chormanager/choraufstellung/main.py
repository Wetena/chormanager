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


class SingerTile(QFrame):
    removed = pyqtSignal(object)
    edit_requested = pyqtSignal(object)
    affinity_requested = pyqtSignal(object)
    def __init__(self, singer, parent=None):
        super().__init__(parent)
        self.singer = singer
        self.position = None
        self._selected = False
        self.setFixedSize(120, 60)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self._bg = voice_group_color(singer.voice_group)
        self.setStyleSheet(f"background-color: {self._bg}; border: 1px solid #888; border-radius: 4px;")
        self.setAutoFillBackground(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        lay = QVBoxLayout(self); lay.setContentsMargins(4,2,4,2); lay.setSpacing(0)
        n = QLabel(f"<b>{singer.name}</b>"); n.setAlignment(Qt.AlignmentFlag.AlignCenter); n.setWordWrap(True)
        n.setStyleSheet("background: transparent; color: #000; font-size: 9pt;"); lay.addWidget(n)
        vg = singer.voice_group.value if hasattr(singer.voice_group, 'value') else str(singer.voice_group)
        v = QLabel(vg); v.setAlignment(Qt.AlignmentFlag.AlignCenter); v.setStyleSheet("background: transparent; color: #333; font-size: 8pt;"); lay.addWidget(v)
        if singer.height > 0:
            h = QLabel(f"{singer.height} cm"); h.setAlignment(Qt.AlignmentFlag.AlignCenter); h.setStyleSheet("background: transparent; color: #555; font-size: 7pt;"); lay.addWidget(h)
        btn = QPushButton("×"); btn.setFixedSize(14,14); btn.setStyleSheet("font-size: 10pt; padding: 0; background: transparent; border: none;")
        btn.clicked.connect(self.on_remove); lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setXOffset(2)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 35))
        self.setGraphicsEffect(shadow)
    def show_context_menu(self, pos):
        menu = QMenu(self)
        edit_action = menu.addAction("Bearbeiten")
        affinity_action = menu.addAction("Nähe setzen")
        remove_action = menu.addAction("Entfernen")
        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_action:
            self.edit_requested.emit(self)
        elif action == affinity_action:
            self.affinity_requested.emit(self)
        elif action == remove_action:
            self.on_remove()
    def on_remove(self): self.removed.emit(self)
    def set_selected(self, selected: bool):
        bg = voice_group_color(self.singer.voice_group)
        if selected:
            self.setStyleSheet(
                f"background-color: {bg}; "
                f"border: 3px solid #0066cc; border-radius: 4px;"
            )
        else:
            self.setStyleSheet(
                f"background-color: {bg}; "
                f"border: 1px solid #888; border-radius: 4px;"
            )
        self.style().polish(self)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = e.globalPosition()
            modifiers = QApplication.keyboardModifiers()
            parent_grid = self.parent()
            
            if isinstance(parent_grid, FormationGrid):
                sid = self.singer.singer_id
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    if sid in parent_grid.selected_ids:
                        parent_grid.selected_ids.remove(sid)
                    else:
                        parent_grid.selected_ids.add(sid)
                else:
                    if sid not in parent_grid.selected_ids:
                        parent_grid.selected_ids = {sid}
                
                parent_grid.update_selection_visuals()
                parent_grid.is_group_dragging = False
    
    def dragEnterEvent(self, e):
        e.acceptProposedAction()
    
    def dragMoveEvent(self, e):
        e.acceptProposedAction()
    
    def dropEvent(self, e):
        e.acceptProposedAction()
        parent = self.parent()
        if parent and hasattr(parent, 'dropEvent'):
            parent.dropEvent(e)
    def mouseMoveEvent(self, e):
        if not hasattr(self, '_drag_start_pos'):
            super().mouseMoveEvent(e)
            return
        
        if not (e.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(e)
            return
        
        dist = (e.globalPosition() - self._drag_start_pos).manhattanLength()
        if dist > QApplication.startDragDistance():
            drag = QDrag(self)
            mime = QMimeData()
            
            parent_grid = self.parent()
            if isinstance(parent_grid, FormationGrid) and len(parent_grid.selected_ids) > 1:
                group_ids = list(parent_grid.selected_ids)
                mime.setText(f"singer:{self.singer.singer_id}:group:{','.join(group_ids)}")
            else:
                pos_info = f":pos:{self.position[0]},{self.position[1]}" if self.position else ""
                mime.setText(f"singer:{self.singer.singer_id}{pos_info}")
            
            drag.setMimeData(mime)
            drag.setPixmap(self.grab())
            drag.setHotSpot(QPoint(self.width() // 2, self.height() // 2))
            
            self.hide()
            action = drag.exec(Qt.DropAction.MoveAction)
            self.show()
            
            if hasattr(self, '_drag_start_pos'):
                del self._drag_start_pos
        else:
            super().mouseMoveEvent(e)

from core.commands import QtMoveSingerCommand as MoveSingerCommand
from core.commands import QtSwapSingersCommand as SwapSingersCommand
from core.commands import QtMoveGroupCommand as MoveGroupCommand


class FormationGrid(QWidget):
    singer_removed_from_grid = pyqtSignal(object)
    singer_edit_requested = pyqtSignal(object)
    singer_affinity_requested = pyqtSignal(object)
    selection_changed = pyqtSignal()
    
    CELL_WIDTH = 130
    CELL_HEIGHT = 80
    OFFSET = 65
    MARGIN_LEFT = 80
    MARGIN_TOP = 20
    
    def __init__(self, rows=4, cols=5, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            background: #f8f4eb;
            border: 1px solid #d4c9b8;
        """)
        self.rows = rows
        self.cols = cols
        self.staggered = False
        self.singers = []
        self.tiles = {}
        self.selected_ids = set()
        
        self.rubber_band = None
        self.drag_start_pos = None
        self.is_group_dragging = False
        self.undo_stack = QUndoStack(self)
        self.setAcceptDrops(True)
        self.setMinimumSize(self.cols * self.CELL_WIDTH + self.MARGIN_LEFT + 50, 
                           self.rows * self.CELL_HEIGHT + self.MARGIN_TOP + 50)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_grid_context_menu)
    
    def show_grid_context_menu(self, pos):
        menu = QMenu(self)
        
        if len(self.selected_ids) == 1:
            sid = list(self.selected_ids)[0]
            singer = next((s for s in self.singers if s.singer_id == sid), None)
            if singer and singer.affinity:
                partner = next((s for s in self.singers if s.singer_id == singer.affinity), None)
                if partner and partner.row >= 0 and singer.row >= 0:
                    affinity_action = menu.addAction(f" Nähe: {singer.name} → {partner.name} platzieren")
                    affinity_action.triggered.connect(lambda: self.apply_affinity_proximity(singer))
                    menu.addSeparator()
        
        if len(self.selected_ids) == 2:
            swap_action = menu.addAction("Positionen tauschen")
            swap_action.triggered.connect(self.swap_selected_singers)
            menu.addSeparator()
        
        undo_action = menu.addAction("Rückgängig")
        undo_action.setEnabled(self.undo_stack.canUndo())
        undo_action.triggered.connect(self.undo_stack.undo)
        
        redo_action = menu.addAction("Wiederholen")
        redo_action.setEnabled(self.undo_stack.canRedo())
        redo_action.triggered.connect(self.undo_stack.redo)
        
        menu.exec(self.mapToGlobal(pos))
    
    def set_dimensions(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.setMinimumSize(cols * self.CELL_WIDTH + self.MARGIN_LEFT + 50, 
                           rows * self.CELL_HEIGHT + self.MARGIN_TOP + 50)
        self.refresh_grid()
    
    def set_staggered(self, v):
        self.staggered = v
        self.refresh_grid()
    
    def update_selection_visuals(self):
        for tile in list(self.tiles.values()):
            if isinstance(tile, SingerTile):
                tile.set_selected(tile.singer.singer_id in self.selected_ids)
    
    def highlight_singer(self, singer, parent_window):
        if singer.singer_id not in self.tiles:
            return
        tile = self.tiles[singer.singer_id]
        
        self._search_pulse_count = 0
        self._search_pulse_max = 5
        self._search_pulse_timer = QTimer(self)
        self._search_pulse_timer.timeout.connect(lambda: self._pulse_step(tile, parent_window))
        self._search_pulse_timer.start(200)
    
    def _pulse_step(self, tile, parent_window):
        count = self._search_pulse_count
        if count >= self._search_pulse_max * 2:
            self._search_pulse_timer.stop()
            self._restore_tile_style(tile)
            if parent_window:
                parent_window.search_input.clear()
            return
        
        is_odd = count % 2 == 1
        vg_color = voice_group_color(tile.singer.voice_group)
        
        if is_odd:
            tile.setStyleSheet(f"""
                background-color: #FFD700;
                border: 3px solid #FF8C00;
                border-radius: 4px;
            """)
            self._pulse_bring_to_front(tile)
        else:
            self._restore_tile_style(tile)
        
        self._search_pulse_count += 1
    
    def _restore_tile_style(self, tile):
        tile.setStyleSheet("")
        vg_color = voice_group_color(tile.singer.voice_group)
        tile.set_selected(tile.singer.singer_id in self.selected_ids)
        tile.style().polish(tile)
    
    def _pulse_bring_to_front(self, tile):
        tile.raise_()
        tile.update()
    
    def clear_search_highlight(self):
        if hasattr(self, '_search_pulse_timer') and self._search_pulse_timer:
            self._search_pulse_timer.stop()
        for tile in list(self.tiles.values()):
            if isinstance(tile, SingerTile):
                self._restore_tile_style(tile)
    
    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(e)

        widget = self.childAt(e.pos())
        if isinstance(widget, SingerTile):
            sid = widget.singer.singer_id
            modifiers = QApplication.keyboardModifiers()

            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if sid in self.selected_ids:
                    self.selected_ids.discard(sid)
                else:
                    self.selected_ids.add(sid)
                self.update_selection_visuals()
                self.selection_changed.emit()
                return

            if sid in self.selected_ids and len(self.selected_ids) > 1:
                self.is_group_dragging = True
                self.drag_start_pos = e.pos()
                return

            self.selected_ids.clear()
            self.selected_ids.add(sid)
            self.update_selection_visuals()
            self.selection_changed.emit()
            return

        self.selected_ids.clear()
        self.update_selection_visuals()
        self.selection_changed.emit()

        self.drag_start_pos = e.pos()
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.rubber_band.setGeometry(QRect(self.drag_start_pos, self.drag_start_pos))
        self.rubber_band.show()

    def mouseMoveEvent(self, e):
        if self.rubber_band and self.rubber_band.isVisible():
            rect = QRect(self.drag_start_pos, e.pos()).normalized()
            self.rubber_band.setGeometry(rect)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.rubber_band and self.rubber_band.isVisible():
            rect = self.rubber_band.geometry()
            self.rubber_band.hide()
            self.rubber_band = None

            for tile in list(self.tiles.values()):
                if rect.intersects(tile.geometry()):
                    self.selected_ids.add(tile.singer.singer_id)

            self.update_selection_visuals()
            self.selection_changed.emit()

        self.refresh_grid()
        super().mouseReleaseEvent(e)

    def swap_selected_singers(self):
        if len(self.selected_ids) != 2:
            QMessageBox.warning(self, "Fehler", "Bitte genau zwei Sänger auswählen (Ctrl+Klick).")
            return

        sid1, sid2 = list(self.selected_ids)
        singer1 = next((s for s in self.singers if s.singer_id == sid1), None)
        singer2 = next((s for s in self.singers if s.singer_id == sid2), None)

        if not singer1 or not singer2:
            return

        command = SwapSingersCommand(singer1, singer2, self)
        self.undo_stack.push(command)

        self.selected_ids.clear()
        self.refresh_grid()
    
    def apply_affinity_proximity(self, singer):
        if not singer.affinity:
            return False
        
        partner = next((s for s in self.singers if s.singer_id == singer.affinity), None)
        if not partner or partner.row < 0 or singer.row < 0:
            return False
        
        if singer.row != partner.row:
            return False
        
        if abs(singer.col - partner.col) == 1:
            return False
        
        target_col = singer.col + 1 if singer.col < partner.col else singer.col - 1
        
        if target_col < 0 or target_col >= self.cols:
            return False
        
        occupant = next((s for s in self.singers if s.row == singer.row and s.col == target_col), None)
        
        if occupant and occupant.singer_id != partner.singer_id:
            old_row, old_col = partner.row, partner.col
            partner.row, partner.col = occupant.row, occupant.col
            occupant.row, occupant.col = old_row, old_col
        elif not occupant:
            partner.row, partner.col = singer.row, target_col
        
        self.refresh_grid()
        return True
    
    def refresh_grid(self):
        for tile in list(self.tiles.values()):
            tile.deleteLater()
        self.tiles.clear()
        
        for label in list(self.findChildren(QLabel)):
            if label.text().startswith("Reihe "):
                label.deleteLater()
        
        for cell in list(self.findChildren(QFrame)):
            if hasattr(cell, '_is_grid_cell'):
                cell.deleteLater()
        
        for r in range(self.rows):
            for c in range(self.cols):
                cell = QFrame(self)
                cell._is_grid_cell = True
                x = self.MARGIN_LEFT + c * self.CELL_WIDTH
                if self.staggered and r % 2 == 1:
                    x += self.OFFSET
                y = self.MARGIN_TOP + r * self.CELL_HEIGHT
                cell.setGeometry(x, y, self.CELL_WIDTH - 5, self.CELL_HEIGHT - 5)
                cell.setFrameShape(QFrame.Shape.Panel)
                cell.setFrameShadow(QFrame.Shadow.Sunken)
                cell.setStyleSheet("""
                    background-color: rgba(255,255,255, 0.65);
                    border: 1px solid #d4c9b8;
                    border-radius: 3px;
                """)
                cell.lower()
                cell.show()
        
        for singer in self.singers:
            if singer.row >= 0 and singer.col >= 0:
                tile = SingerTile(singer)
                tile.position = (singer.row, singer.col)
                tile.removed.connect(self.on_tile_removed)
                tile.edit_requested.connect(self.on_tile_edit_requested)
                tile.affinity_requested.connect(self.on_tile_affinity_requested)
                
                x = self.MARGIN_LEFT + singer.col * self.CELL_WIDTH
                if self.staggered and singer.row % 2 == 1:
                    x += self.OFFSET
                y = self.MARGIN_TOP + singer.row * self.CELL_HEIGHT
                
                tile.setParent(self)
                tile.move(x, y)
                tile.show()
                tile.installEventFilter(self)
                self.tiles[singer.singer_id] = tile
        
        self.update_selection_visuals()
        self.update()
        self.updateGeometry()
    
    def place_singer(self, singer):
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.is_occupied(r, c):
                    return self.place_singer_at(singer, r, c)
        return False
    
    def place_singer_at(self, singer, r, c):
        singer.row = r
        singer.col = c
        if singer not in self.singers:
            self.singers.append(singer)
        self.refresh_grid()
        return True
    
    def is_occupied(self, r, c):
        for s in self.singers:
            if s.row == r and s.col == c:
                return True
        return False
    
    def get_singer_at(self, r, c):
        for s in self.singers:
            if s.row == r and s.col == c:
                return s
        return None
    
    def on_tile_removed(self, tile):
        singer = tile.singer
        if singer in self.singers:
            singer.row = -1
            singer.col = -1
            self.singers.remove(singer)
        if singer.singer_id in self.tiles:
            del self.tiles[singer.singer_id]
        tile.deleteLater()
        self.refresh_grid()
        self.singer_removed_from_grid.emit(singer)
    
    def on_tile_edit_requested(self, tile):
        self.singer_edit_requested.emit(tile.singer)
    
    def on_tile_affinity_requested(self, tile):
        self.singer_affinity_requested.emit(tile.singer)
    
    def get_placed_singers(self):
        return [(s, s.row, s.col) for s in self.singers if s.row >= 0]
    
    def get_placed_singer_ids(self):
        return {s.singer_id for s in self.singers if s.row >= 0}
    
    def auto_arrange_by_height(self):
        from core.arrangement import arrange_by_height, apply_placements
        if not self.singers:
            return
        placements = arrange_by_height(self.singers, self.rows, self.cols)
        apply_placements(self.singers, placements)
        self.refresh_grid()
    
    def auto_arrange_men_outer(self):
        from core.arrangement import arrange_men_outer, apply_placements
        if not self.singers:
            return
        placements = arrange_men_outer(self.singers, self.rows, self.cols)
        apply_placements(self.singers, placements)
        self.refresh_grid()
    
    def auto_arrange_satb(self):
        from core.arrangement import arrange_satb, apply_placements
        if not self.singers:
            return
        placements = arrange_satb(self.singers, self.rows, self.cols)
        apply_placements(self.singers, placements)
        self.refresh_grid()
    
    def auto_arrange_sbta(self):
        from core.arrangement import arrange_sbta, apply_placements
        if not self.singers:
            return
        placements = arrange_sbta(self.singers, self.rows, self.cols)
        apply_placements(self.singers, placements)
        self.refresh_grid()
    
    def auto_arrange_s1s2b2b1t2t1a2a1(self):
        from core.arrangement import arrange_s1s2b2b1t2t1a2a1, apply_placements
        if not self.singers:
            return
        placements = arrange_s1s2b2b1t2t1a2a1(self.singers, self.rows, self.cols)
        apply_placements(self.singers, placements)
        self.refresh_grid()

    def auto_arrange_s1s2a1a2t1t2b1b2(self):
        from core.arrangement import arrange_s1s2a1a2t1t2b1b2, apply_placements
        if not self.singers:
            return
        placements = arrange_s1s2a1a2t1t2b1b2(self.singers, self.rows, self.cols)
        apply_placements(self.singers, placements)
        self.refresh_grid()

    def auto_arrange_s1s2b1b2t1t2a1a2(self):
        from core.arrangement import arrange_s1s2b1b2t1t2a1a2, apply_placements
        if not self.singers:
            return
        placements = arrange_s1s2b1b2t1t2a1a2(self.singers, self.rows, self.cols)
        apply_placements(self.singers, placements)
        self.refresh_grid()
    
    def optimize(self, primary_rule=None, refinement_rules=None):
        rule_ids = []
        if primary_rule:
            rule_ids.append(primary_rule)
        if refinement_rules:
            rule_ids.extend(refinement_rules)
        
        if not rule_ids:
            return
        
        try:
            from core.optimizer import FormationOptimizer
            FormationOptimizer.run(self, rule_ids)
        except Exception as e:
            print(f"Optimization error: {e}")
    
    def dragMoveEvent(self, e):
        e.acceptProposedAction()
    
    def dragEnterEvent(self, e):
        e.acceptProposedAction()
    
    def dropEvent(self, e):
        e.acceptProposedAction()
        txt = e.mimeData().text()
        if not txt.startswith("singer:"):
            return

        is_group_move = ":group:" in txt
        sid = txt.split(":group:")[0].replace("singer:", "") if is_group_move else txt.replace("singer:", "")
        if ":pos:" in sid:
            sid = sid.split(":pos:")[0]

        dragged_singer = next((s for s in self.singers if s.singer_id == sid), None)
        if not dragged_singer:
            self.refresh_grid()
            return

        pos = e.position()
        row = int((pos.y() - self.MARGIN_TOP) / self.CELL_HEIGHT)
        col_offset = self.OFFSET if (self.staggered and row % 2 == 1) else 0
        col = int((pos.x() - self.MARGIN_LEFT - col_offset) / self.CELL_WIDTH)

        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            self.refresh_grid()
            return

        if is_group_move:
            group_ids = txt.split(":group:")[1].split(",")
            delta_row = row - dragged_singer.row
            delta_col = col - dragged_singer.col

            if delta_row == 0 and delta_col == 0:
                self.refresh_grid()
                return

            can_move = True
            for gid in group_ids:
                singer = next((s for s in self.singers if s.singer_id == gid), None)
                if singer is None:
                    can_move = False
                    break
                new_row = (singer.row or 0) + delta_row
                new_col = (singer.col or 0) + delta_col
                if new_row < 0 or new_row >= self.rows or new_col < 0 or new_col >= self.cols:
                    can_move = False
                    break
            
            if not can_move:
                QMessageBox.warning(self, "Rand erreicht", "Die Gruppe würde teilweise außerhalb des Rasters landen.")
                self.refresh_grid()
                return

            command = MoveGroupCommand(group_ids, delta_col, delta_row, self)
            self.undo_stack.push(command)

            self.selected_ids.clear()

        else:
            old_row = dragged_singer.row
            old_col = dragged_singer.col
            for s in self.singers:
                if s != dragged_singer and s.row == row and s.col == col:
                    if old_row >= 0:
                        s.row, s.col = old_row, old_col
                    else:
                        return
                    break

            dragged_singer.row = row
            dragged_singer.col = col

            if dragged_singer.row != old_row or dragged_singer.col != old_col:
                command = MoveSingerCommand(dragged_singer, old_row, old_col,
                                            dragged_singer.row, dragged_singer.col, self)
                self.undo_stack.push(command)

        self.refresh_grid()



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
        self.grid.singer_removed_from_grid.connect(self.on_singer_removed_from_grid); self.grid.singer_edit_requested.connect(self.edit_singer); self.grid.singer_affinity_requested.connect(self.set_singer_affinity)
        self.grid.undo_stack.canUndoChanged.connect(self.update_undo_redo)
        self.grid.undo_stack.canRedoChanged.connect(self.update_undo_redo)
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
        self.grid.undo_stack.undo()

    def redo_last_action(self):
        self.grid.undo_stack.redo()

    def update_undo_redo(self):
        self.undo_action.setEnabled(self.grid.undo_stack.canUndo())
        self.redo_action.setEnabled(self.grid.undo_stack.canRedo())

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