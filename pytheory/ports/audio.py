from __future__ import annotations

from os import PathLike
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..rhythm import Score


Pathish = str | PathLike[str]


class AudioConverter(Protocol):
    """Convert an audio file into a WAV file consumable by analysis code."""

    name: str

    def available(self) -> bool:
        ...

    def convert(self, source: Pathish, target: Pathish) -> None:
        ...


class AudioLoader(Protocol):
    """Load an audio file into a mono sample buffer and sample rate."""

    def load(self, path: Pathish) -> tuple[Any, int]:
        ...


class AudioTranscriber(Protocol):
    """Turn an audio file into a musical score."""

    def transcribe(
        self,
        path: Pathish,
        *,
        bpm: int | None = None,
        quantize: float | None = None,
        split: bool = False,
        part_name: str = "melody",
        synth: str = "piano_synth",
        fmin: float = 50.0,
        fmax: float = 1500.0,
    ) -> "Score":
        ...


class AudioPlayer(Protocol):
    """Play musical material through the active audio engine."""

    def play(
        self,
        target: Any,
        *,
        temperament: str = "equal",
        synth: Any = None,
        t: int = 1_000,
        envelope: Any = None,
    ) -> None:
        ...

    def play_score(self, score: "Score") -> None:
        ...

