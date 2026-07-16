"""Office and release state machines."""

from app.domain.office.enums import OfficeProjectStatus, ReleaseStatus
from app.domain.state_machine import StateMachine

OFFICE_PROJECT_TRANSITIONS: dict[str, set[str]] = {
    OfficeProjectStatus.DRAFT_IN_STUDIO: {OfficeProjectStatus.DRAFT_IN_OFFICE},
    OfficeProjectStatus.DRAFT_IN_OFFICE: {OfficeProjectStatus.READY_FOR_RELEASE},
    OfficeProjectStatus.READY_FOR_RELEASE: set(),
}

RELEASE_TRANSITIONS: dict[str, set[str]] = {
    ReleaseStatus.DRAFT: {ReleaseStatus.VALIDATING},
    ReleaseStatus.VALIDATING: {
        ReleaseStatus.MODERATION,
        ReleaseStatus.FAILED,
        ReleaseStatus.REJECTED,
    },
    ReleaseStatus.MODERATION: {
        ReleaseStatus.DELIVERED,
        ReleaseStatus.REJECTED,
        ReleaseStatus.FAILED,
    },
    ReleaseStatus.DELIVERED: {ReleaseStatus.RELEASED, ReleaseStatus.FAILED},
    ReleaseStatus.RELEASED: set(),
    ReleaseStatus.REJECTED: set(),
    ReleaseStatus.FAILED: set(),
}

office_project_state_machine = StateMachine("office_project", OFFICE_PROJECT_TRANSITIONS)
release_state_machine = StateMachine("release", RELEASE_TRANSITIONS)
