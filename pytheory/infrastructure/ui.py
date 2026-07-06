from __future__ import annotations

import webbrowser


class DefaultBrowserLauncher:
    """Adapter for launching a browser from local desktop workflows."""

    def open(self, url: str) -> None:
        webbrowser.open(url)

