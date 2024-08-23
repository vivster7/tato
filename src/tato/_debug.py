import time
from contextlib import contextmanager

import libcst as cst


def _debug_source_code(node: cst.CSTNode) -> str:
    """Return source code. Useful for debugging."""
    tree = cst.parse_module("")
    tree = tree.with_changes(body=[node])
    return tree.code


@contextmanager
def _measure_time(header: str):
    start_time = time.monotonic()
    print(f"==== {header} ====")
    try:
        yield
    finally:
        end_time = time.monotonic()
        print(f"{header} took {end_time - start_time:.4f} seconds")
        print(f"{'=' * (len(header) + 10)}\n")
