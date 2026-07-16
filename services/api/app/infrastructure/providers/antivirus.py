"""Antivirus scanner interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ScanResult:
    clean: bool
    threat_name: str | None = None
    provider: str = "mock"


class AntivirusScanner(ABC):
    @abstractmethod
    async def scan(self, *, bucket: str, object_key: str) -> ScanResult:
        raise NotImplementedError


class MockAntivirusScanner(AntivirusScanner):
    """Mock scanner — passes all files unless object key contains 'eicar'."""

    async def scan(self, *, bucket: str, object_key: str) -> ScanResult:
        if "eicar" in object_key.lower():
            return ScanResult(clean=False, threat_name="EICAR-Test-File", provider="mock")
        return ScanResult(clean=True, provider="mock")
