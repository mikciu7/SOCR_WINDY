from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.elevator import Elevator
    from simulation.building import Floor
    from simulation.passenger import Passenger


class BaseDispatcher(ABC):
    """Interfejs algorytmu sterowania windami."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    def on_new_request(
        self,
        elevators: list["Elevator"],
        floors: list["Floor"],
        passenger: "Passenger",
    ) -> None:
        """Wywołane gdy pojawia się nowy pasażer. Domyślnie deleguje do dispatch()."""
        self.dispatch(elevators, floors)

    @abstractmethod
    def dispatch(
        self,
        elevators: list["Elevator"],
        floors: list["Floor"],
    ) -> None:
        """Przypisuje żądania do wind (modyfikuje stop_queue)."""
        ...

    def reset(self) -> None:
        """Resetuje stan wewnętrzny dispatchera (np. przy rebuildzie)."""
        pass

    # --- Helpers wspólne dla wszystkich algorytmów ---

    @staticmethod
    def get_pending_floors(floors: list["Floor"]) -> list[int]:
        """Zwraca numery pięter z czekającymi pasażerami."""
        return [f.number for f in floors if f.all_waiting]

    @staticmethod
    def get_assigned_floors(elevators: list["Elevator"]) -> set[int]:
        """Zwraca wszystkie piętra już w kolejkach wind."""
        assigned: set[int] = set()
        for e in elevators:
            assigned.update(e.stop_queue)
        return assigned

    @staticmethod
    def find_idle_elevator(elevators: list["Elevator"]) -> "Elevator | None":
        """Zwraca pierwszą wolną windę (IDLE bez kolejki)."""
        for e in elevators:
            if e.is_idle and not e.stop_queue:
                return e
        return None
