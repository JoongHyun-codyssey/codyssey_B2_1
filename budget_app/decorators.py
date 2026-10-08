from functools import wraps
from time import perf_counter
from typing import Callable, TypeVar

ReturnT = TypeVar("ReturnT")


def measure_time(func: Callable[[], ReturnT]) -> Callable[[], ReturnT]:
    @wraps(func)
    def wrapper() -> ReturnT:
        start = perf_counter()

        try:
            return func()
        finally:
            elapsed = perf_counter() - start
            print(f"[실행 시간] {elapsed:.3f}초")

    return wrapper
