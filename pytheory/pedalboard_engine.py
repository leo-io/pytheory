"""Optional pedalboard-based plugin rendering."""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy

from .engines import EffectSpec, PluginSpec, normalize_plugin_spec, snapshot_plugin_registry
from .play import (
    SAMPLE_RATE,
    _apply_chorus,
    _apply_delay,
    _apply_distortion,
    _apply_highpass,
    _apply_lowpass,
    _apply_phaser,
    _apply_reverb_stereo,
    _build_tempo_map,
    _master_bus,
    _pan_to_stereo,
    _render_drums_numpy,
    _render_notes_to_buf,
    _render_part_numpy_dry,
    _score_render_context,
)
from .rhythm import _DrumTone

_WARNED_FEATURES: set[tuple[str, str]] = set()


def _warn_once(part_name, feature):
    key = (part_name, feature)
    if key not in _WARNED_FEATURES:
        warnings.warn(
            f"Part {part_name!r} uses {feature}, which is not fully supported by "
            "the pedalboard engine yet; falling back where possible.",
            stacklevel=3,
        )
        _WARNED_FEATURES.add(key)


def _import_pedalboard():
    try:
        import pedalboard
        import mido
    except ImportError as exc:
        raise ImportError(
            "Pedalboard rendering requires optional dependencies. "
            "Install them with: pip install 'pytheory[pedalboard]'"
        ) from exc
    return pedalboard, mido


def _load_plugin(spec, expected_kind):
    pedalboard, _ = _import_pedalboard()
    spec = normalize_plugin_spec(spec)
    path = Path(spec.path)
    if not path.exists():
        raise FileNotFoundError(f"Plugin not found: {spec.path}")
    try:
        plugin = pedalboard.load_plugin(
            str(path),
            parameter_values=dict(spec.parameters),
            plugin_name=spec.plugin_name,
            initialization_timeout=spec.initialization_timeout,
        )
        if expected_kind == "instrument" and not getattr(plugin, "is_instrument", False):
            raise TypeError(f"Plugin is not an instrument: {spec.path}")
        if expected_kind == "effect" and not getattr(plugin, "is_effect", False):
            raise TypeError(f"Plugin is not an effect: {spec.path}")
        if spec.preset:
            plugin.load_preset(spec.preset)
        plugin.reset()
        return plugin
    except Exception as exc:
        raise RuntimeError(f"Failed to load plugin {spec.path}: {exc}") from exc


def _clamp_midi(value):
    return max(0, min(127, int(value)))


def _message_bytes(status, data1, data2):
    _, mido = _import_pedalboard()
    return bytes(mido.Message.from_bytes([status, data1, data2]).bytes())


def _note_events_to_midi_messages(notes, score, part, *, channel=0):
    tempo_map = _build_tempo_map(score)
    from .play import _beat_to_sample

    events = []
    beat_pos = 0.0
    for note_index, note in enumerate(notes):
        if note.tone is not None and not isinstance(note.tone, _DrumTone):
            start = _beat_to_sample(beat_pos, tempo_map) / SAMPLE_RATE
            end = _beat_to_sample(beat_pos + note.beats, tempo_map) / SAMPLE_RATE
            if hasattr(note.tone, "tones"):
                tones = note.tone.tones
            else:
                tones = [note.tone]
            velocity = _clamp_midi(getattr(note, "velocity", 100))
            for tone in tones:
                midi_note = _clamp_midi(getattr(tone, "midi", 60))
                events.append((_message_bytes(0x90 | channel, midi_note, velocity), start, 1))
                events.append((_message_bytes(0x80 | channel, midi_note, 0), end, 0))
        if not getattr(note, "_hold", False):
            beat_pos += note.beats
    events.sort(key=lambda item: (item[1], item[2]))
    return [(msg, timestamp) for msg, timestamp, _ in events]


def _normalize_audio_output(audio, total_samples):
    arr = numpy.asarray(audio, dtype=numpy.float32)
    if arr.ndim == 1:
        arr = numpy.stack([arr, arr], axis=0)
    if arr.ndim != 2:
        raise ValueError(f"Unexpected plugin output shape: {arr.shape}")
    if arr.shape[0] in (1, 2):
        arr = arr.T
    if arr.shape[1] == 1:
        arr = numpy.repeat(arr, 2, axis=1)
    elif arr.shape[1] > 2:
        arr = arr[:, :2]
    if len(arr) < total_samples:
        padded = numpy.zeros((total_samples, 2), dtype=numpy.float32)
        padded[:len(arr), :arr.shape[1]] = arr
        arr = padded
    elif len(arr) > total_samples:
        arr = arr[:total_samples]
    arr = numpy.nan_to_num(arr, copy=False)
    return numpy.ascontiguousarray(arr.astype(numpy.float32))


def _render_plugin_instrument(spec, notes, score, part, context):
    plugin = _load_plugin(spec, "instrument")
    midi_messages = _note_events_to_midi_messages(notes, score, part)
    audio = plugin(
        midi_messages,
        context.total_samples / SAMPLE_RATE,
        SAMPLE_RATE,
        num_channels=2,
        buffer_size=8192,
    )
    return _normalize_audio_output(audio, context.total_samples)


def _apply_builtin_effects(stereo, part):
    mono = stereo.mean(axis=1).astype(numpy.float32)
    if part.distortion_mix > 0:
        mono = _apply_distortion(mono, mix=part.distortion_mix, drive=part.distortion_drive)
    if part.chorus_mix > 0:
        mono = _apply_chorus(mono, mix=part.chorus_mix, rate=part.chorus_rate, depth=part.chorus_depth)
    if part.phaser_mix > 0:
        mono = _apply_phaser(mono, mix=part.phaser_mix, rate=part.phaser_rate)
    if part.highpass > 0:
        mono = _apply_highpass(mono, part.highpass, q=part.highpass_q)
    if part.lowpass > 0:
        mono = _apply_lowpass(mono, part.lowpass, q=part.lowpass_q)
    if part.delay_mix > 0:
        mono = _apply_delay(mono, mix=part.delay_mix, time=part.delay_time, feedback=part.delay_feedback)
    stereo_out = _pan_to_stereo(mono, part.pan)
    if part.reverb_mix > 0:
        stereo_out = _apply_reverb_stereo(mono, mix=part.reverb_mix, decay=part.reverb_decay)
    return stereo_out * part.volume


def _apply_plugin_effects(stereo, effects):
    out = numpy.ascontiguousarray(stereo.T.astype(numpy.float32))
    for effect_spec in effects:
        spec = effect_spec if isinstance(effect_spec, EffectSpec) else normalize_plugin_spec(effect_spec, mix=1.0)
        plugin = _load_plugin(spec, "effect")
        wet = plugin(out, SAMPLE_RATE, reset=True)
        wet_arr = _normalize_audio_output(wet, stereo.shape[0]).T
        dry_arr = out.T
        mix = max(0.0, min(1.0, spec.mix))
        blended = dry_arr * (1.0 - mix) + wet_arr * mix
        out = numpy.ascontiguousarray(blended.T.astype(numpy.float32))
    return numpy.ascontiguousarray(out.T.astype(numpy.float32))


def _resolve_part_plugin_spec(part, registry):
    if getattr(part, "vst_instrument", None) is not None:
        return part.vst_instrument
    return registry.get(part.synth)


def render_score_pedalboard(score):
    """Render a score with pedalboard plugins where configured."""
    context = _score_render_context(score)
    total_samples = context.total_samples
    stereo_buf = numpy.zeros((total_samples, 2), dtype=numpy.float32)
    instrument_registry, _drumkit_spec = snapshot_plugin_registry()

    if score.notes:
        default_mono = numpy.zeros(total_samples, dtype=numpy.float32)
        from .play import sine_wave, Envelope
        _render_notes_to_buf(
            score.notes, default_mono, context.samples_per_beat, total_samples,
            sine_wave, Envelope.PIANO.value, 0.5, score.bpm,
            swing=score.swing,
            tempo_map=context.tempo_map if context.has_tempo_changes else None,
        )
        stereo_buf += _pan_to_stereo(default_mono, 0.0)

    for part in score.parts.values():
        if not part.notes and not part._drum_hits:
            continue
        if any(getattr(note, "bend", 0.0) for note in part.notes):
            _warn_once(part.name, "pitch bend")
        if getattr(part, "glide", 0.0):
            _warn_once(part.name, "glide")

        spec = _resolve_part_plugin_spec(part, instrument_registry)
        if spec is None:
            part_mono = _render_part_numpy_dry(part, score, context, stereo_buf=stereo_buf)
            if part.reverb_mix > 0:
                stereo_buf += _apply_reverb_stereo(part_mono, mix=part.reverb_mix, decay=part.reverb_decay)
            else:
                stereo_buf += _pan_to_stereo(part_mono, part.pan)
            continue

        if any(isinstance(note.tone, _DrumTone) for note in part.notes):
            _warn_once(part.name, "drum note VST conversion")
            part_mono = _render_part_numpy_dry(part, score, context, stereo_buf=stereo_buf)
            stereo_buf += _pan_to_stereo(part_mono, part.pan)
            continue

        rendered = _render_plugin_instrument(spec, part.notes, score, part, context)
        if getattr(part, "vst_effects", ()):
            rendered = _apply_plugin_effects(rendered, part.vst_effects)
        rendered = _apply_builtin_effects(rendered, part)
        stereo_buf += rendered

    drum_trigger, drum_stereo = _render_drums_numpy(score, context)
    stereo_buf += drum_stereo

    # Keep NumPy sidechain behavior for fallback parts.
    if numpy.any(drum_trigger):
        pass

    return numpy.ascontiguousarray(_master_bus(stereo_buf).astype(numpy.float32))
