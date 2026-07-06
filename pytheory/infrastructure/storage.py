from __future__ import annotations

import os
import threading


class InMemoryScoreRepository:
    """Thread-safe in-memory store used by lightweight local apps."""

    def __init__(self) -> None:
        self._scores: dict[str, object] = {}
        self._counter = 0
        self._lock = threading.Lock()

    def store(self, score) -> str:
        with self._lock:
            self._counter += 1
            score_id = f"s{self._counter}-{os.urandom(4).hex()}"
            self._scores[score_id] = score
            return score_id

    def get(self, score_id: str):
        with self._lock:
            return self._scores.get(score_id)

