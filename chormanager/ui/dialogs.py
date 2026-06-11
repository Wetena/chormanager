"""Dialogs for event management - backward compatibility re-exports.

All dialog classes have been moved to chormanager/ui/dialogs/ package.
This module re-exports them for backward compatibility.
"""

from .dialogs import (
    sanitize_filename,
    AVAILABILITY_STATUS,
    AvailabilityDelegate,
    AvailabilityDialog,
    EventDialog,
    EventListDialog,
    EventAvailabilityDialog,
    ConfigDialog,
    SelbstdarstellungDialog,
    SingerSelectionDialog,
    DropZone,
    BackupRestoreDialog,
    NewFormationDialog,
    RepertoireDialog,
)

__all__ = [
    "sanitize_filename",
    "AVAILABILITY_STATUS",
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
