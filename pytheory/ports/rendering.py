from __future__ import annotations

from os import PathLike
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..rhythm import Score


class ScoreRenderer(Protocol):
    """Render a score into audio artifacts."""

    @property
    def sample_rate(self) -> int:
        ...

    def render(self, score: "Score") -> Any:
        ...

    def to_wav_bytes(self, score: "Score") -> bytes:
        ...

    def save_wav(self, score: "Score", path: str | PathLike[str]) -> str | PathLike[str]:
        ...

