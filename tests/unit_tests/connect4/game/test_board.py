from collections import OrderedDict
from collections.abc import Sequence

import pytest

from connect4.game.board import PLAYER1, PLAYER2, Connect4Board, IllegalMoveError, Move


def _test_game_state(board: Connect4Board, move: Move, should_win: bool = False):
    assert board.last_move_won() == should_win
    assert board.winner is None if not should_win else board.winner == move.player
    assert board.last_player == move.player
    assert board.next_player != move.player
    assert board.move_history[-1] == move


def test_connect4_errors():
    board = Connect4Board()

    # Verify initial game state
    assert not board.move_history
    assert not board.last_move_won()
    assert board.winner is None
    assert board.next_player is PLAYER1
    assert board.last_player is PLAYER2

    # Player 2 can't go when it is Player 1's move
    with pytest.raises(IllegalMoveError) as ctx:
        board.play(PLAYER2, 0)
    assert ctx.match(f"It is {PLAYER1}'s turn")

    # Insert a token for PLAYER1 at column 0, we expect the token to fall at row 0.
    board.play(PLAYER1, 0)
    _test_game_state(board, Move(player=PLAYER1, column=0, row=0))

    # Player 1 can't go when it is Player 2's move
    with pytest.raises(IllegalMoveError) as ctx:
        board.play(PLAYER1, 0)
    assert ctx.match(f"It is {PLAYER2}'s turn")


# NOTE: inputs are in (col, expected_row) order
CONNECT4_TEST_CASES = {
    "no_moves": ([], False),
    "one_move": ([(0, 0)], False),
    # Player 1 wins horizontally
    "horizontal_win": ([(0, 0), (0, 1), (1, 0), (0, 2), (2, 0), (0, 3), (3, 0)], True),
    # Player 2 wins vertically
    "vertical_win": ([(0, 0), (0, 1), (1, 0), (0, 2), (2, 0), (0, 3), (4, 0), (0, 4)], True),
    # Player 2 wins across diagonal going from upper left to lower right
    "negative_diagonal_win": (
        # fmt: off
        [
            (0, 0), (1, 0), (2, 0), (3, 0),
            (3, 1), (2, 1), (1, 1), (0, 1),
            (0, 2), (1, 2), (2, 2), (3, 2),
            (1, 3), (0, 3),
        ],
        # fmt: on
        True,
    ),
    # Player 1 wins across diagonal going from lower left to upper right
    "positive_diagonal_win": (
        # fmt: off
        [
            (0, 0), (1, 0), (2, 0), (3, 0),
            (3, 1), (2, 1), (1, 1), (0, 1),
            (0, 2), (1, 2), (2, 2), (3, 2),
            (3, 3),
        ],
        # fmt: on
        True,
    ),
}

CONNECT4_TEST_CASE_IDS = list(CONNECT4_TEST_CASES.keys())
CONNECT4_TEST_ARG_VALUES = list(CONNECT4_TEST_CASES[k] for k in CONNECT4_TEST_CASE_IDS)


@pytest.mark.parametrize(
    argnames=["move_set", "last_move_should_win"],
    ids=CONNECT4_TEST_CASE_IDS,
    argvalues=CONNECT4_TEST_ARG_VALUES,
)
def test_connect4_win_conditions(move_set: Sequence[tuple[int, int]], last_move_should_win: bool):
    board = Connect4Board()
    next_player = PLAYER1

    for i, move in enumerate(move_set):
        input_col = move[0]
        expected_row = move[1]

        expected_move = Move(player=next_player, column=input_col, row=expected_row)
        emitted_row = board.play(next_player, input_col)

        assert emitted_row == expected_move.row
        if i == len(move_set) - 1:
            _test_game_state(board, expected_move, should_win=last_move_should_win)
        else:
            _test_game_state(board, expected_move, should_win=False)

        next_player = PLAYER2 if next_player is PLAYER1 else PLAYER1

    assert board.last_move_won() == last_move_should_win
