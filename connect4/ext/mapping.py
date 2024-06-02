from collections.abc import Mapping


def to_mapping(obj) -> Mapping:
    if isinstance(obj, Mapping):
        return obj

    # For namedtuples
    if hasattr(obj, "_asdict"):
        return obj._asdict()

    return vars(obj)
