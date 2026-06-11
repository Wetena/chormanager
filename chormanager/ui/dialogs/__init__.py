"""Dialog modules for ChorManager UI."""

from .helpers import sanitize_filename
from .availability import AvailabilityDelegate, AvailabilityDialog
from .event_dialog import EventDialog
from .event_list_dialog import EventListDialog
from .event_availability import EventAvailabilityDialog
from .config_dialog import ConfigDialog
from .selbstdarstellung import SelbstdarstellungDialog
from .singer_selection import SingerSelectionDialog
from .drop_zone import DropZone
from .backup_restore import BackupRestoreDialog
from .new_formation import NewFormationDialog
from .repertoire_dialog import RepertoireDialog

__all__ = [
    "sanitize_filename",
    "AvailabilityDelegate",
    "AvailabilityDialog",
    "EventDialog",
    "EventListDialog",
    "EventAvailabilityDialog",
    "ConfigDialog",
    "SelbstdarstellungDialog",
    "SingerSelectionDialog",
    "DropZone",
    "BackupRestoreDialog",
    "NewFormationDialog",
    "RepertoireDialog",
]
