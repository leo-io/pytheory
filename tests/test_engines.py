from pathlib import Path

import numpy

from pytheory import (
    clear_plugin_registry,
    get_engine,
    register_drumkit,
    register_instrument,
    set_engine,
)
from pytheory.engines import EffectSpec, PluginSpec, normalize_plugin_spec, snapshot_plugin_registry
from pytheory.play import render_score, render_scores
from pytheory.rhythm import Duration, Score


def test_engine_default_and_validation():
    assert get_engine() == "numpy"
    assert set_engine("numpy") == "numpy"
    try:
        set_engine("wat")
    except ValueError as exc:
        assert "Unknown engine" in str(exc)
    else:
        raise AssertionError("expected invalid engine to fail")


def test_registry_normalizes_absolute_paths(tmp_path):
    clear_plugin_registry()
    plugin_path = tmp_path / "plugin.vst3"
    plugin_path.write_text("x", encoding="utf-8")
    register_instrument("lead", plugin_path)
    register_drumkit(plugin_path, note_map={36: 36})
    registry, drumkit = snapshot_plugin_registry()
    assert registry["lead"].path == str(plugin_path.resolve())
    assert drumkit.path == str(plugin_path.resolve())
    assert drumkit.note_map == {36: 36}


def test_effect_spec_normalization(tmp_path):
    path = tmp_path / "fx.vst3"
    path.write_text("x", encoding="utf-8")
    spec = normalize_plugin_spec(path, mix=0.25)
    assert isinstance(spec, EffectSpec)
    assert spec.mix == 0.25


def test_render_score_engine_override(monkeypatch):
    score = Score("4/4", bpm=120)
    score.part("lead", synth="sine").add("C4", Duration.QUARTER)

    def fake_render(_score):
        return numpy.zeros((32, 2), dtype=numpy.float32)

    monkeypatch.setattr("pytheory.pedalboard_engine.render_score_pedalboard", fake_render)
    buf = render_score(score, engine="pedalboard")
    assert buf.shape == (32, 2)


def test_render_scores_propagates_engine(monkeypatch):
    import importlib

    play_mod = importlib.import_module("pytheory.play")

    score = Score("4/4", bpm=120)
    score.part("lead", synth="sine").add("C4", Duration.QUARTER)
    seen = []

    def fake_render(_score, *, engine=None):
        seen.append(engine)
        return numpy.zeros((16, 2), dtype=numpy.float32)

    monkeypatch.setattr(play_mod, "render_score", fake_render)
    render_scores([score, score], workers=2, engine="pedalboard")
    assert seen == ["pedalboard", "pedalboard"]
