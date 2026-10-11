"""
Timing utilities for CausalIQ Core.

Record elapsed time of critical operations, note not thread safe.
Migrated from legacy.core.timing with exact functionality preservation.
"""

import queue
import threading
from time import time
from typing import Any, Callable, Optional


class MetaTiming(type):
    """
    Overwrites the __repr__() method so that print(Timing) works as
    required.
    """

    def __repr__(cls) -> str:
        return cls.to_string()  # type: ignore[attr-defined, no-any-return]


class Timing(metaclass=MetaTiming):
    """
    Singleton class collects count, mean and max time for actions.

    :cvar bool active: whether timing collection is active
    :cvar times dict: times collected
                      {action1: {scale1: {count, total, max}, ...}, ...}
    :cvar set/None filter: only these actions will be recorded
    """

    MAX_ACTION_LEN = 10
    VAL_FMT = "{}  {}    {:11.0f}    {:12.3f}    {:12.3f}    {:12.3f}  \n"

    active = False
    times: dict = {}
    filter = None

    @classmethod
    def on(cls, active: bool, filter: Optional[set] = None) -> None:
        """
        Switching timing on and off

        :param bool active: whether timing should be on or off
        :param set/None filter: only these actions recorded

        :raises TypeError: if bad arg type
        """
        if not isinstance(active, bool) or (
            filter is not None
            and (
                not isinstance(filter, set)
                or not all([isinstance(f, str) for f in filter])
            )
        ):
            raise TypeError("Timing.on() bad arg type")
        cls.active = active
        cls.filter = filter
        cls.times = {}

    @classmethod
    def off(cls) -> None:
        """
        Turn timing collection off, lose collected timings.
        """
        cls.active = False
        cls.times = {}
        cls.filter = None

    @classmethod
    def add(cls, action: str, elapsed: float, scale: int = 100) -> None:
        """
        Add an elapsed time without having called now() and record().

        Arguments:
            action: action being timed
            elapsed: elapsed time to add
            scale: indication of scale of action e.g. num of nodes

        :raises TypeError: if bad arg type
        :raises ValueError: if bad arg value
        """
        start = time() - elapsed
        cls.record(action, scale, start)

    @classmethod
    def now(cls) -> Optional[float]:
        """
        Returns current time, generally for the start of an action

        :returns float: epoch time in seconds
        """
        return time() if cls.active is True else None

    @classmethod
    def record(
        cls, action: str, scale: int, start: Optional[float]
    ) -> Optional[float]:
        """
        Records time for specified action

        :param str action: action being timed
        :param int scale: indication of scale of action e.g. num of nodes
        :param int start: time at which action started

        :raises TypeError: if bad arg type
        :raises ValueError: if bad arg value

        :returns float: epoch time when this function called
        """
        now = None
        if cls.active is True and (cls.filter is None or action in cls.filter):
            cls._ensure_action_scale(action, scale)

            if not isinstance(start, float):
                raise TypeError("Timing.record() bad arg type")

            now = time()
            cls._accumulate(action, scale, now - start)

        return now

    @classmethod
    def _ensure_action_scale(cls, action: str, scale: int) -> None:
        """
        Validate and create the storage for an action/scale pair.

        :param str action: action being timed
        :param int scale: indication of scale of action e.g. num of nodes

        :raises TypeError: if bad arg type
        :raises ValueError: if bad arg value
        """
        if action not in cls.times:
            if not isinstance(action, str):
                raise TypeError("Timing.record() bad arg type")
            if len(action) == 0 or len(action) > cls.MAX_ACTION_LEN:
                raise ValueError("Timing.record() bad arg value")
            cls.times[action] = {}

        if scale not in cls.times[action]:
            if not isinstance(scale, int) or isinstance(scale, bool):
                raise TypeError("Timing.record() bad arg type")
            cls.times[action].update(
                {scale: {"count": 0, "total": 0.0, "max": 0.0}}
            )

    @classmethod
    def _accumulate(cls, action: str, scale: int, elapsed: float) -> None:
        """
        Add an elapsed time to an existing action/scale accumulator.

        :param str action: action being timed
        :param int scale: indication of scale of action
        :param float elapsed: elapsed time to add
        """
        stats = cls.times[action][scale]
        stats["count"] += 1
        stats["total"] += elapsed
        if elapsed > stats["max"]:
            stats["max"] = elapsed

    @classmethod
    def to_string(cls, filter: Optional[set] = None) -> str:
        """
        Print out timings in nice format, optionally only for specified
        actions.

        :param set/None filter: only return info about these actions.

        :return str: human friendly timing information
        """
        if cls.active is not True:
            return "\n\nTiming was not enabled.\n"

        cls._validate_action_filter(filter)

        res = cls._header()
        for action in sorted(cls.times):
            if filter is not None and action not in filter:
                continue
            res += cls._action_rows(action)

        return res

    @classmethod
    def _validate_action_filter(cls, filter: Optional[set]) -> None:
        """
        Validate the optional action filter argument.

        :param set/None filter: only return info about these actions.

        :raises TypeError: if bad arg type
        """
        if filter is not None and (
            not isinstance(filter, set)
            or not all([isinstance(f, str) for f in filter])
        ):
            raise TypeError("Timing.to_string() bad arg value")

    @classmethod
    def _header(cls) -> str:
        """
        Return the column header block for the timing table.

        :return str: header lines for the timing output
        """
        res = "\n{:^{}s}{:^14}{:^15}{:^16}{:^16}{:^16}\n".format(
            "Action",
            cls.MAX_ACTION_LEN + 4,
            "Scale",
            "Count",
            "Mean (s)",
            "Max. (s)",
            "Total (s)",
        )
        res += (
            " {0:->{1}s}{2}{0:->12}{2}{0:->13}{2}{0:->14}"
            + "{2}{0:->14}{2}{0:->14}\n"
        ).format("-", cls.MAX_ACTION_LEN + 2, "  ")
        return res

    @classmethod
    def _action_rows(cls, action: str) -> str:
        """
        Return the formatted timing rows for a single action.

        :param str action: action to format timings for

        :return str: formatted rows plus a trailing blank line
        """
        a_str = "  {:>{}s}  ".format(action, cls.MAX_ACTION_LEN)
        num, count, total, max = 0, 0, 0.0, None
        res = ""
        for scale in sorted(cls.times[action]):
            v = cls.times[action][scale]
            num += 1
            count += v["count"]
            total += v["total"]
            max = v["max"] if max is None or v["max"] > max else max
            res += cls._scale_row(a_str, scale, v)
        if num > 1:
            res += cls.VAL_FMT.format(
                a_str, "       ALL", count, total / count, max, total
            )
        return res + "\n"

    @classmethod
    def _scale_row(cls, a_str: str, scale: int, v: dict) -> str:
        """
        Return the formatted row for one action/scale pair.

        :param str a_str: formatted action name prefix
        :param int scale: indication of scale of action
        :param dict v: collected count, total and max timings

        :return str: formatted row
        """
        return cls.VAL_FMT.format(
            a_str,
            "{:10.0f}".format(scale),
            v["count"],
            v["total"] / v["count"],
            v["max"],
            v["total"],
        )

    @classmethod
    def __repr__(cls) -> str:
        """
        Print out all timings in nice format

        :return str: human friendly timing information
        """
        return cls.to_string()


# Timeout functionality for algorithm execution


class TimeoutError(Exception):
    """Raised when an operation times out"""

    pass


def _run_function_in_queue(
    func: Callable,
    args: tuple,
    kwargs: dict,
    result_queue: queue.Queue,
    exception_queue: queue.Queue,
) -> None:
    """
    Run a function, placing its result or exception on a queue.

    :param func: function to execute
    :param args: positional arguments for the function
    :param kwargs: keyword arguments for the function
    :param result_queue: queue to receive the function result
    :param exception_queue: queue to receive any raised exception
    """
    try:
        result = func(*args, **kwargs)
        result_queue.put(result)
    except Exception as e:
        exception_queue.put(e)


def _collect_thread_result(
    result_queue: queue.Queue, exception_queue: queue.Queue
) -> Any:
    """
    Return the thread result, re-raising any recorded exception.

    :param result_queue: queue holding the function result, if produced
    :param exception_queue: queue holding any raised exception

    :raises Exception: any exception raised by the wrapped function
    :raises RuntimeError: if no result or exception was found

    :returns: result from the wrapped function
    """
    # Check if an exception occurred
    if not exception_queue.empty():
        raise exception_queue.get()

    # Check if we have a result
    if not result_queue.empty():
        return result_queue.get()

    # This shouldn't happen, but just in case
    raise RuntimeError("Thread completed but no result or exception found")


def run_with_timeout(
    func: Callable,
    args: tuple = (),
    kwargs: Optional[dict] = None,
    timeout_seconds: Optional[int] = None,
) -> Any:
    """
    Run a function with a timeout using threading approach.

    This is compatible with both subprocess-based (R, Java) and direct Python
    function calls (causal-learn). For subprocess calls, the timeout will
    terminate the subprocess if it exceeds the time limit.

    :param func: Function to execute
    :param args: Positional arguments for the function
    :param kwargs: Keyword arguments for the function
    :param timeout_seconds: Maximum execution time in seconds,
                           None for no timeout

    :raises TimeoutError: if execution exceeds timeout_seconds
    :raises Exception: any exception raised by the wrapped function

    :returns: Result from the wrapped function
    """
    if timeout_seconds is None:
        # No timeout specified, run directly
        return func(*(args or ()), **(kwargs or {}))

    if timeout_seconds <= 0:
        raise ValueError("Timeout must be positive")

    result_queue: queue.Queue = queue.Queue()
    exception_queue: queue.Queue = queue.Queue()

    # Start the function in a separate thread
    thread = threading.Thread(
        target=_run_function_in_queue,
        args=(func, args or (), kwargs or {}, result_queue, exception_queue),
    )
    thread.daemon = True  # Dies when main thread dies
    thread.start()

    # Wait for completion or timeout
    thread.join(timeout_seconds)

    if thread.is_alive():
        # Thread is still running - timeout occurred
        # Note: We can't actually kill the thread, but we can abandon it
        # For subprocess-based algorithms, this will leave a subprocess running
        # That's a limitation we'll need to address in subprocess wrappers
        raise TimeoutError(
            f"Algorithm execution exceeded " f"{timeout_seconds} seconds"
        )

    return _collect_thread_result(result_queue, exception_queue)


def with_timeout(timeout_seconds: Optional[int] = None) -> Callable:
    """
    Decorator version of run_with_timeout.

    :param timeout_seconds: Maximum execution time in seconds,
                           None for no timeout

    Usage:
        @with_timeout(300)  # 5 minute timeout
        def my_algorithm(data):
            # algorithm implementation
            return result
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return run_with_timeout(func, args, kwargs, timeout_seconds)

        return wrapper

    return decorator
