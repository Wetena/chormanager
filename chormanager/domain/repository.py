"""Repository layer for ChorManager — backward-compatible re-exports.

Individual repositories are now in domain/repositories/.
"""

from .repositories.singer import SingerRepository
from .repositories.event import EventRepository
from .repositories.availability import AvailabilityRepository
from .repositories.project import ProjectRepository
from .repositories.besetzung import BesetzungRepository
from .repositories.repertoire import RepertoireRepository

__all__ = [
    "SingerRepository",
    "EventRepository",
    "AvailabilityRepository",
    "ProjectRepository",
    "BesetzungRepository",
    "RepertoireRepository",
]
