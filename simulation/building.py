from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .elevator import Elevator
from .passenger import Passenger, reset_id_counter

if TYPE_CHECKING:
    from algorithms.base import BaseDispatcher
    from metrics.collector import MetricsCollector


@dataclass
class Floor:
    number: int
    waiting_up: list[Passenger] = field(default_factory=list)
    waiting_down: list[Passenger] = field(default_factory=list)

    @property
    def all_waiting(self) -> list[Passenger]:
        return self.waiting_up + self.waiting_down

    def add_passenger(self, p: Passenger) -> None:
        if p.destination_floor > p.origin_floor:
            self.waiting_up.append(p)
        else:
            self.waiting_down.append(p)


class Building:
    def __init__(
        self,
        num_floors: int,
        num_elevators: int,
        dispatcher: "BaseDispatcher",
        collector: "MetricsCollector",
    ) -> None:
        self.num_floors = num_floors
        self.num_elevators = num_elevators
        self.dispatcher = dispatcher
        self.collector = collector
        self.floors: list[Floor] = [Floor(i) for i in range(num_floors)]
        self.elevators: list[Elevator] = [Elevator(i) for i in range(num_elevators)]

    def add_passenger(self, p: Passenger) -> None:
        self.floors[p.origin_floor].add_passenger(p)
        self.collector.record_arrival(p)
        # Natychmiast powiadom dispatcher
        self.dispatcher.on_new_request(self.elevators, self.floors, p)

    def update(self, dt: float, sim_time: float) -> None:
        # Dispatcher może zaktualizować stop_queue wind
        self.dispatcher.dispatch(self.elevators, self.floors)
        # Zaktualizuj każdą windę
        for elevator in self.elevators:
            elevator.update(dt, sim_time, self)

    def reset(self) -> None:
        reset_id_counter()
        self.floors = [Floor(i) for i in range(self.num_floors)]
        for i, elev in enumerate(self.elevators):
            elev.reset(start_floor=0)

    def rebuild(self, num_floors: int, num_elevators: int) -> None:
        """Przebuduj budynek z nową konfiguracją."""
        self.num_floors = num_floors
        self.num_elevators = num_elevators
        self.floors = [Floor(i) for i in range(num_floors)]
        self.elevators = [Elevator(i) for i in range(num_elevators)]
        reset_id_counter()
