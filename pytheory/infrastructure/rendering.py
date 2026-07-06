from __future__ import annotations

import wave
from os import PathLike

import numpy


class DefaultScoreRenderer:
    """Adapter for the built-in synthesis and rendering engine."""

    @property
    def sample_rate(self) -> int:
        from ..play import SAMPLE_RATE

        return SAMPLE_RATE

    def render(self, score):
        from ..play import render_score

        return render_score(score)

    def to_wav_bytes(self, score) -> bytes:
        buf = self.render(score)
        data = (numpy.clip(buf, -1.0, 1.0) * 32767).astype(numpy.int16)
        from io import BytesIO

        out = BytesIO()
        with wave.open(out, "wb") as handle:
            handle.setnchannels(2)
            handle.setsampwidth(2)
            handle.setframerate(self.sample_rate)
            handle.writeframes(data.tobytes())
        return out.getvalue()

    def save_wav(self, score, path: str | PathLike[str]):
        with open(path, "wb") as handle:
            handle.write(self.to_wav_bytes(score))
        return path

