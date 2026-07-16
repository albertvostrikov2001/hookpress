"""State machine tests."""

import pytest

from app.domain.billing.state_machines import payment_state_machine, transition_payment
from app.domain.state_machine import InvalidStateTransition, StateMachine
from app.domain.studio.enums import AiTaskStatus
from app.domain.studio.state_machines import ai_task_state_machine


def test_valid_transition():
    sm = StateMachine("order", {"CREATED": {"PAID", "CANCELLED"}})
    assert sm.can_transition("CREATED", "PAID") is True
    sm.assert_transition("CREATED", "PAID")


def test_invalid_transition():
    sm = StateMachine("order", {"CREATED": {"PAID"}})
    with pytest.raises(InvalidStateTransition):
        sm.assert_transition("CREATED", "SHIPPED")


def test_ai_task_state_machine_happy_path():
    ai_task_state_machine.assert_transition(AiTaskStatus.PENDING, AiTaskStatus.PROCESSING)
    ai_task_state_machine.assert_transition(AiTaskStatus.PROCESSING, AiTaskStatus.SUCCEEDED)


def test_ai_task_invalid_transition():
    with pytest.raises(InvalidStateTransition):
        ai_task_state_machine.assert_transition(AiTaskStatus.PENDING, AiTaskStatus.SUCCEEDED)


def test_payment_state_machine_webhook_path():
    state = transition_payment("CREATED", "PENDING")
    state = transition_payment(state, "AUTHORIZED")
    state = transition_payment(state, "CAPTURED")
    assert state == "CAPTURED"


def test_payment_invalid_refund_from_pending():
    with pytest.raises(InvalidStateTransition):
        payment_state_machine.assert_transition("PENDING", "REFUNDED")

