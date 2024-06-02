from dataclasses import dataclass, field

from connect4.ext.dataclasses import SerializeMixin

PLAYER1 = "red"
PLAYER2 = "yellow"


class IllegalMoveError(Exception):
    pass


@dataclass(kw_only=True, frozen=True)
class Move(SerializeMixin):
    player: str
    column: int
    row: int


@dataclass(kw_only=True, frozen=True)
class Connect4Board(SerializeMixin):
    num_columns: int = field(default=7)
    num_rows: int = field(default=6)
    winning_threshold: int = field(default=4)

    # Game State
    move_history: list[Move] = field(default_factory=list)
    column_heights: list[int] = field(init=False)
    game_state: list[list[str]] = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "column_heights", [0 for _ in range(self.num_columns)])
        object.__setattr__(
            self,
            "game_state",
            [["" for _ in range(self.num_columns)] for _ in range(self.num_rows)],
        )

    @property
    def last_player(self):
        return PLAYER1 if len(self.move_history) % 2 else PLAYER2

    @property
    def next_player(self):
        return PLAYER2 if len(self.move_history) % 2 else PLAYER1

    def play(self, player: str, column: int):
        if player == self.last_player:
            raise IllegalMoveError(f"It is {self.next_player}'s turn")

        row = self.column_heights[column]
        if row >= self.num_rows:
            raise IllegalMoveError(f"{column = } is full")

        self.move_history.append(Move(player=player, column=column, row=row))
        self.game_state[row][column] = player
        self.column_heights[column] += 1

        return row

    def last_move_won(self):
        if not self.move_history:
            return False

        def _count_consecutive(player, row, col, d_row, d_col):
            count = 0
            while (
                0 <= row < self.num_rows
                and 0 <= col < self.num_columns
                and self.game_state[row][col] == player
            ):
                count += 1
                row += d_row
                col += d_col

            return count

        last_move = self.move_history[-1]

        # Last move completes a vertical set
        if (
            _count_consecutive(last_move.player, last_move.row, last_move.column, -1, 0)
            >= self.winning_threshold
        ):
            return True

        # Last move completes a horizontal set
        if (
            _count_consecutive(last_move.player, last_move.row, last_move.column, 0, -1)
            + _count_consecutive(last_move.player, last_move.row, last_move.column, 0, 1)
            - 1
            >= self.winning_threshold
        ):
            return True

        # Last move completes one diagonal set
        if (
            _count_consecutive(last_move.player, last_move.row, last_move.column, -1, -1)
            + _count_consecutive(last_move.player, last_move.row, last_move.column, 1, 1)
            - 1
            >= self.winning_threshold
        ):
            return True

        # Last move completes a diagonal set
        if (
            _count_consecutive(last_move.player, last_move.row, last_move.column, 1, -1)
            + _count_consecutive(last_move.player, last_move.row, last_move.column, -1, 1)
            - 1
            >= self.winning_threshold
        ):
            return True

        return False

    @property
    def winner(self) -> str | None:
        if self.last_move_won():
            return self.move_history[-1].player

        return None
