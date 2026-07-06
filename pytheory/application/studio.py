from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

from ..ports import (
    get_audio_transcriber,
    get_browser_launcher,
    get_score_renderer,
    get_score_repository,
)


@dataclass(frozen=True)
class TranscriptionOptions:
    bpm: int | None = None
    quantize: float | None = None
    split: bool = False
    part_name: str = "melody"
    synth: str = "piano_synth"
    fmin: float = 50.0
    fmax: float = 1500.0

    @classmethod
    def from_query(cls, params: dict[str, str]) -> "TranscriptionOptions":
        bpm = int(params["bpm"]) if params.get("bpm") else None
        quantize = float(params["quantize"]) if params.get("quantize") else None
        return cls(
            bpm=bpm,
            quantize=quantize,
            split=params.get("split") in ("1", "true", "on"),
            part_name=params.get("part_name", "melody"),
            synth=params.get("synth", "piano_synth"),
            fmin=float(params["fmin"]) if params.get("fmin") else 50.0,
            fmax=float(params["fmax"]) if params.get("fmax") else 1500.0,
        )


class StudioApplication:
    """HTTP-agnostic use cases for the Studio experience."""

    def __init__(
        self,
        *,
        repository=None,
        transcriber=None,
        renderer=None,
        browser_launcher=None,
    ) -> None:
        self.repository = repository or get_score_repository()
        self.transcriber = transcriber or get_audio_transcriber()
        self.renderer = renderer or get_score_renderer()
        self.browser_launcher = browser_launcher or get_browser_launcher()

    def transcribe_upload(
        self,
        audio_bytes: bytes,
        filename: str,
        options: TranscriptionOptions,
    ) -> dict[str, object]:
        from ..rhythm import Score

        suffix = os.path.splitext(filename)[1] or ".wav"
        fd, tmp = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(audio_bytes)
            score = self.transcriber.transcribe(
                tmp,
                bpm=options.bpm,
                quantize=options.quantize,
                split=options.split,
                part_name=options.part_name,
                synth=options.synth,
                fmin=options.fmin,
                fmax=options.fmax,
            )
            if not isinstance(score, Score):
                raise TypeError("Active audio transcriber must return a Score.")
        finally:
            os.unlink(tmp)

        score_id = self.repository.store(score)
        title = os.path.splitext(os.path.basename(filename))[0] or "Transcription"
        detected = getattr(score, "detected_key", None)
        parts = {
            name: sum(1 for note in part.notes if note.tone is not None)
            for name, part in score.parts.items()
        }
        if score._drum_hits:
            parts["drums"] = len(score._drum_hits)
        return {
            "id": score_id,
            "bpm": score.bpm,
            "key": str(detected) if detected else None,
            "parts": parts,
            "abc": score.to_abc(title=title, key=self._abc_key_for(detected)),
        }

    def render_score_wav_bytes(self, score_id: str) -> bytes | None:
        score = self.repository.get(score_id)
        if score is None:
            return None
        return self.renderer.to_wav_bytes(score)

    def score_midi_bytes(self, score_id: str) -> bytes | None:
        score = self.repository.get(score_id)
        if score is None:
            return None
        fd, tmp = tempfile.mkstemp(suffix=".mid")
        os.close(fd)
        try:
            score.save_midi(tmp)
            with open(tmp, "rb") as handle:
                return handle.read()
        finally:
            os.unlink(tmp)

    def launch_browser(self, url: str) -> None:
        self.browser_launcher.open(url)

    @staticmethod
    def _abc_key_for(detected_key) -> str:
        if detected_key is None:
            return "C"
        tonic = detected_key.note_names[0]
        return tonic + ("m" if detected_key.mode == "minor" else "")

