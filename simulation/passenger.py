from dataclasses import dataclass, field
from typing import Optional


_id_counter = 0


def _next_id() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter


def reset_id_counter() -> None:
    global _id_counter
    _id_counter = 0


@dataclass
class Passenger:
    origin_floor: int
    destination_floor: int
    arrival_time: float
    id: int = field(default_factory=_next_id)
    board_time: Optional[float] = None
    exit_time: Optional[float] = None

    @property
    def wait_time(self) -> Optional[float]:
        if self.board_time is None:
            return None
        return self.board_time - self.arrival_time

    @property
    def trip_time(self) -> Optional[float]:
        if self.board_time is None or self.exit_time is None:
            return None
        return self.exit_time - self.board_time

    @property
    def total_time(self) -> Optional[float]:
        if self.exit_time is None:
            return None
        return self.exit_time - self.arrival_time

    @property
    def direction(self) -> int:
        return 1 if self.destination_floor > self.origin_floor else -1

    def __repr__(self) -> str:
        return f"P{self.id}({self.origin_floor}->{self.destination_floor})"
