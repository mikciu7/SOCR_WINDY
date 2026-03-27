"""
Symulacja Windy — SOCZ Projekt
Uruchomienie: python main.py
"""
import sys
import random
import pygame

from simulation.clock import SimClock
from simulation.building import Building
from simulation.passenger import Passenger
from metrics.collector import MetricsCollector
from algorithms import ALGORITHMS, FCFSDispatcher, SCANDispatcher, LOOKDispatcher
from gui.building_view import BuildingView
from gui.control_panel import ControlPanel
from gui.metrics_panel import MetricsPanel
from gui import colors

# --- Stałe okna ---
WIN_W = 1280
WIN_H = 800
METRICS_H = 70
PANEL_W = 340
BUILD_W = WIN_W - PANEL_W
BUILD_H = WIN_H - METRICS_H

# --- Automatyczne generowanie pasażerów ---
AUTO_SPAWN_INTERVAL = 3.0  # sekundy symulacji między pasażerami


class AutoSpawner:
    def __init__(self) -> None:
        self._timer = 0.0
        self.interval = AUTO_SPAWN_INTERVAL

    def update(self, dt: float, sim_time: float, building: Building) -> None:
        self._timer += dt
        if self._timer >= self.interval:
            self._timer = 0.0
            self._spawn(sim_time, building)

    def _spawn(self, sim_time: float, building: Building) -> None:
        n = building.num_floors
        origin = random.randint(0, n - 1)
        dest = random.randint(0, n - 1)
        while dest == origin:
            dest = random.randint(0, n - 1)
        p = Passenger(origin_floor=origin, destination_floor=dest, arrival_time=sim_time)
        building.add_passenger(p)


def make_dispatcher(name: str, num_floors: int):
    cls = ALGORITHMS[name]
    if name == "SCAN":
        return cls(num_floors)
    return cls()


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Symulacja Windy — SOCZ")
    clock_real = pygame.time.Clock()

    # Fonty
    font = pygame.font.SysFont("segoeui", 18, bold=True)
    font_small = pygame.font.SysFont("segoeui", 15)

    # Stan symulacji
    sim_clock = SimClock()
    collector = MetricsCollector()
    current_algo = "FCFS"
    dispatcher = make_dispatcher(current_algo, 10)
    building = Building(
        num_floors=10,
        num_elevators=3,
        dispatcher=dispatcher,
        collector=collector,
    )
    auto_spawner = AutoSpawner()

    # Rects
    build_rect = pygame.Rect(0, 0, BUILD_W, BUILD_H)
    panel_rect = pygame.Rect(BUILD_W, 0, PANEL_W, WIN_H - METRICS_H)
    metrics_rect = pygame.Rect(0, WIN_H - METRICS_H, WIN_W, METRICS_H)

    # GUI
    building_view = BuildingView(building, build_rect)

    def on_algo_change(name: str) -> None:
        nonlocal current_algo, dispatcher
        current_algo = name
        dispatcher = make_dispatcher(name, building.num_floors)
        building.dispatcher = dispatcher

    def on_rebuild(num_floors: int, num_elevators: int) -> None:
        nonlocal dispatcher
        dispatcher = make_dispatcher(current_algo, num_floors)
        building.dispatcher = dispatcher
        building.collector = collector
        building.rebuild(num_floors, num_elevators)
        collector.reset()
        sim_clock.reset()

    def on_add_passenger(origin: int, dest: int) -> None:
        p = Passenger(origin_floor=origin, destination_floor=dest, arrival_time=sim_clock.sim_time)
        building.add_passenger(p)

    def on_reset() -> None:
        nonlocal dispatcher
        dispatcher = make_dispatcher(current_algo, building.num_floors)
        building.dispatcher = dispatcher
        building.reset()
        collector.reset()
        sim_clock.reset()

    control_panel = ControlPanel(
        rect=panel_rect,
        sim_clock=sim_clock,
        on_algo_change=on_algo_change,
        on_rebuild=on_rebuild,
        on_add_passenger=on_add_passenger,
        on_reset=on_reset,
    )
    metrics_panel = MetricsPanel(metrics_rect, collector)

    running = True
    while running:
        real_dt = clock_real.tick(60)
        sim_dt = sim_clock.tick(real_dt)
        collector.tick(sim_clock.sim_time)

        # --- Eventy ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            control_panel.handle_event(event)
            building_view.handle_event(event, on_add_passenger)

        # --- Update ---
        if control_panel.auto_spawn and sim_dt > 0:
            auto_spawner.update(sim_dt, sim_clock.sim_time, building)

        building.update(sim_dt, sim_clock.sim_time)

        # --- Draw ---
        screen.fill(colors.BG)
        building_view.draw(screen, font, font_small)
        control_panel.draw(screen, font, font_small)
        metrics_panel.draw(screen, font, font_small)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
