"""
SCAN (Elevator Algorithm)
Winda przesuwa się do końca budynku (góra/dół), zbierając pasażerów po drodze.
Na końcu zawraca. Każda winda ma niezależny kierunek.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from .base import BaseDispatcher

if TYPE_CHECKING:
    from simulation.elevator import Elevator
    from simulation.building import Floor
    from simulation.passenger import Passenger


class SCANDispatcher(BaseDispatcher):
    def __init__(self, num_floors: int = 10) -> None:
        self.num_floors = num_floors
        self._scan_dir: dict[int, int] = {}

    @property
    def name(self) -> str:
        return "SCAN"

    def dispatch(
        self,
        elevators: list["Elevator"],
        floors: list["Floor"],
    ) -> None:
        pending = set(self.get_pending_floors(floors))
        if not pending:
            return

        # Kluczowa poprawka: globalne przypisane piętra — unikamy duplikatów
        global_assigned = self.get_assigned_floors(elevators)
        unassigned = [f for f in pending if f not in global_assigned]

        for floor in unassigned:
            best = self._pick_elevator(floor, elevators)
            if best is not None:
                self._update_scan_dir(best, floor)
                best.assign_stop(floor)

    def _pick_elevator(self, floor: int, elevators: list["Elevator"]) -> "Elevator | None":
        # 1. Winda jadąca w kierunku tego piętra i jeszcze do niego dotrze
        for e in elevators:
            if e.direction == 1 and e.position <= floor:
                return e
            if e.direction == -1 and e.position >= floor:
                return e
        # 2. Wolna winda — preferuj zgodną z kierunkiem skanowania
        idle = [e for e in elevators if e.is_idle and not e.stop_queue]
        if not idle:
            return None
        for e in idle:
            scan_dir = self._scan_dir.get(e.id, 1)
            if (scan_dir == 1 and floor >= e.current_floor) or \
               (scan_dir == -1 and floor <= e.current_floor):
                return e
        return min(idle, key=lambda e: abs(e.position - floor))

    def _update_scan_dir(self, elev: "Elevator", floor: int) -> None:
        if floor >= elev.current_floor:
            self._scan_dir[elev.id] = 1
        else:
            self._scan_dir[elev.id] = -1
        # SCAN: zawróć przy ścianie budynku
        if elev.current_floor >= self.num_floors - 1:
            self._scan_dir[elev.id] = -1
        elif elev.current_floor <= 0:
            self._scan_dir[elev.id] = 1

    def reset(self) -> None:
        self._scan_dir.clear()
