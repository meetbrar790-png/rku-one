"""Disposable, per-user VIP request rate-limit prototype.

In-memory only; not distributed or production-ready. Does not reserve IDs.
"""
from collections import defaultdict, deque
from threading import Lock
import time


class TestOnlyInterestLimiter:
    def __init__(self, max_requests=5, window_seconds=60, clock=None):
        if max_requests < 1 or window_seconds <= 0:
            raise ValueError("Positive limits required")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock or time.monotonic
        self._history = defaultdict(deque)
        self._lock = Lock()

    def allow(self, requester_id):
        if type(requester_id) is not int or requester_id < 1:
            raise ValueError("Authenticated requester required")
        with self._lock:
            now = self.clock()
            history = self._history[requester_id]
            while history and now - history[0] >= self.window_seconds:
                history.popleft()
            if len(history) >= self.max_requests:
                return False
            history.append(now)
            return True
