# PyTheory Architecture

PyTheory now has an explicit layered structure so the musical model can stay stable while delivery and infrastructure concerns evolve.

## Layers

- `pytheory.domain`
  Exposes the core musical objects in one place: tones, systems, scales, chords, rhythm, scores, and related value objects.

- `pytheory.application`
  Hosts use-case services such as playback orchestration and Studio transcription flows. These modules coordinate work but do not own low-level I/O details.

- `pytheory.ports`
  Defines the extension boundaries for audio loading, transcription, playback, score rendering, browser launching, and score storage. Registries make it easy to swap implementations at runtime.

- `pytheory.infrastructure`
  Contains the default adapters that preserve current behavior by delegating to the existing synthesis, transcription, and browser tooling.

## Extension Points

The active backend can be replaced without patching the domain model:

```python
from pytheory.ports import register_audio_loader, register_score_renderer

register_audio_loader(MyLibsndfileLoader())
register_score_renderer(MyRealtimeRenderer())
```

Useful targets for customization:

- alternate audio converters or import libraries
- new playback engines
- GUI/browser launch integrations
- external score repositories for apps or services

## Compatibility

The flat public API remains available. Existing imports like `pytheory.Tone`, `pytheory.Score`, and `pytheory.play()` still work, while new code can prefer `pytheory.model` or `pytheory.domain`.
