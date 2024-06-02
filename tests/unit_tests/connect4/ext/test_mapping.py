from collections import OrderedDict, namedtuple
from dataclasses import dataclass

from connect4.ext.mapping import to_mapping


def test_to_mapping():
    data = OrderedDict.fromkeys("ab")
    assert to_mapping(data) is data

    data = {"x": 12}
    assert to_mapping(data) is data

    @dataclass
    class Example:
        a: int

    assert to_mapping(Example(1)) == {"a": 1}

    class Example2:
        def __init__(self):
            self.b = 2

    assert to_mapping(Example2()) == {"b": 2}

    tuple_instance = namedtuple("X", ["y"])(3)
    assert to_mapping(tuple_instance) == {"y": 3}
