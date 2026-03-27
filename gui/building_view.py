"""Wizualizacja budynku z szybami, windami i pasażerami."""
from __future__ import annotations
import pygame
from simulation.building import Building
from simulation.elevator import ElevatorState
from . import colors

SHAFT_W = 60          # szerokość szybu
SHAFT_GAP = 20        # odstęp między szybami
FLOOR_H = 58          # wysokość piętra
MARGIN_LEFT = 60      # margines dla numerów pięter
MARGIN_TOP = 20
MARGIN_BOTTOM = 20
ELEV_W = 44
ELEV_H = 48
PASSENGER_R = 5       # promień kropki pasażera


class BuildingView:
    def __init__(self, building: Building, rect: pygame.Rect) -> None:
        self.building = building
        self.rect = rect
        self._manual_from: int | None = None   # klik piętro startowe (ręczny pasażer)

    def _floor_y(self, floor: int) -> int:
        """Y górnej krawędzi piętra (piętro 0 = dół)."""
        n = self.building.num_floors
        total_h = n * FLOOR_H
        base_y = self.rect.y + MARGIN_TOP + total_h
        return base_y - (floor + 1) * FLOOR_H

    def _shaft_x(self, elev_id: int) -> int:
        return self.rect.x + MARGIN_LEFT + elev_id * (SHAFT_W + SHAFT_GAP)

    def handle_event(self, event: pygame.event.Event, add_passenger_cb) -> None:
        """Klik w piętro = ręczne dodawanie pasażera (2 kliki: skąd, dokąd)."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            floor = self._hit_floor(event.pos)
            if floor is not None:
                if self._manual_from is None:
                    self._manual_from = floor
                else:
                    origin = self._manual_from
                    dest = floor
                    self._manual_from = None
                    if origin != dest:
                        add_passenger_cb(origin, dest)

    def _hit_floor(self, pos: tuple[int, int]) -> int | None:
        """Zwraca numer piętra pod kursorem, lub None."""
        if not self.rect.collidepoint(pos):
            return None
        for floor in range(self.building.num_floors):
            y = self._floor_y(floor)
            if y <= pos[1] <= y + FLOOR_H:
                return floor
        return None

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, font_small: pygame.font.Font) -> None:
        # Tło widoku
        pygame.draw.rect(surface, colors.BG, self.rect)

        n = self.building.num_floors
        ne = self.building.num_elevators
        total_shaft_w = ne * SHAFT_W + (ne - 1) * SHAFT_GAP

        # --- Rysuj piętra i szyby ---
        for floor in range(n):
            y = self._floor_y(floor)

            # Linia piętra
            pygame.draw.line(surface, colors.FLOOR_LINE,
                             (self.rect.x + MARGIN_LEFT - 5, y + FLOOR_H),
                             (self.rect.x + MARGIN_LEFT + total_shaft_w + 10, y + FLOOR_H), 1)

            # Numer piętra
            label = font_small.render(str(floor), True, colors.FLOOR_NUM)
            surface.blit(label, (self.rect.x + 5, y + FLOOR_H // 2 - 8))

            # Tło szybów
            for eid in range(ne):
                sx = self._shaft_x(eid)
                shaft_rect = pygame.Rect(sx, y, SHAFT_W, FLOOR_H)
                pygame.draw.rect(surface, colors.SHAFT, shaft_rect)

            # Pasażerowie czekający na tym piętrze
            waiting = self.building.floors[floor].all_waiting
            self._draw_waiting_passengers(surface, floor, waiting, total_shaft_w)

            # Podświetlenie przy ręcznym dodawaniu
            if self._manual_from == floor:
                hl = pygame.Rect(self.rect.x + MARGIN_LEFT, y, total_shaft_w, FLOOR_H)
                s = pygame.Surface((hl.width, hl.height), pygame.SRCALPHA)
                s.fill((60, 140, 220, 60))
                surface.blit(s, hl.topleft)

        # --- Rysuj windy ---
        for elev in self.building.elevators:
            self._draw_elevator(surface, elev, font_small)

        # --- Podpowiedź ręczny pasażer ---
        if self._manual_from is not None:
            hint = font_small.render(
                f"Wybierz piętro docelowe (start: {self._manual_from})",
                True, colors.TEXT_WARN,
            )
            surface.blit(hint, (self.rect.x + 10, self.rect.bottom - 22))

    def _draw_waiting_passengers(
        self,
        surface: pygame.Surface,
        floor: int,
        waiting: list,
        total_shaft_w: int,
    ) -> None:
        if not waiting:
            return
        y = self._floor_y(floor)
        x_start = self.rect.x + MARGIN_LEFT + self.building.num_elevators * (SHAFT_W + SHAFT_GAP) + 8
        for i, p in enumerate(waiting[:10]):
            cx = x_start + (i % 5) * (PASSENGER_R * 2 + 3)
            cy = y + FLOOR_H // 2 + (i // 5) * (PASSENGER_R * 2 + 2) - 4
            pygame.draw.circle(surface, colors.PASSENGER_WAIT, (cx, cy), PASSENGER_R)
        if len(waiting) > 10:
            font_tiny = pygame.font.SysFont(None, 14)
            t = font_tiny.render(f"+{len(waiting)-10}", True, colors.TEXT_DIM)
            surface.blit(t, (x_start, y + FLOOR_H - 14))

    def _draw_elevator(self, surface: pygame.Surface, elev, font_small: pygame.font.Font) -> None:
        sx = self._shaft_x(elev.id)
        # Ciągła pozycja Y
        ey = self._floor_y(0) + FLOOR_H - ELEV_H - int(elev.position * FLOOR_H)
        ex = sx + (SHAFT_W - ELEV_W) // 2

        elev_rect = pygame.Rect(ex, ey, ELEV_W, ELEV_H)

        # Kolor windy zależny od stanu
        if elev.state in (ElevatorState.DOOR_OPENING, ElevatorState.DOOR_OPEN, ElevatorState.DOOR_CLOSING):
            body_color = colors.DOOR_OPEN
        else:
            body_color = colors.ELEVATOR

        pygame.draw.rect(surface, body_color, elev_rect, border_radius=4)
        pygame.draw.rect(surface, colors.ACCENT, elev_rect, 1, border_radius=4)

        # Drzwi – animacja
        door_ratio = elev.door_open_ratio
        gap = int(door_ratio * (ELEV_W // 2 - 4))
        door_left = pygame.Rect(ex + 4, ey + 8, ELEV_W // 2 - 4 - gap, ELEV_H - 16)
        door_right = pygame.Rect(ex + ELEV_W // 2 + gap, ey + 8, ELEV_W // 2 - 4 - gap, ELEV_H - 16)
        pygame.draw.rect(surface, colors.ELEVATOR_DOOR, door_left, border_radius=2)
        pygame.draw.rect(surface, colors.ELEVATOR_DOOR, door_right, border_radius=2)

        # ID windy
        id_txt = font_small.render(f"W{elev.id + 1}", True, colors.TEXT)
        surface.blit(id_txt, id_txt.get_rect(centerx=ex + ELEV_W // 2, y=ey + 2))

        # Liczba pasażerów w środku
        if elev.passengers:
            cnt = font_small.render(str(len(elev.passengers)), True, colors.PASSENGER_IN)
            surface.blit(cnt, cnt.get_rect(centerx=ex + ELEV_W // 2, y=ey + ELEV_H - 16))

        # Strzałka kierunku
        if elev.direction == 1:
            arrow = "▲"
        elif elev.direction == -1:
            arrow = "▼"
        else:
            arrow = ""
        if arrow:
            a_txt = font_small.render(arrow, True, colors.TEXT_DIM)
            surface.blit(a_txt, (sx + SHAFT_W - 16, self._floor_y(elev.current_floor) + 4))
