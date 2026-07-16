"""OAuth-style scopes derived from RBAC roles."""

from enum import StrEnum

from app.domain.auth.roles import Role


class Scope(StrEnum):
    STUDIO_READ = "studio:read"
    STUDIO_WRITE = "studio:write"
    OFFICE_READ = "office:read"
    OFFICE_WRITE = "office:write"
    MARKET_READ = "market:read"
    MARKET_WRITE = "market:write"
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    PROMO_READ = "promo:read"
    PROMO_WRITE = "promo:write"
    NOTIFICATIONS_READ = "notifications:read"
    NOTIFICATIONS_WRITE = "notifications:write"
    ADMIN = "admin:all"


ROLE_SCOPES: dict[Role, set[Scope]] = {
    Role.ARTIST: {
        Scope.STUDIO_READ,
        Scope.STUDIO_WRITE,
        Scope.OFFICE_READ,
        Scope.OFFICE_WRITE,
        Scope.MARKET_READ,
        Scope.MARKET_WRITE,
        Scope.BILLING_READ,
        Scope.BILLING_WRITE,
        Scope.PROMO_READ,
        Scope.PROMO_WRITE,
        Scope.NOTIFICATIONS_READ,
        Scope.NOTIFICATIONS_WRITE,
    },
    Role.PERFORMER: {
        Scope.STUDIO_READ,
        Scope.STUDIO_WRITE,
        Scope.OFFICE_READ,
        Scope.OFFICE_WRITE,
        Scope.MARKET_READ,
        Scope.MARKET_WRITE,
        Scope.BILLING_READ,
        Scope.BILLING_WRITE,
        Scope.PROMO_READ,
        Scope.PROMO_WRITE,
        Scope.NOTIFICATIONS_READ,
        Scope.NOTIFICATIONS_WRITE,
    },
    Role.MODERATOR: {
        Scope.STUDIO_READ,
        Scope.OFFICE_READ,
        Scope.MARKET_READ,
        Scope.BILLING_READ,
        Scope.PROMO_READ,
        Scope.NOTIFICATIONS_READ,
        Scope.NOTIFICATIONS_WRITE,
    },
    Role.ADMIN: {Scope.ADMIN},
}


def scopes_for_roles(roles: list[str]) -> list[str]:
    granted: set[Scope] = set()
    for role_name in roles:
        try:
            role = Role(role_name)
        except ValueError:
            continue
        granted.update(ROLE_SCOPES.get(role, set()))
    if Scope.ADMIN in granted:
        return sorted({s.value for s in Scope})
    return sorted(s.value for s in granted)


def scopes_from_payload(payload: dict) -> set[Scope]:
    raw = payload.get("scopes") or []
    return {Scope(s) for s in raw if s in Scope._value2member_map_}
