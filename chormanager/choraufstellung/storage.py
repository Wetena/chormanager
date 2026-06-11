import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


def _get_data_dir() -> Path:
    """Returns data directory in program folder."""
    return Path(__file__).parent / "data"


class FormationStorage:
    """Handle saving and loading of choir formations to/from JSON files"""
    
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath
    
    def save_formation(self, singers: List, rows: int, cols: int, 
                       filepath: Optional[str] = None,
                       placed_singers: List[Tuple] = None,
                       staggered: bool = False,
                       voicing_config: List[str] = None,
                       metadata: Dict[str, Any] = None) -> bool:
        """Save formation data to JSON file"""
        target_path = Path(filepath or self.filepath)
        if not target_path:
            raise ValueError("No filepath specified")
        
        try:
            placed_ids = set()
            placed_data = []
            if placed_singers:
                for singer, row, col in placed_singers:
                    placed_ids.add(singer.singer_id)
                    placed_data.append({
                        "singer": singer.to_dict(),
                        "row": row,
                        "col": col
                    })
            
            singers_data = []
            for singer in singers:
                if singer.singer_id not in placed_ids:
                    singers_data.append(singer.to_dict())
            
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "rows": rows,
                "cols": cols,
                "staggered": staggered,
                "voicing_config": voicing_config or [],
                "singers": singers_data,
                "placed": placed_data,
                "metadata": metadata or {}
            }
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, target_path)
            return True
        except Exception as e:
            print(f"Error saving formation: {e}")
            return False
    
    def load_formation(self, filepath: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load formation data from JSON file"""
        target_path = Path(filepath or self.filepath)
        if not target_path:
            raise ValueError("No filepath specified")
            
        if not target_path.exists():
            print(f"File not found: {target_path}")
            return None
            
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            from singer_model import Singer
            
            all_singers = []
            placed_list = []
            
            for placed in data.get("placed", []):
                singer_data = placed.get("singer", {})
                sid = singer_data.get("singer_id", "")
                row = placed.get("row", 0)
                col = placed.get("col", 0)
                
                if sid:
                    singer = Singer.from_dict(singer_data)
                    singer.row = row
                    singer.col = col
                    all_singers.append(singer)
                    placed_list.append((singer, row, col))
            
            for singer_data in data.get("singers", []):
                singer = Singer.from_dict(singer_data)
                if singer.row < 0 and singer.col < 0:
                    all_singers.append(singer)
            
            return {
                "rows": data.get("rows", 3),
                "cols": data.get("cols", 4),
                "staggered": data.get("staggered", False),
                "voicing_config": data.get("voicing_config", []),
                "singers": all_singers,
                "placed": placed_list
            }
        except Exception as e:
            print(f"Error loading formation: {e}")
            return None

    def _get_backup_dir(self) -> Path:
        """Erstellt Backup-Verzeichnis und gibt Pfad zurück."""
        backup_dir = _get_data_dir() / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def save_autosave(self, data: dict, max_keep: int = 5) -> bool:
        """Speichert Auto-Save mit Zeitstempel und Rotation."""
        try:
            backup_dir = self._get_backup_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"autosave_{timestamp}.json"
            filepath = backup_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            latest_link = backup_dir / "latest_autosave.json"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(filename)
            
            self._rotate_backups(backup_dir, max_keep)
            
            return True
        except IOError as e:
            print(f"Auto-save IO error: {e}")
            return False
        except Exception as e:
            print(f"Auto-save error: {e}")
            return False

    def _rotate_backups(self, backup_dir: Path, max_keep: int):
        """Löscht älteste Backups, falls mehr als max_keep vorhanden."""
        try:
            autosave_files = sorted([
                f.name for f in backup_dir.iterdir()
                if f.name.startswith("autosave_") and f.name.endswith(".json")
            ])
            
            while len(autosave_files) > max_keep:
                oldest = autosave_files.pop(0)
                oldest_path = backup_dir / oldest
                if oldest_path.exists():
                    oldest_path.unlink()
        except OSError as e:
            print(f"Backup rotation error: {e}")

    def get_latest_autosave_path(self) -> Optional[str]:
        """Gibt Pfad zum neuesten Auto-Save zurück."""
        try:
            backup_dir = self._get_backup_dir()
            latest_link = backup_dir / "latest_autosave.json"
            if latest_link.exists():
                target = os.readlink(latest_link)
                full_path = backup_dir / target
                if full_path.exists():
                    return str(full_path)
            return None
        except OSError:
            return None

    def get_latest_autosave_mtime(self) -> Optional[float]:
        """Gibt mtime des neuesten Auto-Save zurück."""
        path = self.get_latest_autosave_path()
        if path and Path(path).exists():
            return Path(path).stat().st_mtime
        return None

    def delete_latest_autosave(self) -> bool:
        """Löscht den neuesten Auto-Save."""
        try:
            backup_dir = self._get_backup_dir()
            latest_link = backup_dir / "latest_autosave.json"
            if latest_link.exists():
                target = os.readlink(latest_link)
                full_path = backup_dir / target
                if full_path.exists():
                    full_path.unlink()
                latest_link.unlink()
            return True
        except OSError as e:
            print(f"Error deleting latest autosave: {e}")
            return False
