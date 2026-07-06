"""Dependency-free engine selection and plugin registry state."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Mapping

Scalar = int | float | bool | str
ENGINE_NAMES = ("numpy", "pedalboard")


@dataclass(frozen=True)
class PluginSpec:
    path: str
    preset: str | None = None
    plugin_name: str | None = None
    parameters: Mapping[str, Scalar] = field(default_factory=dict)
    initialization_timeout: float = 10.0


@dataclass(frozen=True)
class EffectSpec(PluginSpec):
    mix: float = 1.0


@dataclass(frozen=True)
class DrumkitSpec(PluginSpec):
    note_map: Mapping[int, int] = field(default_factory=dict)


_lock = RLock()
_default_engine = "numpy"
_instrument_registry: dict[str, PluginSpec] = {}
_drumkit_spec: DrumkitSpec | None = None


def _normalize_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve())


def normalize_plugin_spec(
    spec: PluginSpec | EffectSpec | DrumkitSpec | str | Path,
    *,
    preset: str | None = None,
    plugin_name: str | None = None,
    parameters: Mapping[str, Scalar] | None = None,
    initialization_timeout: float = 10.0,
    mix: float | None = None,
    note_map: Mapping[int, int] | None = None,
) -> PluginSpec | EffectSpec | DrumkitSpec:
    if isinstance(spec, DrumkitSpec):
        return DrumkitSpec(
            path=_normalize_path(spec.path),
            preset=spec.preset,
            plugin_name=spec.plugin_name,
            parameters=dict(spec.parameters),
            initialization_timeout=spec.initialization_timeout,
            note_map=dict(spec.note_map),
        )
    if isinstance(spec, EffectSpec):
        return EffectSpec(
            path=_normalize_path(spec.path),
            preset=spec.preset,
            plugin_name=spec.plugin_name,
            parameters=dict(spec.parameters),
            initialization_timeout=spec.initialization_timeout,
            mix=spec.mix,
        )
    if isinstance(spec, PluginSpec):
        return PluginSpec(
            path=_normalize_path(spec.path),
            preset=spec.preset,
            plugin_name=spec.plugin_name,
            parameters=dict(spec.parameters),
            initialization_timeout=spec.initialization_timeout,
        )

    base = dict(parameters or {})
    path_str = _normalize_path(spec)
    if note_map is not None:
        return DrumkitSpec(
            path=path_str,
            preset=preset,
            plugin_name=plugin_name,
            parameters=base,
            initialization_timeout=initialization_timeout,
            note_map=dict(note_map),
        )
    if mix is not None:
        return EffectSpec(
            path=path_str,
            preset=preset,
            plugin_name=plugin_name,
            parameters=base,
            initialization_timeout=initialization_timeout,
            mix=mix,
        )
    return PluginSpec(
        path=path_str,
        preset=preset,
        plugin_name=plugin_name,
        parameters=base,
        initialization_timeout=initialization_timeout,
    )


def validate_engine(engine: str) -> str:
    if engine not in ENGINE_NAMES:
        raise ValueError(
            f"Unknown engine {engine!r}. Expected one of: {', '.join(ENGINE_NAMES)}."
        )
    return engine


def set_engine(engine: str) -> str:
    global _default_engine
    with _lock:
        _default_engine = validate_engine(engine)
        return _default_engine


def get_engine() -> str:
    with _lock:
        return _default_engine


def resolve_engine(engine: str | None) -> str:
    if engine is None:
        return get_engine()
    return validate_engine(engine)


def register_instrument(
    name,
    path,
    *,
    preset=None,
    plugin_name=None,
    parameters=None,
    initialization_timeout=10.0,
):
    spec = normalize_plugin_spec(
        path,
        preset=preset,
        plugin_name=plugin_name,
        parameters=parameters,
        initialization_timeout=initialization_timeout,
    )
    with _lock:
        _instrument_registry[str(name)] = spec
    return spec


def register_drumkit(
    path,
    *,
    preset=None,
    plugin_name=None,
    parameters=None,
    initialization_timeout=10.0,
    note_map=None,
):
    global _drumkit_spec
    spec = normalize_plugin_spec(
        path,
        preset=preset,
        plugin_name=plugin_name,
        parameters=parameters,
        initialization_timeout=initialization_timeout,
        note_map=note_map or {},
    )
    with _lock:
        _drumkit_spec = spec
    return spec


def unregister_instrument(name):
    with _lock:
        _instrument_registry.pop(str(name), None)


def clear_plugin_registry():
    global _drumkit_spec
    with _lock:
        _instrument_registry.clear()
        _drumkit_spec = None


def snapshot_plugin_registry():
    with _lock:
        return dict(_instrument_registry), _drumkit_spec
