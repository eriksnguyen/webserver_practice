"""
Introduces helper mixins for dataclasses. The primary mixin of import is `SerializeMixin` which helps
with serializing and deserializing dataclasses to and from JSON representations.

NOTE: This module is written expecting python 3.11+ because of use of `Self`

To convert to Python 3.10+, utilize
```
R = TypeVar("R", bound="Replaceable")
S = TypeVar("S", bound="Serializable")
```

Converting to Python 3.9+ is possible, and involves deleting a lot of type manipulation
that's done below.
"""

import abc
import dataclasses
import re
from collections import OrderedDict
from collections.abc import Callable, Mapping
from pathlib import Path
from types import GenericAlias, NoneType, UnionType
from typing import Any, List, Self, Union, get_args, get_origin, overload

from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper

from connect4.ext.itertools import first
from connect4.ext.mapping import to_mapping
from connect4.ext.typing import fully_qualified_type
from connect4.ext.undefined import UNDEFINED, coalesce_undefined

FieldFilter = Callable[[str, Any], bool]

_default_field_filter: FieldFilter = lambda _, value: value is not None


def _robust_is_subclass(maybe_cls, cls_or_cls_tuple):
    try:
        return issubclass(maybe_cls, cls_or_cls_tuple)
    except TypeError as e:
        # This is triggered with type alias like typing.Dict
        if e.args == ("issubclass() arg 1 must be a class",):
            return False

        raise


def _robust_is_instance(instance, maybe_subscripted_generic):
    # Subscripted generics (e.g. typing.List[int] and list[int]) have origins of `list`
    origin = get_origin(maybe_subscripted_generic)
    if origin is not None:
        return isinstance(instance, origin)

    return isinstance(instance, maybe_subscripted_generic)


class Replaceable(abc.ABC):
    @abc.abstractmethod
    def replace(self: Self, **kwargs) -> Self:
        """
        Creates a new object of the same type as `self`, replacing fields with values from `kwargs`.
        """
        raise NotImplementedError


class ReplaceMixin(Replaceable):
    def replace(self: Self, **kwargs) -> Self:
        if not dataclasses.is_dataclass(self):
            raise TypeError(f"'{fully_qualified_type(self)}' is not a dataclass")

        # We add this because `dataclasses.is_dataclass` returns a type guard that erroneously
        # implies `self` could be a type instead of an instance.
        assert not isinstance(self, type)

        return dataclasses.replace(self, **kwargs)


class Serializable(abc.ABC):
    @abc.abstractmethod
    def to_json(self) -> Mapping:
        """
        Converts an existing object into a JSON serializable Python object.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def from_json(cls, json_data: Mapping, strict=False) -> Self:
        raise NotImplementedError


class SerializeMixin(Serializable):
    @classmethod
    def from_json(cls, json_data: Mapping, strict=False) -> Self:
        qualified_type = fully_qualified_type(cls)
        if not dataclasses.is_dataclass(cls):
            raise TypeError(f"{qualified_type} is not a dataclass")

        # TODO(erik): Consider using `typing.get_type_hints`. If someone uses
        # `from __future__ import annotations`, the types are stored as strings e.g.
        # `Field(..., type="str | None")` instead of `Field(..., type = str | None)`
        # which breaks downstream inspection code.
        #
        # Reference
        # https://stackoverflow.com/questions/69090936/how-to-convert-python-string-type-annotation-to-proper-type
        fields = {x.name: x for x in dataclasses.fields(cls)}

        # Handle any type conversions that are necessary
        converted = {}
        for k, v in json_data.items():
            if k not in fields:
                if strict:
                    raise ValueError(f"Field `{k}` is not known for class `{qualified_type}`")
            else:
                converted[k] = _build_value(cls, fields[k].type, v, strict)

        return cls(**converted)

    @overload
    @classmethod
    def from_(cls, value: None, **kwargs) -> None:
        ...

    @overload
    @classmethod
    def from_(cls, value: Any, **kwargs) -> Self:
        ...

    @classmethod
    def from_(cls, value: Any | None, **kwargs) -> Self | None:
        """
        Attempts to create an instance of the class from an arbitrary python object that
        represents a Mapping.
        """

        if value is None:
            return None

        if isinstance(value, cls):
            return value

        if isinstance(value, Serializable):
            json_value = value.to_json()
        else:
            json_value = to_mapping(value)

        return cls.from_json(json_value, **kwargs)

    def to_json(self, *, filter_=UNDEFINED) -> Mapping[str, Any]:
        qualified_type = fully_qualified_type(self)
        if not dataclasses.is_dataclass(self):
            raise TypeError(f"{qualified_type} is not a dataclass")

        field_filter = coalesce_undefined(filter_, _default_field_filter)

        data = _ValueToJSONConverter(filter_=field_filter)
        fields = dataclasses.fields(self)
        for field in fields:
            key = field.name
            value = getattr(self, key)
            if field_filter is None or field_filter(key, value):
                data[key] = value

        return data.dict_


@dataclasses.dataclass(frozen=True, kw_only=True)
class _ValueToJSONConverter:
    """
    Provides a write-only dictionary that converts a value into a json
    compatible version based on its type. The conversion is restricted to specifically registered
    converter functions. This is used by `SerializeMixin` to recursively convert values for
    serialization.
    """

    filter_: FieldFilter | None
    dict_: OrderedDict[str, Any] = dataclasses.field(default_factory=OrderedDict)

    @property
    def converters(self) -> dict[tuple, Callable[[Self, Any], Any]]:
        return {
            (list, tuple): (lambda self, value: [self._convert(v) for v in value]),
            (set, frozenset): (lambda self, value: [self._convert(v) for v in sorted(value)]),
            (Serializable,): (lambda self, value: value.to_json(filter_=self.filter_)),
            (Path,): (lambda _, value: value.as_posix()),
            (type(re.compile("")),): (lambda _, value: value.pattern),
        }

    def __setitem__(self, key, value):
        self.dict_[key] = self._convert(value)

    def _convert(self, value):
        if _is_namedtuple_type(type(value)):
            data = value._asdict()
            return [self._convert(data[field]) for field in value._fields]

        for type_tuple, converter in self.converters.items():
            if isinstance(value, type_tuple):
                return converter(self, value)

        return value


def _build_value(cls, target_type, value, strict):
    if target_type is None or target_type is Any:
        # `type` is not specified so value should not be converted
        pass
    elif _is_list_type(target_type):
        # `typing.List` or `list`
        (element_type,) = get_args(target_type)
        value = [_build_value(cls, element_type, v, strict) for v in value]
    elif _is_set_type(target_type):
        # `typing.Set` or `set`
        (element_type,) = get_args(target_type)
        value = set(_build_value(cls, element_type, v, strict) for v in value)
    elif _is_frozenset_type(target_type):
        # `typing.FrozenSet` or `frozenset`
        (element_type,) = get_args(target_type)
        value = frozenset(_build_value(cls, element_type, v, strict) for v in value)
    elif _is_tuple_type(target_type):
        # `typing.Tuple` or `tuple`
        element_types = get_args(target_type)
        if (
            len(element_types) == 2
            and element_types[0] is not Ellipsis
            and element_types[1] is Ellipsis
        ):
            # e.g. `tuple[int, ...]`
            element_types = [element_types[0]] * len(value)
        elif len(element_types) == len(value):
            # Heterogenous tuple e.g. `tuple[A, B, C]`
            pass
        else:
            raise ValueError(
                f"For {target_type = }, expected {len(element_types)} values but found {len(value)}"
            )

        value = tuple(
            _build_value(cls, element_type, v, strict)
            for element_type, v in zip(element_types, value)
        )
    elif _is_union_type(target_type):
        # `typing.Optional` or `X | None`
        possible_types = set(get_args(target_type))

        if NoneType in possible_types and len(possible_types) == 2:
            if value is not None:
                possible_types.remove(NoneType)
                actual_type = first(possible_types)
                value = _build_value(cls, actual_type, value, strict)
        else:
            raise ValueError("Deserializing arbitrary Union type is not supported")
    elif _robust_is_subclass(target_type, SerializeMixin):
        value = target_type.from_(value, strict=strict)
    elif isinstance(target_type, EnumTypeWrapper) and isinstance(value, int):
        # Protobuf enum. We don't want to cast the value because they are passed around as
        # specially typed ints.
        pass
    elif _robust_is_instance(value, target_type):
        # value already conforms to a specific type, e.g. "x" to `str`
        pass
    else:
        # Lastly we simply convert the value to the type. This includes
        #  - Primitives like: int, float, str, dict
        #  - collections.OrderedDict
        #  - collections.namedtuple (note, there is no typing information for the fields)
        #  - pathlib.Path
        value = target_type(value)

    return value


def _is_generic_alias(target_type):
    # With Python <3.9, the base types `list`, etc. could not support `[]` notation for types.
    # Therefore the `typing.List`, etc. classes were added as a stopgap.
    #
    # NOTE: The older style of typing will not be removed until at least Python 3.14
    #
    # References
    # https://docs.python.org/3/library/typing.html#deprecated-aliases

    # pylint: disable=deprecated-typing-alias
    is_old_generic_alias = issubclass(type(target_type), type(List[int]))
    # pylint: enable=deprecated-typing-alias

    # With Python >=3.9, the base type `list`, etc. now do support `[]` notation for types.
    # e.g. `list[int]` works.
    is_new_generic_alias = isinstance(target_type, GenericAlias)

    return is_old_generic_alias or is_new_generic_alias


def _is_union_type(target_type):
    # The original `Optional` type is slightly more compliated

    # pylint: disable=consider-alternative-union-syntax
    is_union_generic_alias = (
        issubclass(type(target_type), type(Union[int, str])) and get_origin(target_type) is Union
    )
    # pylint: enable=consider-alternative-union-syntax

    # With Python 3.10, better union type support was added
    #
    # References
    # https://docs.python.org/3/library/stdtypes.html#types-union
    is_new_union_alias = isinstance(target_type, UnionType)

    return is_union_generic_alias or is_new_union_alias


def _is_list_type(target_type):
    return _is_generic_alias(target_type) and get_origin(target_type) is list


def _is_set_type(target_type):
    return _is_generic_alias(target_type) and get_origin(target_type) is set


def _is_frozenset_type(target_type):
    return _is_generic_alias(target_type) and get_origin(target_type) is frozenset


def _is_namedtuple_type(target_type):
    bases = getattr(target_type, "__bases__", None)
    if bases is None or bases != (tuple,):
        return False

    fields = getattr(target_type, "_fields", None)
    if not isinstance(fields, tuple) or not all(isinstance(f, str) for f in fields):
        return False

    return True


def _is_tuple_type(target_type):
    return _is_generic_alias(target_type) and get_origin(target_type) is tuple
