import time
from typing import Callable, TypeVar

T = TypeVar("T")


def print_elapsed(start: float, *args, **kwargs):
    elapsed = time.time() - start
    print(f"[{elapsed:.1f}s]", *args, **kwargs)


def group_by(xs: list[T], key: Callable[[T], str]) -> dict[str, list[T]]:
    result: dict[str, list[T]] = dict()

    for x in xs:
        k = key(x)
        result.setdefault(k, [])
        result[k].append(x)

    return result
