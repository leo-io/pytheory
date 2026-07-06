from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..rhythm import Score


class ScoreRepository(Protocol):
    """Persistence boundary for score-oriented applications."""

    def store(self, score: "Score") -> str:
        ...

    def get(self, score_id: str) -> "Score" | None:
        ...

