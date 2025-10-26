from __future__ import annotations

import time
from collections import deque
from typing import Deque

from triarb.config import get_settings


class CircuitBreaker:
    def __init__(self, window_seconds: int = 60, max_failures: int = 5):
        self.window = window_seconds
        self.max_failures = max_failures
        self.failures: Deque[float] = deque()

    def record_failure(self) -> None:
        now = time.time()
        self.failures.append(now)
        self._trim(now)

    def _trim(self, now: float) -> None:
        while self.failures and now - self.failures[0] > self.window:
            self.failures.popleft()

    def tripped(self) -> bool:
        self._trim(time.time())
        return len(self.failures) >= self.max_failures


class RiskManager:
    def __init__(self):
        self.settings = get_settings()
        self.breaker = CircuitBreaker()
        self.open_cycles = 0

    def allow_cycle(self, notional: float) -> bool:
        if self.breaker.tripped():
            return False
        if self.open_cycles >= self.settings.max_open_cycles:
            return False
        if notional > self.settings.max_leg_notional_quote:
            return False
        self.open_cycles += 1
        return True

    def release_cycle(self) -> None:
        self.open_cycles = max(0, self.open_cycles - 1)

    def register_failure(self) -> None:
        self.breaker.record_failure()
        self.release_cycle()
