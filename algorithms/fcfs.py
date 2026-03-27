"""
FCFS – First Come, First Served
Żądania obsługiwane w kolejności zgłoszeń.
Wolna winda dostaje pierwsze nieobsługiwane żądanie.
"""
from __future__ import annotations
from collections import deque
from typing import TYPE_CHECKING

from .base import BaseDispatcher

if TYPE_CHECKING:
    from simulation.elevator import Elevator
    from simulation.building import Floor
    from simulation.passenger import Passenger


class FCFSDispatcher(BaseDispatcher):
    def __init__(self) -> None:
        # Kolejka (floor_number,) w kolejności zgłoszeń (bez duplikatów)
        self._queue: deque[int] = deque()

    @property
    def name(self) -> str:
        return "FCFS"

    def on_new_request(
        self,
        elevators: list["Elevator"],
        floors: list["Floor"],
        passenger: "Passenger",
    ) -> None:
        floor = passenger.origin_floor
        if floor not in self._queue:
            self._queue.append(floor)
        self.dispatch(elevators, floors)

    def dispatch(
        self,
        elevators: list["Elevator"],
        floors: list["Floor"],
    ) -> None:
        # Wyczyść piętra bez czekających pasażerów z kolejki
        pending = set(self.get_pending_floors(floors))
        self._queue = deque(f for f in self._queue if f in pending)

        # Przypisz kolejne żądania do wolnych wind
        for floor in list(self._queue):
            # Sprawdź czy ktoś już jedzie po to piętro
            already_served = any(floor in e.stop_queue for e in elevators)
            if already_served:
                continue
            idle = self.find_idle_elevator(elevators)
            if idle is None:
                break
            idle.assign_stop(floor)

    def reset(self) -> None:
        self._queue.clear()
