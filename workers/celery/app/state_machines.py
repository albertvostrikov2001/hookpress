"""State machine guards shared by Celery workers."""


class InvalidStateTransition(Exception):
    def __init__(self, entity: str, from_state: str, to_state: str):
        super().__init__(f"Cannot transition {entity} from {from_state} to {to_state}")
        self.entity = entity
        self.from_state = from_state
        self.to_state = to_state


class StateMachine:
    def __init__(self, entity: str, transitions: dict[str, set[str]]):
        self.entity = entity
        self.transitions = transitions

    def assert_transition(self, from_state: str, to_state: str) -> None:
        if to_state not in self.transitions.get(from_state, set()):
            raise InvalidStateTransition(self.entity, from_state, to_state)


AI_TASK_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"SUCCEEDED", "FAILED", "CANCELLED"},
    "SUCCEEDED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
}

ai_task_state_machine = StateMachine("ai_task", AI_TASK_TRANSITIONS)
