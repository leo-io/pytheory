import numpy

from pytheory.engines import PluginSpec
from pytheory.pedalboard_engine import (
    _load_plugin,
    _normalize_audio_output,
    _note_events_to_midi_messages,
)
from pytheory.rhythm import Duration, Score


def test_midi_timestamps_are_absolute_and_sorted():
    score = Score("4/4", bpm=120)
    part = score.part("lead", synth="sine")
    part.add("C4", Duration.QUARTER)
    part.add("E4", Duration.QUARTER)
    messages = _note_events_to_midi_messages(part.notes, score, part)
    times = [t for _, t in messages]
    assert times == sorted(times)
    assert times[0] == 0.0
    assert times[1] == 0.5


def test_normalize_audio_output_shapes_and_dtype():
    mono = _normalize_audio_output(numpy.ones(10, dtype=numpy.float64), 12)
    assert mono.shape == (12, 2)
    assert mono.dtype == numpy.float32
    assert mono.flags.c_contiguous

    channel_first = _normalize_audio_output(numpy.ones((2, 8), dtype=numpy.float32), 8)
    assert channel_first.shape == (8, 2)


def test_load_plugin_applies_preset_and_reset(monkeypatch, tmp_path):
    plugin_path = tmp_path / "instrument.vst3"
    plugin_path.write_text("x", encoding="utf-8")
    calls = []

    class FakePlugin:
        is_instrument = True
        is_effect = False

        def load_preset(self, preset):
            calls.append(("preset", preset))

        def reset(self):
            calls.append(("reset",))

    class FakeMidoMessage:
        def __init__(self, data):
            self._data = bytes(data)

        @classmethod
        def from_bytes(cls, data):
            return cls(data)

        def bytes(self):
            return list(self._data)

    class FakePedalboard:
        @staticmethod
        def load_plugin(path, parameter_values, plugin_name, initialization_timeout):
            calls.append(("load", path, dict(parameter_values), plugin_name, initialization_timeout))
            return FakePlugin()

    import pytheory.pedalboard_engine as pbe

    def fake_import():
        class FakeMido:
            Message = FakeMidoMessage

        return FakePedalboard, FakeMido

    monkeypatch.setattr(pbe, "_import_pedalboard", fake_import)
    spec = PluginSpec(path=str(plugin_path), preset="preset.fxp", parameters={"gain": 0.5})
    plugin = _load_plugin(spec, "instrument")
    assert isinstance(plugin, FakePlugin)
    assert calls[0][0] == "load"
    assert calls[1] == ("preset", "preset.fxp")
    assert calls[2] == ("reset",)
