"""RBAC roles and permissions."""

from enum import StrEnum


class Role(StrEnum):
    ARTIST = "artist"
    PERFORMER = "performer"
    MODERATOR = "moderator"
    ADMIN = "admin"


DEFAULT_SIGNUP_ROLES = {Role.ARTIST}
