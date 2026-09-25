from functools import wraps
from time import perf_counter
from typing import Callable


def measure_time(func: Callable[[], None]) -> Callable[[], None]:
    @wraps(func)
    def wrapper() -> None:
        start = perf_counter()

        try:
            return func()
        finally:
            elapsed = perf_counter() - start
            print(f"[실행 시간] {elapsed:.3f}초")

    return wrapper