"""Payment provider interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.domain.billing.state_machines import payment_status_external, transition_payment


@dataclass
class PaymentIntent:
    payment_id: str
    status: str
    amount_minor: int
    metadata: dict[str, Any]
    internal_status: str = field(default="CREATED", repr=False)


class PaymentProvider(ABC):
    @abstractmethod
    async def create_payment(
        self,
        *,
        order_id: str,
        amount_minor: int,
        idempotency_key: str,
    ) -> PaymentIntent:
        raise NotImplementedError

    @abstractmethod
    async def parse_webhook(self, payload: dict[str, Any]) -> PaymentIntent:
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    """In-memory mock payment provider for development and tests."""

    def __init__(self) -> None:
        self._payments: dict[str, PaymentIntent] = {}

    async def create_payment(
        self,
        *,
        order_id: str,
        amount_minor: int,
        idempotency_key: str,
    ) -> PaymentIntent:
        if idempotency_key in self._payments:
            return self._payments[idempotency_key]
        internal = transition_payment("CREATED", "PENDING")
        intent = PaymentIntent(
            payment_id=f"mock_{idempotency_key}",
            status=payment_status_external(internal),
            amount_minor=amount_minor,
            metadata={"order_id": order_id, "idempotency_key": idempotency_key},
            internal_status=internal,
        )
        self._payments[idempotency_key] = intent
        return intent

    async def parse_webhook(self, payload: dict[str, Any]) -> PaymentIntent:
        idempotency_key = payload["idempotency_key"]
        amount_minor = int(payload["amount_minor"])
        order_id = payload["order_id"]
        if idempotency_key in self._payments:
            existing = self._payments[idempotency_key]
            if existing.status == "succeeded":
                return existing
            internal = transition_payment(existing.internal_status, "AUTHORIZED")
            internal = transition_payment(internal, "CAPTURED")
            existing.internal_status = internal
            existing.status = payment_status_external(internal)
            return existing
        internal = transition_payment("CREATED", "PENDING")
        internal = transition_payment(internal, "AUTHORIZED")
        internal = transition_payment(internal, "CAPTURED")
        intent = PaymentIntent(
            payment_id=f"mock_{idempotency_key}",
            status=payment_status_external(internal),
            amount_minor=amount_minor,
            metadata={"order_id": order_id, "idempotency_key": idempotency_key},
            internal_status=internal,
        )
        self._payments[idempotency_key] = intent
        return intent

    def reset(self) -> None:
        self._payments.clear()
