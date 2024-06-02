from connect4.ext.itertools import first


def test_first():
    assert first([]) is None
    assert first("") is None
    assert first([], default=1) == 1
    assert first([1]) == 1
    assert first("ABC") == "A"
