"""AI task state machine (Master Prompt §23)."""

from app.domain.studio.enums import AiTaskStatus
from app.domain.state_machine import StateMachine

AI_TASK_TRANSITIONS: dict[str, set[str]] = {
    AiTaskStatus.PENDING: {AiTaskStatus.PROCESSING, AiTaskStatus.CANCELLED},
    AiTaskStatus.PROCESSING: {
        AiTaskStatus.SUCCEEDED,
        AiTaskStatus.FAILED,
        AiTaskStatus.CANCELLED,
    },
    AiTaskStatus.SUCCEEDED: set(),
    AiTaskStatus.FAILED: set(),
    AiTaskStatus.CANCELLED: set(),
}

ai_task_state_machine = StateMachine("ai_task", AI_TASK_TRANSITIONS)


def assert_ai_task_transition(from_state: str, to_state: str) -> None:
    ai_task_state_machine.assert_transition(from_state, to_state)
