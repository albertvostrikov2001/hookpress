"""Studio domain enums."""

from enum import StrEnum


class AiTaskStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AiTaskType(StrEnum):
    GENERATE_LYRICS = "GENERATE_LYRICS"
    GENERATE_AUDIO = "GENERATE_AUDIO"
    GENERATE_WAVEFORM = "GENERATE_WAVEFORM"


class StudioProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
