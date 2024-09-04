import functools
import time
from contextlib import contextmanager
from typing import Callable

import libcst as cst


def debug_source_code(node: cst.CSTNode) -> str:
    """Return source code. Useful for debugging."""
    tree = cst.parse_module("")
    tree = tree.with_changes(body=[node])
    return tree.code


@contextmanager
def measure_time(header: str):
    start_time = time.monotonic()
    print(f"==== {header} ====")
    try:
        yield
    finally:
        end_time = time.monotonic()
        print(f"{header} took {end_time - start_time:.4f} seconds")
        print(f"{'=' * (len(header) + 10)}\n")


def measure_fn_time(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        header = func.__name__
        start_time = time.monotonic()
        print(f"==== {header} ====")
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.monotonic()
            print(f"{header} took {end_time - start_time:.4f} seconds")
            print(f"{'=' * (len(header) + 10)}\n")

    return wrapper
