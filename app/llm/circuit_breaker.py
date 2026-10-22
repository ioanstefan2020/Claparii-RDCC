import time
from typing import Literal

CircuitState = Literal["CLOSED", "OPEN", "HALF_OPEN"]


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""

    pass


class CircuitBreaker:
    """
    Lightweight circuit breaker for protecting external LLM provider calls.
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

    def can_execute(self) -> bool:
        s = self.state
        return s in ("CLOSED", "HALF_OPEN")

    def check_available(self) -> None:
        if not self.can_execute():
            raise CircuitBreakerOpenException(
                f"Circuit breaker is OPEN. Fast failing to prevent cascading errors."
            )

    def record_success(self) -> None:
        self.failure_count = 0
        self._state = "CLOSED"
        self.last_failure_time = None

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self._state = "OPEN"
