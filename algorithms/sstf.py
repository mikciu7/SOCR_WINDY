"""
SSTF – Shortest Seek Time First
Wolna winda wybiera żądanie z najmniejszą odległością od jej aktualnej pozycji.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from .base import BaseDispatcher

if TYPE_CHECKING:
    from simulation.elevator import Elevator
    from simulation.building import Floor
    from simulation.passenger import Passenger


class SSTFDispatcher(BaseDispatcher):
    @property
    def name(self) -> str:
        return "SSTF"

    def dispatch(
        self,
        elevators: list["Elevator"],
        floors: list["Floor"],
    ) -> None:
        pending = self.get_pending_floors(floors)
        if not pending:
            return

        assigned = self.get_assigned_floors(elevators)
        unassigned = [f for f in pending if f not in assigned]

        for floor in unassigned:
            # Znajdź wolną windę najbliżej tego piętra
            idle_elevators = [e for e in elevators if e.is_idle and not e.stop_queue]
            if not idle_elevators:
                break
            closest = min(idle_elevators, key=lambda e: abs(e.position - floor))
            closest.assign_stop(floor)
