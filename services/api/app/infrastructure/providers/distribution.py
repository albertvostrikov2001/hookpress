"""Distribution provider interfaces."""

from abc import ABC, abstractmethod
import uuid


class DistributionProvider(ABC):
    @abstractmethod
    async def submit_release(self, release_id: uuid.UUID, metadata: dict) -> dict:
        raise NotImplementedError


class MockDistributionProvider(DistributionProvider):
    async def submit_release(self, release_id: uuid.UUID, metadata: dict) -> dict:
        return {
            "external_id": f"mock-dist-{release_id}",
            "status": "ACCEPTED",
            "metadata": metadata,
        }
