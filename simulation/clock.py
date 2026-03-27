class SimClock:
    def __init__(self) -> None:
        self.sim_time: float = 0.0
        self.speed: float = 1.0   # mnożnik: 0.25 – 20.0
        self.paused: bool = False

    def tick(self, real_dt_ms: int) -> float:
        """Przesuwa zegar symulacji. Zwraca dt w sekundach symulacji."""
        if self.paused:
            return 0.0
        dt = (real_dt_ms / 1000.0) * self.speed
        self.sim_time += dt
        return dt

    def reset(self) -> None:
        self.sim_time = 0.0
        self.paused = False
