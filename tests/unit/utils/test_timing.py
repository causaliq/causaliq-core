"""
Test the Timing class.

Migrated from legacy/core/test/test_timing.py with exact functionality
preservation and added tests for 100% coverage.
"""

from time import sleep, time
from unittest.mock import patch

import pytest

from causaliq_core.utils.timing import (
    TimeoutError,
    Timing,
    run_with_timeout,
    with_timeout,
)

TOO_LONG = "".join(["*"] * (Timing.MAX_ACTION_LEN + 1))


@pytest.fixture(scope="module")  # Ensure timing enabled with module fixture
def on():
    filter = {"ok_1", "ok_2", "ok_3a", "ok_3b"}
    Timing.on(True, filter)

    # Have to directly set filter to include illegal action type/values
    # so that can test for the relevant exceptions

    Timing.filter = filter | {"error", None, False, 2, "", TOO_LONG}
    return Timing.filter


# Test on() function


def test_timing_on_type_error_1_(on):  # no arguments
    with pytest.raises(TypeError):
        Timing.on()


def test_timing_on_type_error_2_(on):  # bad type for active
    with pytest.raises(TypeError):
        Timing.on(1)
    with pytest.raises(TypeError):
        Timing.on([False])
    with pytest.raises(TypeError):
        Timing.on("False")
    with pytest.raises(TypeError):
        Timing.on(None, set())


def test_timing_on_type_error_3_(on):  # bad type for filter
    with pytest.raises(TypeError):
        Timing.on(True, filter=False)
    with pytest.raises(TypeError):
        Timing.on(True, filter="invalid")
    with pytest.raises(TypeError):
        Timing.on(True, filter=["invalid"])


def test_timing_on_ok_1_(on):  # fixture should ensure timing on
    assert Timing.active is True
    assert Timing.filter == on


# Test now() function


def test_timing_now_type_error_1_(on):  # no arguments expected
    with pytest.raises(TypeError):
        Timing.now(False)


def test_timing_now_ok_1_(on):  # check return is as expected
    before = time()
    sleep(1.0)
    now = Timing.now()
    assert isinstance(now, float)
    assert now >= before + 1.0


# Test record() function


def test_timing_record_type_error_1_(on):  # no arguments specified
    with pytest.raises(TypeError):
        Timing.record()


def test_timing_record_type_error_2_(on):  # insufficient arguments
    with pytest.raises(TypeError):
        Timing.record("error", 0)
    with pytest.raises(TypeError):
        Timing.record("error", 0)


def test_timing_record_type_error_3_(on):  # bad action type
    with pytest.raises(TypeError):
        Timing.record(None, 0, time())
    with pytest.raises(TypeError):
        Timing.record(False, 0, time())
    with pytest.raises(TypeError):
        Timing.record(2, 0, time())


def test_timing_record_type_error_4_(on):  # bad scale type
    with pytest.raises(TypeError):
        Timing.record("error", None, time())
    with pytest.raises(TypeError):
        Timing.record("error", False, time())
    with pytest.raises(TypeError):
        Timing.record("error", "invalid", time())
    with pytest.raises(TypeError):
        Timing.record("error", 2.3, time())


def test_timing_record_type_error_5_(on):  # bad start type
    with pytest.raises(TypeError):
        Timing.record("error", 1, None)
    with pytest.raises(TypeError):
        Timing.record("error", 1, 1)
    with pytest.raises(TypeError):
        Timing.record("error", 1, False)
    with pytest.raises(TypeError):
        Timing.record("error", 1, "invalid")
    with pytest.raises(TypeError):
        Timing.record("error", 1, [32.5])


def test_timing_record_value_error_1_(on):  # bad action length
    with pytest.raises(ValueError):
        Timing.record("", 1, time())
    with pytest.raises(ValueError):
        Timing.record(TOO_LONG, 1, time())


def test_timing_record_ok_1_(on):  # record single action of one class
    start = time()
    sleep(0.1)
    Timing.record("ok_1", 0, start)

    print("\n\nok_1 timings are:\n{}".format(Timing.to_string({"ok_1"})))

    assert "ok_1" in Timing.times
    assert 0 in Timing.times["ok_1"]
    assert Timing.times["ok_1"][0]["count"] == 1
    assert Timing.times["ok_1"][0]["total"] == Timing.times["ok_1"][0]["max"]


def test_timing_record_ok_2_(on):  # record single action with different scales
    start = time()
    sleep(0.05)
    Timing.record("ok_2", 1, start)
    sleep(0.03)
    Timing.record("ok_2", 0, start)
    sleep(0.01)
    Timing.record("ok_2", 1, start)

    print("\n\nok_2 timings are:\n{}".format(Timing.to_string({"ok_2"})))

    assert "ok_2" in Timing.times
    assert 0 in Timing.times["ok_2"]
    assert Timing.times["ok_2"][0]["count"] == 1
    assert Timing.times["ok_2"][0]["total"] == Timing.times["ok_2"][0]["max"]
    assert Timing.times["ok_2"][1]["count"] == 2


def test_timing_record_ok_3_(on):  # record different actions
    start = time()
    sleep(0.05)
    Timing.record("ok_3b", 1, start)
    sleep(0.03)
    Timing.record("ok_3b", 0, start)
    sleep(0.01)
    Timing.record("ok_3a", 1, start)
    sleep(0.03)
    Timing.record("ok_3b", 0, start)

    print(
        "\n\nok_3 timings are:\n{}".format(
            Timing.to_string({"ok_3a", "ok_3b"})
        )
    )

    assert "ok_3a" in Timing.times
    assert "ok_3b" in Timing.times
    assert set(Timing.times["ok_3a"]) == {1}
    assert set(Timing.times["ok_3b"]) == {0, 1}
    assert Timing.times["ok_3a"][1]["count"] == 1
    assert Timing.times["ok_3a"][1]["total"] == Timing.times["ok_3a"][1]["max"]
    assert Timing.times["ok_3b"][0]["count"] == 2
    assert Timing.times["ok_3b"][1]["count"] == 1
    assert Timing.times["ok_3b"][1]["total"] == Timing.times["ok_3b"][1]["max"]


# Test missing functionality for 100% coverage


def test_timing_off():
    """Test the off() method."""
    # Set up some state first
    Timing.on(True, {"test"})
    Timing.add("test", 0.1)

    # Verify state exists
    assert Timing.active is True
    assert Timing.times != {}
    assert Timing.filter is not None

    # Turn off
    Timing.off()

    # Verify everything is reset
    assert Timing.active is False
    assert Timing.times == {}
    assert Timing.filter is None


def test_timing_add():
    """Test the add() method."""
    Timing.on(True)

    # Add some elapsed time
    Timing.add("add_test", 0.5, 100)

    # Verify it was recorded
    assert "add_test" in Timing.times
    assert 100 in Timing.times["add_test"]
    assert Timing.times["add_test"][100]["count"] == 1
    # The elapsed time should be approximately 0.5
    assert abs(Timing.times["add_test"][100]["total"] - 0.5) < 0.1


def test_timing_now_active():
    """Test now() when timing is active."""
    Timing.on(True)
    before = time()
    result = Timing.now()
    after = time()

    assert result is not None
    assert before <= result <= after


def test_timing_now_inactive():
    """Test now() when timing is inactive."""
    Timing.off()
    result = Timing.now()
    assert result is None


def test_timing_record_inactive():
    """Test record() when timing is inactive."""
    Timing.off()
    start = time()
    result = Timing.record("test", 100, start)

    # Should return None and not record anything
    assert result is None
    assert "test" not in Timing.times


def test_timing_record_filtered_out():
    """Test record() when action is filtered out."""
    Timing.on(True, {"allowed"})
    start = time()
    result = Timing.record("not_allowed", 100, start)

    # Should return None and not record anything
    assert result is None
    assert "not_allowed" not in Timing.times


def test_timing_to_string_inactive():
    """Test to_string() when timing is inactive."""
    Timing.off()
    result = Timing.to_string()

    expected = "\n\nTiming was not enabled.\n"
    assert result == expected


def test_timing_to_string_filter_error():
    """Test to_string() with invalid filter parameter."""
    Timing.on(True)

    # Test various invalid filter types
    with pytest.raises(TypeError):
        Timing.to_string(filter="invalid")

    with pytest.raises(TypeError):
        Timing.to_string(filter=["invalid"])

    with pytest.raises(TypeError):
        Timing.to_string(filter={"valid", 123})  # mixed types in set


def test_timing_to_string_multiple_scales():
    """Test to_string() output with multiple scales for same action."""
    Timing.on(True)

    # Add multiple scales for same action (use short name for MAX_ACTION_LEN)
    Timing.add("test", 0.1, 10)
    Timing.add("test", 0.2, 20)
    Timing.add("test", 0.3, 10)  # Second entry for scale 10

    result = Timing.to_string()

    # Should include "ALL" summary row
    assert "ALL" in result
    assert "test" in result


def test_timing_repr():
    """Test __repr__ method."""
    Timing.on(True)
    Timing.add("repr_test", 0.1)

    # Should return same as to_string()
    repr_result = Timing.__repr__()
    to_string_result = Timing.to_string()

    assert repr_result == to_string_result


# Timeout functionality tests


def test_run_with_timeout_no_timeout():
    """Test run_with_timeout with no timeout specified."""

    def simple_func(x, y):
        return x + y

    result = run_with_timeout(simple_func, (5, 3), timeout_seconds=None)
    assert result == 8


def test_run_with_timeout_success():
    """Test run_with_timeout that completes within timeout."""

    def quick_func():
        sleep(0.1)
        return "completed"

    result = run_with_timeout(quick_func, timeout_seconds=1)
    assert result == "completed"


def test_run_with_timeout_with_args_kwargs():
    """Test run_with_timeout with args and kwargs."""

    def complex_func(a, b, c=None, d=10):
        return a + b + (c or 0) + d

    result = run_with_timeout(
        complex_func, args=(1, 2), kwargs={"c": 3, "d": 4}, timeout_seconds=1
    )
    assert result == 10


def test_run_with_timeout_raises_exception():
    """Test run_with_timeout when function raises an exception."""

    def failing_func():
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        run_with_timeout(failing_func, timeout_seconds=1)


def test_run_with_timeout_timeout_error():
    """Test run_with_timeout when timeout occurs."""

    def slow_func():
        sleep(2)
        return "should not reach here"

    with pytest.raises(
        TimeoutError, match="Algorithm execution exceeded 0.5 seconds"
    ):
        run_with_timeout(slow_func, timeout_seconds=0.5)


def test_run_with_timeout_invalid_timeout():
    """Test run_with_timeout with invalid timeout value."""

    def dummy_func():
        return "test"

    with pytest.raises(ValueError, match="Timeout must be positive"):
        run_with_timeout(dummy_func, timeout_seconds=0)

    with pytest.raises(ValueError, match="Timeout must be positive"):
        run_with_timeout(dummy_func, timeout_seconds=-1)


def test_with_timeout_decorator():
    """Test with_timeout decorator."""

    @with_timeout(1)
    def decorated_func(x):
        return x * 2

    result = decorated_func(5)
    assert result == 10


def test_with_timeout_decorator_timeout():
    """Test with_timeout decorator with timeout."""

    @with_timeout(0.5)
    def slow_decorated_func():
        sleep(2)
        return "should not reach"

    with pytest.raises(TimeoutError):
        slow_decorated_func()


def test_with_timeout_decorator_no_timeout():
    """Test with_timeout decorator with None timeout."""

    @with_timeout(None)
    def no_timeout_func():
        sleep(0.1)
        return "completed"

    result = no_timeout_func()
    assert result == "completed"


def test_timeout_error_exception():
    """Test TimeoutError exception class."""
    # Test that it's properly defined and can be raised
    with pytest.raises(TimeoutError):
        raise TimeoutError("test timeout")

    # Test inheritance
    assert issubclass(TimeoutError, Exception)


def test_run_with_timeout_edge_case():
    """Test edge case where thread completes but no result/exception found."""
    # This is an unlikely edge case but we need to test it for 100% coverage
    with patch("causaliq_core.utils.timing.queue.Queue") as mock_queue_class:
        # Create mock queues that appear empty even after function execution
        mock_result_queue = mock_queue_class.return_value
        mock_exception_queue = mock_queue_class.return_value
        mock_result_queue.empty.return_value = True
        mock_exception_queue.empty.return_value = True

        def simple_func():
            return "test"

        # This should trigger the RuntimeError for 100% coverage
        with pytest.raises(
            RuntimeError,
            match="Thread completed but no result or exception found",
        ):
            run_with_timeout(simple_func, timeout_seconds=1)
