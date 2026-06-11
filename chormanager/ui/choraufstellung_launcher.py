"""Choraufstellung subprocess launcher."""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime

from PyQt6.QtWidgets import QMessageBox


def get_choraufstellung_path():
    """Get the path to the choraufstellung sub-app."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "choraufstellung"
    )


def launch_choraufstellung(window, event=None, filepath=None):
    """Launch choraufstellung as a subprocess.

    Args:
        window: MainWindow instance.
        event: Optional event to load.
        filepath: Optional formation file to open.
    """
    choraufstellung_path = get_choraufstellung_path()

    if not os.path.exists(choraufstellung_path):
        QMessageBox.warning(
            window, "Fehler",
            f"Choraufstellung nicht gefunden unter:\n{choraufstellung_path}",
        )
        return

    env = os.environ.copy()
    db_path = window.db_path or os.path.expanduser("~/.local/share/chormanager/chor.db")
    env["CHOR_DB_PATH"] = db_path

    if event:
        _prepare_event_data(window, event, env)
    elif filepath:
        env["CHOR_FILE"] = filepath
    else:
        project = getattr(window, "current_project", None)
        if project:
            env["CHOR_PROJECT"] = project.name
        current_row = window.events_tab.table.currentRow() if hasattr(window, "events_tab") else -1
        if current_row >= 0:
            item = window.events_tab.table.item(current_row, 0)
            event_id = item.data(0x0100) if item else None  # Qt.ItemDataRole.UserRole
            if event_id:
                ev = window.events_tab.event_repo.get_by_id(event_id)
                if ev:
                    env["CHOR_EVENT_DATE"] = ev.date[:10]
                    env["CHOR_EVENT_NAME"] = ev.name
                    env["CHOR_EVENT_ID"] = ev.id
                    env["CHOR_EVENT_TYPE"] = ev.event_type

    try:
        main_py = os.path.join(choraufstellung_path, "__main__.py")
        if os.path.exists(main_py):
            subprocess.run([sys.executable, main_py], cwd=choraufstellung_path, env=env)
            if hasattr(window, "choraufstellung_tab"):
                window.choraufstellung_tab._load_formations()
    except Exception as e:
        QMessageBox.warning(
            window, "Fehler",
            f"Choraufstellung konnte nicht gestartet werden:\n{e}",
        )


def launch_for_event(window, event):
    """Launch choraufstellung with event data via temp file.

    Args:
        window: MainWindow instance.
        event: Event to load singers for.
    """
    from ..domain.repository import SingerRepository, AvailabilityRepository

    window.content_stack.setCurrentIndex(4)

    project = getattr(window, "current_project", None) or (
        window.projects_tab.current_project if hasattr(window, "projects_tab") else None
    )

    singer_repo = SingerRepository(window.db)
    avail_repo = AvailabilityRepository(window.db)

    singers = singer_repo.get_all()
    available_singers = []
    for singer in singers:
        avail = avail_repo.get_by_ids(singer.id, event.id)
        if avail and avail.status in ("yes", "conditional"):
            available_singers.append({
                "singer_id": singer.id,
                "name": singer.full_name,
                "short_name": singer.short_name or "",
                "voice_group": singer.voice_group,
                "height": singer.height or 0,
                "affinity": singer.affinity_uuid or "",
            })

    data = {
        "project": project.name if project else "",
        "event": {
            "id": event.id,
            "name": event.name,
            "date": event.date,
            "event_type": event.event_type,
        },
        "singers": available_singers,
        "created_at": datetime.now().isoformat(),
    }

    temp_file = os.path.join(tempfile.gettempdir(), "choraufstellung_event.json")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    env = os.environ.copy()
    env["CHOR_EVENT_DATA"] = temp_file
    env["CHOR_PROJECT"] = data.get("project", "")
    env["CHOR_EVENT_DATE"] = event.date[:10]
    env["CHOR_EVENT_NAME"] = event.name
    env["CHOR_EVENT_ID"] = event.id
    env["CHOR_EVENT_TYPE"] = event.event_type

    choraufstellung_path = get_choraufstellung_path()
    try:
        main_py = os.path.join(choraufstellung_path, "__main__.py")
        if os.path.exists(main_py):
            subprocess.run([sys.executable, main_py], cwd=choraufstellung_path, env=env)
            if hasattr(window, "choraufstellung_tab"):
                window.choraufstellung_tab._load_formations()
    except Exception as e:
        QMessageBox.warning(
            window, "Fehler",
            f"Choraufstellung konnte nicht gestartet werden:\n{e}",
        )


def _prepare_event_data(window, event, env):
    """Prepare environment variables for event data."""
    from ..domain.repository import SingerRepository, AvailabilityRepository

    singer_repo = SingerRepository(window.db)
    avail_repo = AvailabilityRepository(window.db)

    singers = singer_repo.get_all()
    available_singers = []
    for singer in singers:
        avail = avail_repo.get_by_ids(singer.id, event.id)
        if avail and avail.status in ("yes", "conditional"):
            available_singers.append({
                "singer_id": singer.id,
                "name": singer.full_name,
                "short_name": singer.short_name or "",
                "voice_group": singer.voice_group,
                "height": singer.height or 0,
                "affinity": singer.affinity_uuid or "",
            })

    project = getattr(window, "current_project", None) or (
        window.projects_tab.current_project if hasattr(window, "projects_tab") else None
    )

    data = {
        "project": project.name if project else "",
        "event": {
            "id": event.id,
            "name": event.name,
            "date": event.date,
            "event_type": event.event_type,
        },
        "singers": available_singers,
        "created_at": datetime.now().isoformat(),
    }

    temp_file = os.path.join(tempfile.gettempdir(), "choraufstellung_event.json")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    env["CHOR_EVENT_DATA"] = temp_file
    env["CHOR_PROJECT"] = data.get("project", "")
