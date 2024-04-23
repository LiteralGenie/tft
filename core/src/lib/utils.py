import time
from copy import deepcopy
from math import ceil
from typing import Any, Callable, TypeVar

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


def to_n_batches(xs: list[T], n_batches: int) -> list[list[T]]:
    max_chunk_size = ceil(len(xs) / n_batches)

    chunks = []
    for idx in range(n_batches):
        start = idx * max_chunk_size
        end = start + max_chunk_size
        chunks.append(xs[start:end])

    return chunks


def to_batch_size(xs: list[T], batch_size: int) -> list[list[T]]:
    n_batches = ceil(len(xs) / batch_size)
    return to_n_batches(xs, n_batches)


MAX_PARAMS_PER_INSERT = 65_000


def batch_queries(
    xs: list[T],
    to_val: Callable[[T], str],
    to_params: Callable[[T], list | tuple],
) -> list[dict[str, Any]]:
    batches = []

    vals, params = ([], [])
    for x in xs:
        v = to_val(x)
        ps = to_params(x)

        if len(ps) + len(params) > MAX_PARAMS_PER_INSERT:
            batches.append(dict(vals=", ".join(vals), params=params))
            vals, params = ([v], [*ps])
        else:
            vals.append(v)
            params.extend(ps)

    if params:
        batches.append(dict(vals=", ".join(vals), params=params))

    return batches
