from __future__ import annotations

from typing import Any


class DefaultAudioTranscriber:
    """Adapter that delegates transcription to the current analysis engine."""

    def transcribe(
        self,
        path,
        *,
        bpm=None,
        quantize=None,
        split=False,
        part_name="melody",
        synth="piano_synth",
        fmin=50.0,
        fmax=1500.0,
    ):
        from ..audio import transcribe

        return transcribe(
            path,
            bpm=bpm,
            quantize=quantize,
            split=split,
            part_name=part_name,
            synth=synth,
            fmin=fmin,
            fmax=fmax,
        )


class DefaultAudioPlayer:
    """Adapter for the built-in playback engine."""

    def play(
        self,
        target: Any,
        *,
        temperament: str = "equal",
        synth: Any = None,
        t: int = 1_000,
        envelope: Any = None,
    ) -> None:
        from ..play import Synth, play

        play(
            target,
            temperament=temperament,
            synth=synth if synth is not None else Synth.SINE,
            t=t,
            envelope=envelope,
        )

    def play_score(self, score) -> None:
        from ..play import play_score

        play_score(score)

