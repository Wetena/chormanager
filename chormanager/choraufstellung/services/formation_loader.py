"""Formation data loader — loads singer data from ChorManager DB or event files.

Extracted from MainWindow to reduce its size.
"""

import os


class FormationLoader:
    """Loads singer data from ChorManager DB or event data files."""

    def __init__(self, main_window):
        self._mw = main_window

    def load_from_chormanager(self):
        """Load singers from ChorManager DB or temp JSON file."""
        from services.chor_manager_data_service import (
            load_singers_from_event_data_file,
            load_singers_from_db,
        )

        mw = self._mw
        event_data_file = os.environ.get("CHOR_EVENT_DATA", "")

        if event_data_file and os.path.exists(event_data_file):
            result = load_singers_from_event_data_file(event_data_file)
            if result:
                mw._loaded_metadata = result["metadata"]
                mw.singers = result["singers"]
                mw.pool.singers = mw.singers
                mw.pool.update_singers(mw.singers, set())
                mw.is_modified = False
                return

        db_path = os.environ.get("CHOR_DB_PATH", os.path.expanduser("~/.local/share/chormanager/chor.db"))
        event_id = mw.event_id or os.environ.get("CHOR_EVENT_ID", "")

        if not db_path or not os.path.exists(db_path):
            return

        singers = load_singers_from_db(db_path, event_id=event_id)
        if singers:
            mw.singers = singers
            mw.pool.singers = mw.singers
            mw.pool.update_singers(mw.singers, set())
            mw.is_modified = False

    def load_formation_data(self, data):
        """Load formation data from dict (used when opening saved file)."""
        mw = self._mw
        mw.singers = data.get("singers", [])
        for s in mw.singers:
            if not hasattr(s, 'affinity'):
                s.affinity = ""
        mw.grid.singers = [s for s in mw.singers if s.row >= 0]
        mw.grid.rows = data.get("rows", 3)
        mw.grid.cols = data.get("cols", 4)
        mw.grid.staggered = data.get("staggered", False)
        mw.grid.refresh_grid()
        mw.pool.singers = mw.singers
        mw.pool.placed_singer_ids = mw.grid.get_placed_singer_ids()
        mw.pool.update_singers(mw.singers, mw.pool.placed_singer_ids)
        mw.is_modified = False
        mw.update_grid_count()

        if hasattr(mw, 'rs'):
            mw.rs.blockSignals(True)
            mw.rs.setCurrentText(str(mw.grid.rows))
            mw.rs.blockSignals(False)
        if hasattr(mw, 'cs'):
            mw.cs.blockSignals(True)
            mw.cs.setCurrentText(str(mw.grid.cols))
            mw.cs.blockSignals(False)
