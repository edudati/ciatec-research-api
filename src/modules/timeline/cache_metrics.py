"""In-process counters for timeline list cache hits and misses."""

from __future__ import annotations

import threading


class TimelineCacheMetrics:
    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()

    def record_hit(self) -> None:
        with self._lock:
            self.hits += 1

    def record_miss(self) -> None:
        with self._lock:
            self.misses += 1

    def snapshot(self) -> tuple[int, int]:
        with self._lock:
            return self.hits, self.misses

    def reset_for_tests(self) -> None:
        with self._lock:
            self.hits = 0
            self.misses = 0


timeline_cache_metrics = TimelineCacheMetrics()
