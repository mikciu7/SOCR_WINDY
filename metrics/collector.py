from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.passenger import Passenger


class MetricsCollector:
    def __init__(self) -> None:
        self.completed: list["Passenger"] = []
        self.arrived: list["Passenger"] = []
        self._sim_time: float = 0.0

    def record_arrival(self, p: "Passenger") -> None:
        self.arrived.append(p)

    def record_exit(self, p: "Passenger") -> None:
        self.completed.append(p)

    def tick(self, sim_time: float) -> None:
        self._sim_time = sim_time

    @property
    def total_served(self) -> int:
        return len(self.completed)

    @property
    def total_arrived(self) -> int:
        return len(self.arrived)

    @property
    def avg_wait_time(self) -> float:
        times = [p.wait_time for p in self.completed if p.wait_time is not None]
        return sum(times) / len(times) if times else 0.0

    @property
    def avg_trip_time(self) -> float:
        times = [p.trip_time for p in self.completed if p.trip_time is not None]
        return sum(times) / len(times) if times else 0.0

    @property
    def avg_total_time(self) -> float:
        times = [p.total_time for p in self.completed if p.total_time is not None]
        return sum(times) / len(times) if times else 0.0

    @property
    def max_wait_time(self) -> float:
        times = [p.wait_time for p in self.completed if p.wait_time is not None]
        return max(times) if times else 0.0

    @property
    def throughput(self) -> float:
        """Pasażerowie na minutę symulacji."""
        if self._sim_time < 1.0:
            return 0.0
        return self.total_served / (self._sim_time / 60.0)

    def reset(self) -> None:
        self.completed.clear()
        self.arrived.clear()
        self._sim_time = 0.0

    def summary(self) -> dict:
        return {
            "total_served": self.total_served,
            "total_arrived": self.total_arrived,
            "avg_wait": round(self.avg_wait_time, 2),
            "avg_trip": round(self.avg_trip_time, 2),
            "avg_total": round(self.avg_total_time, 2),
            "max_wait": round(self.max_wait_time, 2),
            "throughput": round(self.throughput, 2),
        }
