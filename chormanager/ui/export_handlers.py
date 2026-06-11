"""Export handlers for MainWindow."""

import json
import os
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from ..core.export_service import ExportService
from ..ui.export_dialog import ExportDialog


class ExportHandlers:
    """Mixin class providing export functionality for MainWindow."""

    def _get_export_config_for_current_tab(self):
        tab_index = self.content_stack.currentIndex()
        tab_map = {0: 'projekte', 1: 'saenger', 2: 'besetzung', 3: 'termine'}
        tab_key = tab_map.get(tab_index)
        if tab_key and tab_key in self._TAB_EXPORT_CONFIG:
            return self._TAB_EXPORT_CONFIG[tab_key]
        return None

    def _export_tab_generic(self):
        config = self._get_export_config_for_current_tab()
        if not config:
            QMessageBox.warning(self, 'Export', 'Export für diesen Tab nicht verfügbar.')
            return

        table_name, tab_attr, repo_attr, display_name = config
        repo = getattr(getattr(self, tab_attr), repo_attr)
        service = ExportService()

        fields = service.get_table_fields(self.db.get_connection(), table_name)
        if not fields:
            QMessageBox.warning(self, 'Warnung', f'Keine Felder für Tabelle {table_name} gefunden.')
            return

        dialog = ExportDialog(fields, self)
        if not dialog.exec():
            return

        selected_fields = dialog.get_selected_fields()
        fmt = dialog.get_export_format()

        if not selected_fields:
            QMessageBox.warning(self, 'Warnung', 'Keine Felder ausgewählt.')
            return

        items = repo.get_all()
        data = service.get_export_data(items, selected_fields)

        content, ext_filter = self._format_export(data, selected_fields, fmt)

        tab_name_map = {'Projekte': 'projekte', 'Sänger': 'saenger', 'Besetzungen': 'besetzungen', 'Termine': 'termine'}
        ext_map = {'writer': 'odt', 'calc': 'ods', 'csv': 'csv'}
        tab_file = tab_name_map.get(display_name, display_name.lower())
        ext = ext_map.get(fmt, 'csv')
        today = datetime.now().strftime('%Y-%m-%d')
        default_name = f'{today}-{tab_file}.{ext}'
        workdir = Path(__file__).parent.parent.parent / 'workdir'
        workdir.mkdir(exist_ok=True)
        default_path = str(workdir / default_name)

        filename, _ = QFileDialog.getSaveFileName(
            self, f'{display_name} exportieren',
            default_path, ext_filter
        )
        if not filename:
            return

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        self.statusBar().showMessage(f'{display_name} exportiert ({fmt.upper()})')

    def _format_export(self, data, fields, fmt):
        service = ExportService()
        if fmt == 'writer':
            return service.export_to_libreoffice_writer(data, fields), 'LibreOffice Writer (*.odt)'
        elif fmt == 'calc':
            return service.export_to_libreoffice_calc(data, fields), 'LibreOffice Calc (*.ods)'
        else:
            return service.export_to_csv(data, fields), 'CSV (*.csv)'

    def _export_project_libreoffice(self):
        self.content_stack.setCurrentIndex(0)
        self._export_tab_generic()

    def _export_project_csv(self):
        self.content_stack.setCurrentIndex(0)
        self._export_tab_generic()

    def _export_tab(self, tab_index):
        self.content_stack.setCurrentIndex(tab_index)
        self._export_tab_generic()

    def _export_tab_csv(self, tab_index):
        self.content_stack.setCurrentIndex(tab_index)
        self._export_tab_generic()

    def _export_besetzung(self):
        besetzung_fields = [
            {'name': 'name', 'label': 'Name'},
            {'name': 'project', 'label': 'Projekt'},
            {'name': 'singer_count', 'label': 'Anzahl Sänger'},
            {'name': 'updated_at', 'label': 'Zuletzt gespeichert'},
        ]

        dialog = ExportDialog(besetzung_fields, self)
        if not dialog.exec():
            return

        selected = dialog.get_selected_fields()
        fmt = dialog.get_export_format()

        if not selected:
            QMessageBox.warning(self, 'Warnung', 'Keine Felder ausgewählt.')
            return

        service = ExportService()
        besetzungen = self.besetzung_tab.besetzung_repo.get_all()

        data = []
        for b in besetzungen:
            row = {}
            if 'name' in selected:
                row['name'] = b.name
            if 'project' in selected:
                proj = self.besetzung_tab.project_repo.get_by_id(b.project_id)
                row['project'] = proj.name if proj else '-'
            if 'singer_count' in selected:
                singer_ids = b.get_singer_ids()
                row['singer_count'] = len(singer_ids) if singer_ids else 0
            if 'updated_at' in selected:
                try:
                    dt = datetime.fromisoformat(b.updated_at)
                    row['updated_at'] = dt.strftime('%d.%m.%Y %H:%M')
                except (ValueError, OSError):
                    row['updated_at'] = '-'
            data.append(row)

        content, ext_filter = self._format_export(data, selected, fmt)

        today = datetime.now().strftime('%Y-%m-%d')
        workdir = Path(__file__).parent.parent / 'workdir'
        workdir.mkdir(exist_ok=True)
        ext_map = {'writer': 'odt', 'calc': 'ods', 'csv': 'csv'}
        ext = ext_map.get(fmt, 'csv')
        default_path = str(workdir / f'{today}-besetzungen.{ext}')

        filename, _ = QFileDialog.getSaveFileName(
            self, 'Besetzungen exportieren',
            default_path, ext_filter
        )
        if not filename:
            return

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        self.statusBar().showMessage(f'Besetzungen exportiert ({fmt.upper()})')

    def _export_termine(self):
        termin_fields = [
            {'name': 'date', 'label': 'Datum'},
            {'name': 'name', 'label': 'Name'},
            {'name': 'type', 'label': 'Typ'},
            {'name': 'project', 'label': 'Projekt'},
            {'name': 'yes_count', 'label': 'Verbindl. Zusagen'},
            {'name': 'conditional_count', 'label': 'Vorbehalt'},
        ]

        dialog = ExportDialog(termin_fields, self)
        if not dialog.exec():
            return

        selected = dialog.get_selected_fields()
        fmt = dialog.get_export_format()

        if not selected:
            QMessageBox.warning(self, 'Warnung', 'Keine Felder ausgewählt.')
            return

        service = ExportService()
        events = self.events_tab.event_repo.get_all()

        event_type_labels = {
            'gp': 'GP', 'op': 'OP', 'sofa': 'SOFA',
            'probe': 'Probe', 'konzert': 'Konzert',
            'auftritt': 'Auftritt', 'sonstiges': 'Sonstiges',
        }

        data = []
        for e in events:
            row = {}
            if 'date' in selected:
                try:
                    if e.date and len(e.date) >= 10:
                        dt = datetime.strptime(e.date[:10], '%Y-%m-%d')
                        row['date'] = dt.strftime('%d.%m.%Y')
                    else:
                        row['date'] = e.date or '-'
                except Exception:
                    row['date'] = e.date[:10] if e.date else '-'
            if 'name' in selected:
                row['name'] = e.name or ''
            if 'type' in selected:
                row['type'] = event_type_labels.get(e.event_type, e.event_type or '')
            if 'project' in selected:
                proj = self.events_tab.project_repo.get_by_id(e.project_id)
                row['project'] = proj.name if proj else ''
            if 'yes_count' in selected:
                avails = self.events_tab.avail_repo.get_by_event(e.id)
                row['yes_count'] = sum(1 for a in avails if a.status == 'yes')
            if 'conditional_count' in selected:
                avails = self.events_tab.avail_repo.get_by_event(e.id)
                row['conditional_count'] = sum(1 for a in avails if a.status == 'conditional')
            data.append(row)

        content, ext_filter = self._format_export(data, selected, fmt)

        today = datetime.now().strftime('%Y-%m-%d')
        workdir = Path(__file__).parent.parent / 'workdir'
        workdir.mkdir(exist_ok=True)
        ext_map = {'writer': 'odt', 'calc': 'ods', 'csv': 'csv'}
        ext = ext_map.get(fmt, 'csv')
        default_path = str(workdir / f'{today}-termine.{ext}')

        filename, _ = QFileDialog.getSaveFileName(
            self, 'Termine exportieren',
            default_path, ext_filter
        )
        if not filename:
            return

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        self.statusBar().showMessage(f'Termine exportiert ({fmt.upper()})')

    def _export_aufstellung(self):
        aufstellung_fields = [
            {'name': 'filename', 'label': 'Dateiname'},
            {'name': 'size', 'label': 'Dateigröße'},
            {'name': 'project', 'label': 'Projekt'},
            {'name': 'event_date', 'label': 'Termin'},
            {'name': 'event', 'label': 'Typ'},
            {'name': 'saved_at', 'label': 'Gespeichert'},
        ]

        dialog = ExportDialog(aufstellung_fields, self)
        if not dialog.exec():
            return

        selected = dialog.get_selected_fields()
        fmt = dialog.get_export_format()

        if not selected:
            QMessageBox.warning(self, 'Warnung', 'Keine Felder ausgewählt.')
            return

        service = ExportService()
        data_dir = self.choraufstellung_tab._data_dir

        files = []
        if os.path.exists(data_dir):
            for f in os.listdir(data_dir):
                if f.endswith('.json'):
                    fp = os.path.join(data_dir, f)
                    stats = os.stat(fp)
                    entry = {'filename': f, 'size': stats.st_size}
                    try:
                        with open(fp, 'r', encoding='utf-8') as jf:
                            content_json = json.load(jf)
                            entry['metadata'] = content_json.get('metadata', {})
                            entry['saved_at'] = content_json.get('saved_at', '')
                    except Exception:
                        entry['metadata'] = {}
                        entry['saved_at'] = ''
                    files.append(entry)

        data = []
        for f in files:
            meta = f.get('metadata', {})
            row = {}
            if 'filename' in selected:
                row['filename'] = f['filename']
            if 'size' in selected:
                sz = f.get('size', 0)
                row['size'] = f'{sz // 1024} KB' if sz >= 1024 else f'{sz} B'
            if 'project' in selected:
                row['project'] = meta.get('project', '')
            if 'event_date' in selected:
                ed = meta.get('event_date', '')
                row['event_date'] = ed[:10] if ed else ''
            if 'event' in selected:
                row['event'] = meta.get('event', '')
            if 'saved_at' in selected:
                saved = f.get('saved_at', '')
                if saved:
                    try:
                        dt = datetime.fromisoformat(saved)
                        row['saved_at'] = dt.strftime('%d.%m.%Y %H:%M')
                    except Exception:
                        row['saved_at'] = saved
                else:
                    row['saved_at'] = ''
            data.append(row)

        content, ext_filter = self._format_export(data, selected, fmt)

        today = datetime.now().strftime('%Y-%m-%d')
        workdir = Path(__file__).parent.parent / 'workdir'
        workdir.mkdir(exist_ok=True)
        ext_map = {'writer': 'odt', 'calc': 'ods', 'csv': 'csv'}
        ext = ext_map.get(fmt, 'csv')
        default_path = str(workdir / f'{today}-aufstellungen.{ext}')

        filename, _ = QFileDialog.getSaveFileName(
            self, 'Aufstellungen exportieren',
            default_path, ext_filter
        )
        if not filename:
            return

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        self.statusBar().showMessage(f'Aufstellungen exportiert ({fmt.upper()})')
