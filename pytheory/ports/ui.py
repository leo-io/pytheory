from __future__ import annotations

from typing import Protocol


class BrowserLauncher(Protocol):
    """Open a URL with the active UI/browser integration."""

    def open(self, url: str) -> None:
        ...

