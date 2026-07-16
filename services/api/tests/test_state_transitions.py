"""Office and release state transition tests."""

import pytest

from app.domain.office.enums import OfficeProjectStatus, ReleaseStatus
from app.domain.office.state_machines import office_project_state_machine, release_state_machine
from app.domain.state_machine import InvalidStateTransition


def test_office_project_valid_transitions():
    office_project_state_machine.assert_transition(
        OfficeProjectStatus.DRAFT_IN_STUDIO,
        OfficeProjectStatus.DRAFT_IN_OFFICE,
    )
    office_project_state_machine.assert_transition(
        OfficeProjectStatus.DRAFT_IN_OFFICE,
        OfficeProjectStatus.READY_FOR_RELEASE,
    )


def test_office_project_invalid_transition():
    with pytest.raises(InvalidStateTransition):
        office_project_state_machine.assert_transition(
            OfficeProjectStatus.DRAFT_IN_STUDIO,
            OfficeProjectStatus.READY_FOR_RELEASE,
        )


def test_release_draft_to_validating():
    release_state_machine.assert_transition(ReleaseStatus.DRAFT, ReleaseStatus.VALIDATING)


def test_release_validation_pipeline():
    release_state_machine.assert_transition(ReleaseStatus.VALIDATING, ReleaseStatus.MODERATION)
    release_state_machine.assert_transition(ReleaseStatus.MODERATION, ReleaseStatus.DELIVERED)
    release_state_machine.assert_transition(ReleaseStatus.DELIVERED, ReleaseStatus.RELEASED)


def test_release_failure_paths():
    release_state_machine.assert_transition(ReleaseStatus.VALIDATING, ReleaseStatus.FAILED)
    release_state_machine.assert_transition(ReleaseStatus.MODERATION, ReleaseStatus.REJECTED)


def test_release_invalid_skip():
    with pytest.raises(InvalidStateTransition):
        release_state_machine.assert_transition(ReleaseStatus.DRAFT, ReleaseStatus.RELEASED)
