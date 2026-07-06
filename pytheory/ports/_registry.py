from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class BackendRegistry(Generic[T]):
    """Small lazy registry used for pluggable adapters."""

    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._backend: T | None = None

    def get(self) -> T:
        if self._backend is None:
            self._backend = self._factory()
        return self._backend

    def register(self, backend: T) -> T:
        self._backend = backend
        return backend

    def reset(self) -> None:
        self._backend = None

