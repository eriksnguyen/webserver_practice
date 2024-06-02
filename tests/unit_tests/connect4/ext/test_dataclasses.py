import json
import typing
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import pytest

from connect4.ext.dataclasses import ReplaceMixin, SerializeMixin


@dataclass(frozen=True, kw_only=True)
class Foo:
    x: str
    y: int
    z: str


def test_replace_mixin():
    @dataclass(frozen=True, kw_only=True)
    class Bar(Foo, ReplaceMixin):
        pass

    assert Bar(x="x", y=0, z="z").replace(x="abc") == Bar(x="abc", y=0, z="z")


@dataclass
class Base(SerializeMixin):
    @dataclass
    class Args(ReplaceMixin, SerializeMixin):
        @dataclass
        class Nested(SerializeMixin):
            x: Path

        # primitive types
        primitive_1: float

        # pylint: disable=deprecated-typing-alias,consider-alternative-union-syntax

        # lists + SerializeMixin
        list_1: typing.List[Nested]
        list_2: list[int] | None = None

        # Optional
        opt_1: typing.Optional[typing.Any] = None

        # Sets
        set_1: typing.Set[int] | None = None
        set_2: set[int] | None = None
        set_3: typing.FrozenSet[int] | None = None
        set_4: frozenset[int] | None = None

        # Tuples
        tuple_1: typing.Tuple[int, ...] | None = None
        tuple_2: tuple[int, ...] | None = None
        tuple_3: typing.Tuple[int, str] | None = None
        tuple_4: tuple[int, str, int] | None = None
        tuple_5: tuple[int, str] | None = None
        tuple_6: tuple[int] | None = None

        # Dict
        dict_1: typing.Dict[str, int] | None = None
        dict_2: dict[str, int] | None = None
        dict_3: typing.OrderedDict[str, int] | None = None
        dict_4: OrderedDict[str, int] | None = None

        # pylint: enable=deprecated-typing-alias,consider-alternative-union-syntax

    args: Args


@pytest.fixture
def base():
    return Base(Base.Args(2.0, [Base.Args.Nested(Path("a/b/c/"))]))


@pytest.fixture
def odict():
    return OrderedDict(
        [
            (
                "args",
                OrderedDict(
                    [
                        ("primitive_1", 2.0),
                        ("list_1", [OrderedDict([("x", "a/b/c")])]),
                        ("list_2", None),
                        ("opt_1", None),
                        ("set_1", None),
                        ("set_2", None),
                        ("set_3", None),
                        ("set_4", None),
                        ("tuple_1", None),
                        ("tuple_2", None),
                        ("tuple_3", None),
                        ("tuple_4", None),
                        ("tuple_5", None),
                        ("tuple_6", None),
                        ("dict_1", None),
                        ("dict_2", None),
                        ("dict_3", None),
                        ("dict_4", None),
                    ]
                ),
            ),
        ]
    )


def test_serialize_mixin_to_json(
    base: Base, odict: OrderedDict  # pylint: disable=redefined-outer-name
):
    assert isinstance(base.args.list_1[0].x, Path)
    assert (
        json.dumps(base.to_json()) == '{"args": {"primitive_1": 2.0, "list_1": [{"x": "a/b/c"}]}}'
    ), "By default, all null values should be stripped from the output"

    assert json.dumps(base.to_json(filter_=None)) == json.dumps(
        odict
    ), "Specifying a null filter should result in all fields serializing"

    # List
    assert (
        json.dumps(Base(base.args.replace(list_2=[1])).to_json())
        == '{"args": {"primitive_1": 2.0, "list_1": [{"x": "a/b/c"}], "list_2": [1]}}'
    ), "If args.list_2 is not null it should be included in serialization"

    # Sets
    assert (
        json.dumps(Base(base.args.replace(set_1={1})).to_json())
        == '{"args": {"primitive_1": 2.0, "list_1": [{"x": "a/b/c"}], "set_1": [1]}}'
    ), "If args.set_1 is not null it should be included in serialization"

    assert (
        json.dumps(Base(base.args.replace(set_3=frozenset({2}))).to_json())
        == '{"args": {"primitive_1": 2.0, "list_1": [{"x": "a/b/c"}], "set_3": [2]}}'
    ), "If args.set_3 is not null it should be included in serialization"

    # Tuples
    assert (
        json.dumps(Base(base.args.replace(tuple_1=(1,))).to_json())
        == '{"args": {"primitive_1": 2.0, "list_1": [{"x": "a/b/c"}], "tuple_1": [1]}}'
    ), "If args.tuple_1 is not null it should be included in serialization"

    # Mappings
    assert (
        json.dumps(Base(base.args.replace(dict_1={"k": "v"})).to_json())
        == '{"args": {"primitive_1": 2.0, "list_1": [{"x": "a/b/c"}], "dict_1": {"k": "v"}}}'
    ), "If args.dict_1 is not null it should be included in serialization"

    assert (
        json.dumps(Base(base.args.replace(dict_3=OrderedDict([("a", 1)]))).to_json())
        == '{"args": {"primitive_1": 2.0, "list_1": [{"x": "a/b/c"}], "dict_3": {"a": 1}}}'
    ), "If args.dict_3 is not null it should be included in serialization"


def test_serialize_mixin_from_json(base: Base):  # pylint: disable=redefined-outer-name
    deserialized_base = Base.from_json(
        json.loads(
            """\
            {
                "args": {
                    "primitive_1": 2,
                    "list_1": [{"x": "a/b/c"}],
                    "list_2": [0],
                    "opt_1": {"A": {"B": "C"}},
                    "set_1": [1],
                    "set_2": [1, 2],
                    "set_3": [1, 2, 3],
                    "set_4": [1, 2, 3, 4],
                    "tuple_1": [1, 2, 3],
                    "tuple_2": [3, 4, 5],
                    "tuple_3": [1, "a"],
                    "tuple_4": [1, "a", 3],
                    "tuple_5": [1, "e"],
                    "tuple_6": [1],
                    "dict_1": {"a": 3},
                    "dict_2": {"b": 3},
                    "dict_3": {"c": 3},
                    "dict_4": {"d": 3, "e": 4}
                }
            }
            """,
            # Deserialize with an OrderedDict to preserve ordering of keys
            object_pairs_hook=OrderedDict,
        )
    )

    assert isinstance(deserialized_base.args, Base.Args)
    assert isinstance(
        deserialized_base.args.primitive_1, float
    ), "Type of primitive_1 should convert '2' into a float"
    assert isinstance(deserialized_base.args.list_1[0], Base.Args.Nested)
    assert isinstance(deserialized_base.args.list_1[0].x, Path)
    assert isinstance(deserialized_base.args.list_2, list)
    assert isinstance(deserialized_base.args.opt_1, dict)
    assert deserialized_base.args.opt_1 == {
        "A": {"B": "C"}
    }, "Expected type of Any to be kept as is"
    assert isinstance(deserialized_base.args.set_1, set)
    assert isinstance(deserialized_base.args.set_2, set)
    assert isinstance(deserialized_base.args.set_3, frozenset)
    assert isinstance(deserialized_base.args.set_4, frozenset)
    assert isinstance(deserialized_base.args.tuple_1, tuple)
    assert isinstance(deserialized_base.args.tuple_2, tuple)
    assert isinstance(deserialized_base.args.tuple_3, tuple)
    assert isinstance(deserialized_base.args.tuple_4, tuple)
    assert isinstance(deserialized_base.args.tuple_5, tuple)
    assert isinstance(deserialized_base.args.tuple_6, tuple)
    assert isinstance(deserialized_base.args.dict_1, dict)
    assert isinstance(deserialized_base.args.dict_2, dict)
    assert isinstance(deserialized_base.args.dict_3, OrderedDict)
    assert isinstance(deserialized_base.args.dict_4, OrderedDict)

    assert (
        Base(
            base.args.replace(
                list_2=[0],
                opt_1={"A": {"B": "C"}},
                set_1=set([1]),
                set_2=set([1, 2]),
                set_3=frozenset([1, 2, 3]),
                set_4=frozenset([1, 2, 3, 4]),
                tuple_1=tuple([1, 2, 3]),
                tuple_2=tuple([3, 4, 5]),
                tuple_3=tuple([1, "a"]),
                tuple_4=tuple([1, "a", 3]),
                tuple_5=tuple([1, "e"]),
                tuple_6=tuple([1]),
                dict_1={"a": 3},
                dict_2={"b": 3},
                dict_3=OrderedDict([("c", 3)]),
                dict_4=OrderedDict([("d", 3), ("e", 4)]),
            )
        )
        == deserialized_base
    )

    @dataclass
    class Nulls(ReplaceMixin, SerializeMixin):
        opt_1: typing.Any | None
        opt_2: typing.Any | None = None

    deserialized_nulls = Nulls.from_json(json.loads('{"opt_1": null}'))
    assert deserialized_nulls.opt_1 is None, "Explicit null should deserialize to None"
    assert deserialized_nulls.opt_2 is None, "Implicit null should deserialize to None"

    with pytest.raises(TypeError) as ctx:
        Nulls.from_json(json.loads("{}"))

    assert ctx.match(
        "missing 1 required positional argument: 'opt_1'"
    ), "Optionals with no default of None should require explicit null inputs"


def test_serialize_mixin_from_(base: Base):  # pylint: disable=redefined-outer-name
    assert Base.from_(None) is None, "`from_` should return `None` if `None` is provided"

    assert (
        Base.from_(base) is base
    ), "`from_` should return the original object when the classes match"

    class Extension(Base):
        pass

    extension = Extension.from_(base)
    assert (
        extension is not base and extension.to_json() == base.to_json()
    ), "`from_` should convert the value to json and back to the desired class"

    @dataclass
    class NotSerializable:
        args: typing.Any

    assert (
        Extension.from_(NotSerializable(base.args)) == extension
    ), "`from_` should be able to accept objects that are not Serializable."
