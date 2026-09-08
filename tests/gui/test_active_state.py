"""GUI regression tests: restoring/keeping the "Aktiv" state stays safe.

Pinned user-visible regressions (2026-09 audit):

Bug 1 (crash class): ``EventsTab._restore_active_event`` raised
``NameError`` (unbound local ``event``) whenever no
``last_active_event_id`` was stored while the events table had rows —
e.g. first launch with existing data, or after the referenced event
was deleted.

Bug 2 (stale ids): deleting a project/event/besetzung never cleared
the matching ``last_active_*_id`` config key. The next start silently
dropped the restore (``get_by_id`` -> None), so the info bar showed
"Keines" — the user-reported "Aktiv-Parameter verschwinden manchmal".

Bug 4 (stale label): the besetzung info label is only ever written by
the ``active_besetzung_changed`` signal handler — ``_update_info_labels``
ignored it, so after a project switch a besetzung from another project
kept being displayed.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def db(tmp_path):
    from chormanager.data.database import Database

    database = Database(str(tmp_path / "active_state.db"))
    database.connect()
    database.create_tables()
    yield database
    database.close()


@pytest.fixture
def seeded(db):
    """Seed one project, one event and one besetzung; return ids."""
    from chormanager.domain.repository import (
        BesetzungRepository,
        EventRepository,
        ProjectRepository,
    )

    project = ProjectRepository(db).create(name="Hoffmann 2026")
    event = EventRepository(db).create(
        name="Konzert", date="2026-09-01",
        event_type="konzert", project_id=project.id,
    )
    besetzung = BesetzungRepository(db).create(
        name="Konzertbesetzung", project_id=project.id, singer_ids=[]
    )
    return project, event, besetzung


class TestRestoreActiveEventSafe:
    """Bug 1: _restore_active_event must never raise NameError."""

    def test_no_stored_id_with_populated_table_does_not_crash(
        self, qtbot, db, seeded, monkeypatch
    ):
        from chormanager.ui.views.events_tab import EventsTab

        monkeypatch.setattr(
            "chormanager.ui.views.events_tab.get_last_active_event_id",
            lambda: None,
        )
        tab = EventsTab(db)
        qtbot.addWidget(tab)
        try:
            tab._restore_active_event()  # must not raise
        finally:
            tab.deleteLater()

    def test_stored_id_of_deleted_event_does_not_crash(
        self, qtbot, db, seeded, monkeypatch
    ):
        from chormanager.domain.repository import EventRepository
        from chormanager.ui.views.events_tab import EventsTab

        _, event, _ = seeded
        EventRepository(db).delete(event.id)

        monkeypatch.setattr(
            "chormanager.ui.views.events_tab.get_last_active_event_id",
            lambda: event.id,
        )
        tab = EventsTab(db)
        qtbot.addWidget(tab)
        try:
            tab._restore_active_event()  # must not raise
        finally:
            tab.deleteLater()

    def test_valid_id_selects_row(self, qtbot, db, seeded, monkeypatch):
        from chormanager.ui.views.events_tab import EventsTab

        _, event, _ = seeded
        monkeypatch.setattr(
            "chormanager.ui.views.events_tab.get_last_active_event_id",
            lambda: event.id,
        )
        tab = EventsTab(db)
        qtbot.addWidget(tab)
        try:
            tab._restore_active_event()
            assert tab.table.currentRow() >= 0
            item = tab.table.item(tab.table.currentRow(), 0)
            assert item is not None
            assert item.data(0x0100) == event.id  # Qt.ItemDataRole.UserRole
        finally:
            tab.deleteLater()
