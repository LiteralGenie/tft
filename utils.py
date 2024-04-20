import time
from functools import wraps


def print_elapsed(start: float, *args, **kwargs):
    elapsed = time.time() - start
    print(f"[{elapsed:.1f}s]", *args, **kwargs)
