"""Reusable state machine guard."""

from app.core.errors import AppError


class InvalidStateTransition(AppError):
    def __init__(self, entity: str, from_state: str, to_state: str):
        super().__init__(
            code="invalid_state_transition",
            message=f"Cannot transition {entity} from {from_state} to {to_state}",
            status_code=409,
            details={"entity": entity, "from": from_state, "to": to_state},
        )


class StateMachine:
    def __init__(self, entity: str, transitions: dict[str, set[str]]):
        self.entity = entity
        self.transitions = transitions

    def can_transition(self, from_state: str, to_state: str) -> bool:
        return to_state in self.transitions.get(from_state, set())

    def assert_transition(self, from_state: str, to_state: str) -> None:
        if not self.can_transition(from_state, to_state):
            raise InvalidStateTransition(self.entity, from_state, to_state)
