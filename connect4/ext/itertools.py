from collections.abc import Iterable
from typing import TypeVar

T = TypeVar(name="T")


def first(iterable: Iterable[T], *, default: T | None = None):
    try:
        value = next(iter(iterable))
    except StopIteration:
        value = default

    return value
