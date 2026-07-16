"""Office domain enums."""

from enum import StrEnum


class OfficeProjectStatus(StrEnum):
    DRAFT_IN_STUDIO = "DRAFT_IN_STUDIO"
    DRAFT_IN_OFFICE = "DRAFT_IN_OFFICE"
    READY_FOR_RELEASE = "READY_FOR_RELEASE"


class ReleaseStatus(StrEnum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    MODERATION = "MODERATION"
    DELIVERED = "DELIVERED"
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class MediaUploadStatus(StrEnum):
    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class ReleaseType(StrEnum):
    SINGLE = "SINGLE"
    EP = "EP"
    ALBUM = "ALBUM"


class MediaAssetStatus(StrEnum):
    UPLOADING = "UPLOADING"
    SCANNING = "SCANNING"
    READY = "READY"
    REJECTED = "REJECTED"
