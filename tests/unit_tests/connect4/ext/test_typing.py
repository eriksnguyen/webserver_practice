from connect4.ext.typing import fully_qualified_type


def test_fully_qualified_type():
    # The type of `fully_qualified_type` is `function`
    assert fully_qualified_type(fully_qualified_type) == "builtins.function"

    class Type1:
        class Type2:
            pass

    assert (
        fully_qualified_type(Type1())
        == "unit_tests.connect4.ext.test_typing.test_fully_qualified_type.<locals>.Type1"
    ), "Local scope type instances should work"

    assert (
        fully_qualified_type(Type1)
        == "unit_tests.connect4.ext.test_typing.test_fully_qualified_type.<locals>.Type1"
    ), "Local scope type references should work"

    assert (
        fully_qualified_type(Type1.Type2())
        == "unit_tests.connect4.ext.test_typing.test_fully_qualified_type.<locals>.Type1.Type2"
    ), "Local scope subtypes should work"
