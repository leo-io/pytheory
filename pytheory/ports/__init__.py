"""Ports and registries for pluggable PyTheory infrastructure."""

from ._registry import BackendRegistry
from .audio import AudioConverter, AudioLoader, AudioPlayer, AudioTranscriber
from .rendering import ScoreRenderer
from .storage import ScoreRepository
from .ui import BrowserLauncher


def _default_audio_loader():
    from ..infrastructure.importers import DefaultAudioLoader

    return DefaultAudioLoader()


def _default_audio_transcriber():
    from ..infrastructure.audio import DefaultAudioTranscriber

    return DefaultAudioTranscriber()


def _default_audio_player():
    from ..infrastructure.audio import DefaultAudioPlayer

    return DefaultAudioPlayer()


def _default_score_renderer():
    from ..infrastructure.rendering import DefaultScoreRenderer

    return DefaultScoreRenderer()


def _default_score_repository():
    from ..infrastructure.storage import InMemoryScoreRepository

    return InMemoryScoreRepository()


def _default_browser_launcher():
    from ..infrastructure.ui import DefaultBrowserLauncher

    return DefaultBrowserLauncher()


_audio_loader_registry = BackendRegistry(_default_audio_loader)
_audio_transcriber_registry = BackendRegistry(_default_audio_transcriber)
_audio_player_registry = BackendRegistry(_default_audio_player)
_score_renderer_registry = BackendRegistry(_default_score_renderer)
_score_repository_registry = BackendRegistry(_default_score_repository)
_browser_launcher_registry = BackendRegistry(_default_browser_launcher)


def get_audio_loader() -> AudioLoader:
    return _audio_loader_registry.get()


def register_audio_loader(loader: AudioLoader) -> AudioLoader:
    return _audio_loader_registry.register(loader)


def get_audio_transcriber() -> AudioTranscriber:
    return _audio_transcriber_registry.get()


def register_audio_transcriber(transcriber: AudioTranscriber) -> AudioTranscriber:
    return _audio_transcriber_registry.register(transcriber)


def get_audio_player() -> AudioPlayer:
    return _audio_player_registry.get()


def register_audio_player(player: AudioPlayer) -> AudioPlayer:
    return _audio_player_registry.register(player)


def get_score_renderer() -> ScoreRenderer:
    return _score_renderer_registry.get()


def register_score_renderer(renderer: ScoreRenderer) -> ScoreRenderer:
    return _score_renderer_registry.register(renderer)


def get_score_repository() -> ScoreRepository:
    return _score_repository_registry.get()


def register_score_repository(repository: ScoreRepository) -> ScoreRepository:
    return _score_repository_registry.register(repository)


def get_browser_launcher() -> BrowserLauncher:
    return _browser_launcher_registry.get()


def register_browser_launcher(launcher: BrowserLauncher) -> BrowserLauncher:
    return _browser_launcher_registry.register(launcher)


__all__ = [
    "AudioConverter",
    "AudioLoader",
    "AudioPlayer",
    "AudioTranscriber",
    "BrowserLauncher",
    "ScoreRenderer",
    "ScoreRepository",
    "get_audio_loader",
    "get_audio_player",
    "get_audio_transcriber",
    "get_browser_launcher",
    "get_score_renderer",
    "get_score_repository",
    "register_audio_loader",
    "register_audio_player",
    "register_audio_transcriber",
    "register_browser_launcher",
    "register_score_renderer",
    "register_score_repository",
]

