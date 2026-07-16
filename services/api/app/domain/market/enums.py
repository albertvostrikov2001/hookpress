"""Market domain enums."""

from enum import StrEnum


class KworkCategory(StrEnum):
    DESIGN = "design"
    PRODUCTION = "production"
    SOUND_ENGINEERING = "sound_engineering"
    SONGWRITING = "songwriting"


KWORK_CATEGORIES = frozenset(c.value for c in KworkCategory)
