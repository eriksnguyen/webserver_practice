from typing import TypeVar


class _Undefined:
    def __repr__(self):
        return "UNDEFINED"


UNDEFINED = _Undefined()
T = TypeVar("T")


def coalesce_undefined(obj: T | _Undefined, default: T) -> T:
    return obj if not isinstance(obj, _Undefined) else default
