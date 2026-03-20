from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(slots=True)
class ProviderFailure:
    provider: str
    message: str
    error_type: str = "provider_error"
    retryable: bool = False


class TranslationProviderError(RuntimeError):
    def __init__(
        self,
        provider: str,
        message: str,
        *,
        error_type: str = "provider_error",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.message = message
        self.error_type = error_type
        self.retryable = retryable

    def to_failure(self) -> ProviderFailure:
        return ProviderFailure(
            provider=self.provider,
            message=self.message,
            error_type=self.error_type,
            retryable=self.retryable,
        )


class TranslationServiceError(RuntimeError):
    def __init__(self, message: str, *, failures: list[ProviderFailure]) -> None:
        super().__init__(message)
        self.failures = failures


@dataclass(slots=True)
class ProviderDescriptor:
    name: str
    enabled: bool
    configured: bool
    description: str
    priority: int


@dataclass(slots=True)
class TranslationAttempt:
    provider: str
    translations: list[str]
    failures: list[ProviderFailure] = field(default_factory=list)


class TranslationProvider(ABC):
    name: str
    description: str

    @property
    @abstractmethod
    def enabled(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def translate_lines(self, lines: list[str], source_lang: str | None, target_lang: str) -> list[str]:
        raise NotImplementedError

    def describe(self, priority: int) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            enabled=self.enabled,
            configured=self.configured,
            description=self.description,
            priority=priority,
        )
