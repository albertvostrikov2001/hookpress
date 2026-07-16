"""Payment intent state machine (Master Prompt §23)."""

from app.domain.state_machine import StateMachine

PAYMENT_TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"PENDING"},
    "PENDING": {"AUTHORIZED", "FAILED"},
    "AUTHORIZED": {"CAPTURED", "FAILED"},
    "CAPTURED": {"PARTIALLY_REFUNDED", "REFUNDED"},
    "PARTIALLY_REFUNDED": {"REFUNDED"},
    "REFUNDED": set(),
    "FAILED": set(),
}

payment_state_machine = StateMachine("payment", PAYMENT_TRANSITIONS)


def transition_payment(from_state: str, to_state: str) -> str:
    payment_state_machine.assert_transition(from_state, to_state)
    return to_state


def payment_status_external(internal: str) -> str:
    """Map internal payment state to provider-facing status."""
    if internal in {"CREATED", "PENDING", "AUTHORIZED"}:
        return "pending"
    if internal in {"CAPTURED", "PARTIALLY_REFUNDED", "REFUNDED"}:
        return "succeeded"
    if internal == "FAILED":
        return "failed"
    return internal.lower()

