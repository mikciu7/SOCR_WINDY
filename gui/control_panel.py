"""Panel kontrolny po prawej stronie okna."""
from __future__ import annotations
import pygame
from simulation.clock import SimClock
from . import colors
from .widgets import Button, Slider, Dropdown, SpinBox

ALGO_NAMES = ["FCFS", "SSTF", "SCAN", "LOOK"]


class ControlPanel:
    def __init__(
        self,
        rect: pygame.Rect,
        sim_clock: SimClock,
        on_algo_change,
        on_rebuild,
        on_add_passenger,
        on_reset,
    ) -> None:
        self.rect = rect
        self.sim_clock = sim_clock
        self.on_algo_change = on_algo_change
        self.on_rebuild = on_rebuild
        self.on_add_passenger = on_add_passenger
        self.on_reset = on_reset

        x = rect.x + 16
        w = rect.width - 32

        # Suwak prędkości
        self.slider_speed = Slider(
            pygame.Rect(x, rect.y + 80, w - 60, 20),
            min_val=0.25, max_val=20.0, value=1.0,
            label="Prędkość symulacji",
            fmt="{:.2f}x",
        )

        # Dropdown algorytm
        self.dropdown_algo = Dropdown(
            pygame.Rect(x, rect.y + 160, w, 36),
            options=ALGO_NAMES,
            selected=0,
        )

        # SpinBox piętra
        self.spin_floors = SpinBox(
            pygame.Rect(x, rect.y + 260, w, 36),
            min_val=3, max_val=20, value=10,
            label="Liczba pięter",
        )

        # SpinBox windy
        self.spin_elevators = SpinBox(
            pygame.Rect(x, rect.y + 340, w, 36),
            min_val=1, max_val=8, value=3,
            label="Liczba wind",
        )

        # Przyciski
        bh = 38
        self.btn_rebuild = Button(pygame.Rect(x, rect.y + 410, w, bh), "Zastosuj konfigurację")
        self.btn_add = Button(pygame.Rect(x, rect.y + 460, w, bh), "Dodaj pasażera (klik w budynek)")
        self.btn_auto = Button(pygame.Rect(x, rect.y + 510, w, bh), "Auto: WYŁ", toggle=True)
        self.btn_pause = Button(pygame.Rect(x, rect.y + 560, w, bh), "Pauza", toggle=True)
        self.btn_reset = Button(pygame.Rect(x, rect.y + 620, w, bh), "Reset")

        self._prev_algo = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        self.slider_speed.handle_event(event)
        self.sim_clock.speed = self.slider_speed.value

        if self.dropdown_algo.handle_event(event):
            self.on_algo_change(self.dropdown_algo.value)

        self.spin_floors.handle_event(event)
        self.spin_elevators.handle_event(event)

        if self.btn_rebuild.handle_event(event):
            self.on_rebuild(self.spin_floors.value, self.spin_elevators.value)

        if self.btn_auto.handle_event(event):
            label = "Auto: WŁ" if self.btn_auto.active else "Auto: WYŁ"
            self.btn_auto.label = label

        if self.btn_pause.handle_event(event):
            self.sim_clock.paused = self.btn_pause.active
            self.btn_pause.label = "Wznów" if self.btn_pause.active else "Pauza"

        if self.btn_reset.handle_event(event):
            self.on_reset()

    @property
    def auto_spawn(self) -> bool:
        return self.btn_auto.active

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, font_small: pygame.font.Font) -> None:
        pygame.draw.rect(surface, colors.BG_PANEL, self.rect)
        pygame.draw.line(surface, colors.SHAFT_LINE,
                         (self.rect.x, self.rect.y),
                         (self.rect.x, self.rect.bottom), 1)

        # Tytuł
        title = font.render("Panel sterowania", True, colors.TEXT_TITLE)
        surface.blit(title, (self.rect.x + 16, self.rect.y + 16))

        # Sekcja: prędkość
        self.slider_speed.draw(surface, font_small)

        # Sekcja: algorytm
        algo_lbl = font_small.render("Algorytm sterowania:", True, colors.TEXT_DIM)
        surface.blit(algo_lbl, (self.rect.x + 16, self.rect.y + 140))
        self.dropdown_algo.draw(surface, font_small)

        # Sekcja: konfiguracja
        cfg_lbl = font_small.render("Konfiguracja:", True, colors.TEXT_DIM)
        surface.blit(cfg_lbl, (self.rect.x + 16, self.rect.y + 228))
        self.spin_floors.draw(surface, font_small)
        self.spin_elevators.draw(surface, font_small)

        # Przyciski
        self.btn_rebuild.draw(surface, font_small)
        self.btn_add.draw(surface, font_small)
        self.btn_auto.draw(surface, font_small)
        self.btn_pause.draw(surface, font_small)
        self.btn_reset.draw(surface, font_small)

        # Czas symulacji
        time_lbl = font_small.render(
            f"Czas symulacji: {self.sim_clock.sim_time:.1f}s",
            True, colors.TEXT_DIM,
        )
        surface.blit(time_lbl, (self.rect.x + 16, self.rect.bottom - 40))
