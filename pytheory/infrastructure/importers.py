from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import warnings
from os import PathLike
from typing import Sequence

import numpy
from scipy.io import wavfile

from ..ports.audio import AudioConverter


Pathish = str | PathLike[str]


class WavFileReader:
    """Read WAV files into normalized mono numpy arrays."""

    def read(self, path: Pathish) -> tuple[numpy.ndarray, int]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sample_rate, data = wavfile.read(path)
        data = numpy.asarray(data)
        if data.dtype == numpy.int16:
            data = data / 32768.0
        elif data.dtype == numpy.int32:
            data = data / 2147483648.0
        elif data.dtype == numpy.uint8:
            data = (data.astype(numpy.float64) - 128.0) / 128.0
        else:
            data = data.astype(numpy.float64)
        if data.ndim > 1:
            data = data.mean(axis=1)
        return data.astype(numpy.float64), sample_rate


class AfconvertConverter:
    name = "afconvert"

    def available(self) -> bool:
        return shutil.which(self.name) is not None

    def convert(self, source: Pathish, target: Pathish) -> None:
        subprocess.run(
            [self.name, "-f", "WAVE", "-d", "LEI16@44100", str(source), str(target)],
            check=True,
            capture_output=True,
        )


class FFMpegConverter:
    name = "ffmpeg"

    def available(self) -> bool:
        return shutil.which(self.name) is not None

    def convert(self, source: Pathish, target: Pathish) -> None:
        subprocess.run(
            [self.name, "-y", "-i", str(source), "-ar", "44100", str(target)],
            check=True,
            capture_output=True,
        )


class DefaultAudioLoader:
    """Default audio loader backed by WAV I/O plus optional converters."""

    def __init__(
        self,
        *,
        reader: WavFileReader | None = None,
        converters: Sequence[AudioConverter] | None = None,
    ) -> None:
        self._reader = reader or WavFileReader()
        self._converters = list(converters or (AfconvertConverter(), FFMpegConverter()))

    def load(self, path: Pathish) -> tuple[numpy.ndarray, int]:
        if str(path).lower().endswith(".wav"):
            return self._reader.read(path)
        return self._load_via_converter(path)

    def _load_via_converter(self, path: Pathish) -> tuple[numpy.ndarray, int]:
        fd, tmp = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            for converter in self._converters:
                if converter.available():
                    converter.convert(path, tmp)
                    return self._reader.read(tmp)
            raise RuntimeError(
                f"Can't read {path!r}: converting non-WAV audio needs an installed "
                "converter backend such as afconvert or ffmpeg."
            )
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

