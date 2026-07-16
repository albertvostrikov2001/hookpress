"""Market and dispute state machines."""

from app.domain.state_machine import StateMachine

MARKET_ORDER_TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"AWAITING_PAYMENT", "CANCELLED"},
    "AWAITING_PAYMENT": {"FUNDS_HELD", "CANCELLED"},
    "FUNDS_HELD": {"IN_PROGRESS", "CANCELLED"},
    "IN_PROGRESS": {"DELIVERED", "IN_DISPUTE"},
    "DELIVERED": {"COMPLETED", "IN_DISPUTE", "REVISION_REQUESTED"},
    "REVISION_REQUESTED": {"REVISION_IN_PROGRESS", "IN_DISPUTE"},
    "REVISION_IN_PROGRESS": {"DELIVERED", "IN_DISPUTE"},
    "IN_DISPUTE": {"REFUNDED", "PARTIALLY_REFUNDED", "COMPLETED"},
    "COMPLETED": set(),
    "REFUNDED": set(),
    "PARTIALLY_REFUNDED": set(),
    "CANCELLED": set(),
}

DISPUTE_TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"UNDER_REVIEW", "CLOSED"},
    "UNDER_REVIEW": {"RESOLVED", "CLOSED"},
    "RESOLVED": {"CLOSED"},
    "CLOSED": set(),
}

market_order_state_machine = StateMachine("market_order", MARKET_ORDER_TRANSITIONS)
dispute_state_machine = StateMachine("dispute", DISPUTE_TRANSITIONS)
