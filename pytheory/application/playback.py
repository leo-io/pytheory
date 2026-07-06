from __future__ import annotations

from typing import Any, Iterable

from ..ports import get_audio_player


def play_item(
    item: Any,
    *,
    t: int = 600,
    temperament: str = "equal",
    synth: Any = None,
    envelope: Any = None,
) -> None:
    get_audio_player().play(
        item,
        t=t,
        temperament=temperament,
        synth=synth,
        envelope=envelope,
    )


def play_items(items: Iterable[Any], *, t: int = 600) -> None:
    for item in items:
        play_item(item, t=t)


def play_score(score) -> None:
    get_audio_player().play_score(score)

