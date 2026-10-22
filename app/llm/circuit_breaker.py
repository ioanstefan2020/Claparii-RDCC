import statistics
import time
from datetime import datetime, timezone
from typing import Literal

CircuitState = Literal["CLOSED", "OPEN", "HALF_OPEN"]


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""

    pass


class CircuitBreaker:
    """Lightweight circuit breaker for protecting external LLM provider calls.

    - CLOSED: Normal operation. Successes reset failure count.
    - OPEN: Tripped after failure_threshold consecutive failures. Calls fail fast for recovery_time_seconds.
    - HALF_OPEN: Cooldown passed; a probe call is attempted.
    """

    def __init__(self, failure_threshold: int = 3, recovery_time_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self._state: CircuitState = "CLOSED"
        self.last_ok: str | None = None
        self.last_error: str | None = None
        self.reason: str | None = None
        self._latencies: list[float] = []

    @property
    def state(self) -> CircuitState:
        if self._state == "OPEN":
            if (
                self.last_failure_time
                and (time.monotonic() - self.last_failure_time)
                >= self.recovery_time_seconds
            ):
                return "HALF_OPEN"
        return self._state

    @property
    def circuit_status(self) -> str:
        s = self.state
        if s == "CLOSED":
            return "closed"
        if s == "OPEN":
            return "open"
        return "half-open"

    @property
    def p50_ms(self) -> int | None:
        if not self._latencies:
            return None
        return int(statistics.median(self._latencies[-20:]))

    def can_execute(self) -> bool:
        s = self.state
        return s in ("CLOSED", "HALF_OPEN")

    def check_available(self) -> None:
        if not self.can_execute():
            raise CircuitBreakerOpenException(
                f"Circuit breaker is OPEN ({self.reason or 'too many consecutive errors'}). Fast failing to prevent cascading errors."
            )

    def record_success(self, latency_ms: float | None = None) -> None:
        self.failure_count = 0
        self._state = "CLOSED"
        self.last_failure_time = None
        self.reason = None
        self.last_ok = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if latency_ms is not None:
            self._latencies.append(latency_ms)
            if len(self._latencies) > 50:
                self._latencies = self._latencies[-50:]

    def record_failure(self, error: str | None = None) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if error:
            self.last_error = error[:200]
        if self.failure_count >= self.failure_threshold:
            self._state = "OPEN"
            self.reason = f"Tripped after {self.failure_count} consecutive failures: {self.last_error or 'error'}"
