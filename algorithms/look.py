"""
LOOK Algorithm
Jak SCAN, ale winda zawraca gdy brak dalszych żądań w tym kierunku
(nie jedzie do fizycznego końca budynku).
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from .base import BaseDispatcher

if TYPE_CHECKING:
    from simulation.elevator import Elevator
    from simulation.building import Floor
    from simulation.passenger import Passenger


class LOOKDispatcher(BaseDispatcher):
    def __init__(self) -> None:
        self._look_dir: dict[int, int] = {}

    @property
    def name(self) -> str:
        return "LOOK"

    def dispatch(
        self,
        elevators: list["Elevator"],
        floors: list["Floor"],
    ) -> None:
        pending = set(self.get_pending_floors(floors))
        if not pending:
            return

        # Globalne przypisane piętra — unikamy duplikatów między windami
        global_assigned = self.get_assigned_floors(elevators)
        unassigned = [f for f in pending if f not in global_assigned]

        for floor in unassigned:
            best = self._pick_elevator(floor, elevators)
            if best is not None:
                self._update_look_dir(best, floor)
                best.assign_stop(floor)

    def _pick_elevator(self, floor: int, elevators: list["Elevator"]) -> "Elevator | None":
        # 1. Winda jadąca w kierunku piętra i jeszcze do niego dotrze
        for e in elevators:
            if e.direction == 1 and e.position <= floor:
                return e
            if e.direction == -1 and e.position >= floor:
                return e
        # 2. Wolna winda — preferuj zgodną z kierunkiem LOOK
        idle = [e for e in elevators if e.is_idle and not e.stop_queue]
        if not idle:
            return None
        for e in idle:
            look_dir = self._look_dir.get(e.id, 1)
            if (look_dir == 1 and floor >= e.current_floor) or \
               (look_dir == -1 and floor <= e.current_floor):
                return e
        return min(idle, key=lambda e: abs(e.position - floor))

    def _update_look_dir(self, elev: "Elevator", floor: int) -> None:
        # LOOK: zawraca przy ostatnim żądaniu (nie przy końcu budynku)
        if floor >= elev.current_floor:
            self._look_dir[elev.id] = 1
        else:
            self._look_dir[elev.id] = -1

    def reset(self) -> None:
        self._look_dir.clear()
