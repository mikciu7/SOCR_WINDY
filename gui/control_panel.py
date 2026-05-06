"""Panel kontrolny po prawej stronie okna."""
from __future__ import annotations
import json
from pathlib import Path
import pygame
from simulation.clock import SimClock
from . import colors
from .widgets import Button, Slider, Dropdown, SpinBox

ALGO_NAMES = ["FCFS", "SSTF", "SCAN", "LOOK"]
NUM_ELEVATORS = 2  # zawsze stałe

_SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"


def _load_scenario_names() -> list[str]:
    if not _SCENARIOS_DIR.exists():
        return []
    return [p.stem for p in sorted(_SCENARIOS_DIR.glob("*.json"))]


class ControlPanel:
    def __init__(
        self,
        rect: pygame.Rect,
        sim_clock: SimClock,
        on_algo_change,
        on_rebuild,
        on_load_scenario,
        on_reset,
    ) -> None:
        self.rect = rect
        self.sim_clock = sim_clock
        self.on_algo_change = on_algo_change
        self.on_rebuild = on_rebuild
        self.on_load_scenario = on_load_scenario
        self.on_reset = on_reset

        x = rect.x + 16
        w = rect.width - 32
        bh = 36

        # Suwak prędkości
        self.slider_speed = Slider(
            pygame.Rect(x, rect.y + 76, w - 60, 20),
            min_val=0.25, max_val=20.0, value=1.0,
            label="Prędkość symulacji",
            fmt="{:.2f}x",
        )

        # Dropdown algorytm
        self.dropdown_algo = Dropdown(
            pygame.Rect(x, rect.y + 152, w, bh),
            options=ALGO_NAMES,
            selected=0,
        )

        # SpinBox piętra (windy zawsze = 2, bez spinnera)
        self.spin_floors = SpinBox(
            pygame.Rect(x, rect.y + 236, w, bh),
            min_val=3, max_val=20, value=10,
            label="Liczba pięter  (windy: zawsze 2)",
        )
        self.btn_rebuild = Button(
            pygame.Rect(x, rect.y + 286, w, bh), "Zastosuj konfigurację"
        )

        # Scenariusze
        self._scenario_names = _load_scenario_names()
        scenario_labels = self._scenario_names if self._scenario_names else ["(brak)"]
        self.dropdown_scenario = Dropdown(
            pygame.Rect(x, rect.y + 374, w, bh),
            options=scenario_labels,
            selected=0,
        )
        self.btn_load = Button(
            pygame.Rect(x, rect.y + 424, w, bh), "Załaduj scenariusz"
        )

        # Sterowanie
        self.btn_add  = Button(pygame.Rect(x, rect.y + 478, w, bh), "Dodaj pasażera (klik w budynek)")
        self.btn_auto = Button(pygame.Rect(x, rect.y + 524, w, bh), "Auto: WYŁ", toggle=True)
        self.btn_pause = Button(pygame.Rect(x, rect.y + 570, w, bh), "Pauza", toggle=True)
        self.btn_reset = Button(pygame.Rect(x, rect.y + 626, w, bh), "Reset")

    def handle_event(self, event: pygame.event.Event) -> None:
        # Gdy dropdown jest otwarty — obsługuj tylko jego eventy, resztę blokuj
        if self.dropdown_algo._open:
            if self.dropdown_algo.handle_event(event):
                self.on_algo_change(self.dropdown_algo.value)
            return
        if self.dropdown_scenario._open:
            if self.dropdown_scenario.handle_event(event):
                pass  # zmiana selekcji — nie ładuj automatycznie
            return

        self.slider_speed.handle_event(event)
        self.sim_clock.speed = self.slider_speed.value

        if self.dropdown_algo.handle_event(event):
            self.on_algo_change(self.dropdown_algo.value)

        self.spin_floors.handle_event(event)

        if self.btn_rebuild.handle_event(event):
            self.on_rebuild(self.spin_floors.value)

        if self.dropdown_scenario.handle_event(event):
            pass  # zmiana selekcji

        if self.btn_load.handle_event(event) and self._scenario_names:
            chosen = self._scenario_names[self.dropdown_scenario.selected]
            path = _SCENARIOS_DIR / f"{chosen}.json"
            with open(path, encoding="utf-8") as f:
                scenario = json.load(f)
            self.on_load_scenario(scenario)

        if self.btn_auto.handle_event(event):
            self.btn_auto.label = "Auto: WŁ" if self.btn_auto.active else "Auto: WYŁ"

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

        x = self.rect.x + 16

        # Tytuł
        surface.blit(font.render("Panel sterowania", True, colors.TEXT_TITLE), (x, self.rect.y + 14))

        # Prędkość
        self.slider_speed.draw(surface, font_small)

        # Algorytm
        surface.blit(font_small.render("Algorytm sterowania:", True, colors.TEXT_DIM), (x, self.rect.y + 132))
        self.dropdown_algo.draw(surface, font_small)

        # Konfiguracja
        surface.blit(font_small.render("Konfiguracja budynku:", True, colors.TEXT_DIM), (x, self.rect.y + 214))
        self.spin_floors.draw(surface, font_small)
        self.btn_rebuild.draw(surface, font_small)

        # Scenariusze
        surface.blit(font_small.render("Scenariusz testowy:", True, colors.TEXT_DIM), (x, self.rect.y + 354))
        self.dropdown_scenario.draw(surface, font_small)
        self.btn_load.draw(surface, font_small)

        # Sterowanie
        self.btn_add.draw(surface, font_small)
        self.btn_auto.draw(surface, font_small)
        self.btn_pause.draw(surface, font_small)
        self.btn_reset.draw(surface, font_small)

        # Czas symulacji
        surface.blit(
            font_small.render(f"Czas symulacji: {self.sim_clock.sim_time:.1f}s", True, colors.TEXT_DIM),
            (x, self.rect.bottom - 40),
        )

        # Otwarte listy rysuj na samym końcu — zawsze na wierzchu
        self.dropdown_algo.draw_overlay(surface, font_small)
        self.dropdown_scenario.draw_overlay(surface, font_small)
