from __future__ import annotations
from collections import deque
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .building import Building
from .passenger import Passenger

# Stałe czasowe (sekundy symulacji)
FLOOR_TRAVEL_TIME = 1.0   # czas przejazdu jednego piętra
DOOR_OPEN_TIME = 0.5      # czas otwierania drzwi
DOOR_STAY_TIME = 2.0      # czas oczekiwania z otwartymi drzwiami
DOOR_CLOSE_TIME = 0.5     # czas zamykania drzwi

MAX_CAPACITY = 8          # max pasażerów w windzie


class ElevatorState(Enum):
    IDLE = auto()
    MOVING_UP = auto()
    MOVING_DOWN = auto()
    DOOR_OPENING = auto()
    DOOR_OPEN = auto()
    DOOR_CLOSING = auto()


class Elevator:
    def __init__(self, elevator_id: int, start_floor: int = 0) -> None:
        self.id = elevator_id
        self.position: float = float(start_floor)   # ciągła pozycja w jednostkach pięter
        self.state: ElevatorState = ElevatorState.IDLE
        self.direction: int = 0                      # +1, -1, 0
        self.target_floor: Optional[int] = None
        self.stop_queue: deque[int] = deque()        # kolejka pięter do zatrzymania
        self.passengers: list[Passenger] = []
        self.state_timer: float = 0.0                # czas spędzony w bieżącym stanie
        self._door_anim: float = 0.0                 # 0=zamknięte, 1=otwarte (do animacji)

    @property
    def current_floor(self) -> int:
        return round(self.position)

    @property
    def is_idle(self) -> bool:
        return self.state == ElevatorState.IDLE

    @property
    def door_open_ratio(self) -> float:
        """0.0 = zamknięte, 1.0 = otwarte (do rysowania)"""
        return self._door_anim

    def update(self, dt: float, sim_time: float, building: "Building") -> None:
        self.state_timer += dt

        if self.state == ElevatorState.IDLE:
            self._update_idle()

        elif self.state in (ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN):
            self._update_moving(dt, sim_time, building)

        elif self.state == ElevatorState.DOOR_OPENING:
            self._door_anim = min(1.0, self.state_timer / DOOR_OPEN_TIME)
            if self.state_timer >= DOOR_OPEN_TIME:
                self._transition(ElevatorState.DOOR_OPEN)

        elif self.state == ElevatorState.DOOR_OPEN:
            self._door_anim = 1.0
            self._do_boarding(sim_time, building)
            if self.state_timer >= DOOR_STAY_TIME:
                self._transition(ElevatorState.DOOR_CLOSING)

        elif self.state == ElevatorState.DOOR_CLOSING:
            self._door_anim = max(0.0, 1.0 - self.state_timer / DOOR_CLOSE_TIME)
            if self.state_timer >= DOOR_CLOSE_TIME:
                self._door_anim = 0.0
                # Usuń to piętro z kolejki jeśli jeszcze tam jest
                if self.stop_queue and self.stop_queue[0] == self.current_floor:
                    self.stop_queue.popleft()
                self._transition(ElevatorState.IDLE)

    def _update_idle(self) -> None:
        if self.stop_queue:
            next_floor = self.stop_queue[0]
            if next_floor == self.current_floor:
                self._transition(ElevatorState.DOOR_OPENING)
            elif next_floor > self.current_floor:
                self.direction = 1
                self._transition(ElevatorState.MOVING_UP)
            else:
                self.direction = -1
                self._transition(ElevatorState.MOVING_DOWN)

    def _update_moving(self, dt: float, sim_time: float, building: "Building") -> None:
        speed = 1.0 / FLOOR_TRAVEL_TIME   # piętro/s
        self.position += self.direction * speed * dt
        # Przytnij do granic budynku
        self.position = max(0.0, min(float(building.num_floors - 1), self.position))

        if self.stop_queue:
            target = self.stop_queue[0]
            # Sprawdź czy dotarliśmy do celu (z małym marginesem)
            if self.direction == 1 and self.position >= target - 0.01:
                self.position = float(target)
                self._transition(ElevatorState.DOOR_OPENING)
            elif self.direction == -1 and self.position <= target + 0.01:
                self.position = float(target)
                self._transition(ElevatorState.DOOR_OPENING)

    def _do_boarding(self, sim_time: float, building: "Building") -> None:
        """Wysiadanie i wsiadanie pasażerów."""
        floor = self.current_floor
        floor_obj = building.floors[floor]

        # Wysiadanie — wszyscy których cel to to piętro
        exiting = [p for p in self.passengers if p.destination_floor == floor]
        for p in exiting:
            p.exit_time = sim_time
            self.passengers.remove(p)
            building.collector.record_exit(p)

        # Wsiadanie — wszyscy czekający na tym piętrze.
        # Dispatcher celowo posłał tutaj windę — bierzemy każdego (obie strony).
        waiting = floor_obj.waiting_up + floor_obj.waiting_down
        boarded = []
        for p in list(waiting):
            if len(self.passengers) >= MAX_CAPACITY:
                break
            p.board_time = sim_time
            self.passengers.append(p)
            boarded.append(p)
            self._add_stop(p.destination_floor)

        for p in boarded:
            if p in floor_obj.waiting_up:
                floor_obj.waiting_up.remove(p)
            if p in floor_obj.waiting_down:
                floor_obj.waiting_down.remove(p)

    def _add_stop(self, floor: int) -> None:
        """Dodaje piętro do kolejki i sortuje nearest-first od aktualnej pozycji."""
        if floor not in self.stop_queue:
            self.stop_queue.append(floor)
            # Sortuj rosnąco — kierunek ustali _update_idle na podstawie pierwszego elementu
            pos = self.position
            self.stop_queue = deque(sorted(self.stop_queue, key=lambda f: abs(f - pos)))

    def _transition(self, new_state: ElevatorState) -> None:
        self.state = new_state
        self.state_timer = 0.0
        if new_state == ElevatorState.IDLE:
            self.direction = 0
            self.target_floor = None

    def assign_stop(self, floor: int) -> None:
        """Zewnętrzny interface dla dispatchera."""
        self._add_stop(floor)

    def reset(self, start_floor: int = 0) -> None:
        self.position = float(start_floor)
        self.state = ElevatorState.IDLE
        self.direction = 0
        self.target_floor = None
        self.stop_queue = deque()
        self.passengers = []
        self.state_timer = 0.0
        self._door_anim = 0.0

    def __repr__(self) -> str:
        return f"Elevator{self.id}(floor={self.current_floor:.1f}, {self.state.name}, q={list(self.stop_queue)})"
