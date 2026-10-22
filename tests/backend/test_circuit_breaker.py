import pytest
from app.llm.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException


def test_circuit_breaker_initial_state():
    cb = CircuitBreaker(failure_threshold=3, recovery_time_seconds=60)
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True


def test_circuit_breaker_trips_to_open():
    cb = CircuitBreaker(failure_threshold=2, recovery_time_seconds=60)
    cb.record_failure()
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True

    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False

    with pytest.raises(CircuitBreakerOpenException):
        cb.check_available()


def test_circuit_breaker_resets_on_success():
    cb = CircuitBreaker(failure_threshold=2, recovery_time_seconds=60)
    cb.record_failure()
    assert cb.failure_count == 1
    cb.record_success()
    assert cb.failure_count == 0
    assert cb.state == "CLOSED"
