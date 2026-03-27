"""Proste widgety pygame: Button, Slider, Dropdown, SpinBox."""
from __future__ import annotations
import pygame
from . import colors


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        toggle: bool = False,
        active: bool = False,
    ) -> None:
        self.rect = rect
        self.label = label
        self.toggle = toggle
        self.active = active
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Zwraca True przy kliknięciu."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.active = not self.active
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        color = colors.BTN_ACTIVE if self.active else (colors.BTN_HOVER if self._hovered else colors.BTN)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, colors.ACCENT, self.rect, 1, border_radius=6)
        text = font.render(self.label, True, colors.BTN_TEXT)
        surface.blit(text, text.get_rect(center=self.rect.center))


class Slider:
    def __init__(
        self,
        rect: pygame.Rect,
        min_val: float,
        max_val: float,
        value: float,
        label: str = "",
        fmt: str = "{:.1f}x",
    ) -> None:
        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.label = label
        self.fmt = fmt
        self._dragging = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Zwraca True gdy wartość się zmieniła."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        if event.type == pygame.MOUSEMOTION and self._dragging:
            ratio = (event.pos[0] - self.rect.x) / self.rect.width
            ratio = max(0.0, min(1.0, ratio))
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        # Label
        if self.label:
            lbl = font.render(self.label, True, colors.TEXT_DIM)
            surface.blit(lbl, (self.rect.x, self.rect.y - 20))

        # Track
        track = pygame.Rect(self.rect.x, self.rect.centery - 3, self.rect.width, 6)
        pygame.draw.rect(surface, colors.SLIDER_TRACK, track, border_radius=3)

        # Fill
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_w = int(ratio * self.rect.width)
        if fill_w > 0:
            fill = pygame.Rect(self.rect.x, self.rect.centery - 3, fill_w, 6)
            pygame.draw.rect(surface, colors.SLIDER_FILL, fill, border_radius=3)

        # Thumb
        thumb_x = self.rect.x + fill_w
        pygame.draw.circle(surface, colors.SLIDER_THUMB, (thumb_x, self.rect.centery), 9)

        # Value label
        val_text = font.render(self.fmt.format(self.value), True, colors.TEXT)
        surface.blit(val_text, (self.rect.right + 8, self.rect.centery - 8))


class Dropdown:
    def __init__(self, rect: pygame.Rect, options: list[str], selected: int = 0) -> None:
        self.rect = rect
        self.options = options
        self.selected = selected
        self._open = False
        self._hovered_item = -1

    @property
    def value(self) -> str:
        return self.options[self.selected]

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Zwraca True gdy selekcja się zmieniła."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._open = not self._open
                return False
            if self._open:
                for i, item_rect in enumerate(self._item_rects()):
                    if item_rect.collidepoint(event.pos):
                        old = self.selected
                        self.selected = i
                        self._open = False
                        return self.selected != old
                self._open = False
        if event.type == pygame.MOUSEMOTION and self._open:
            self._hovered_item = -1
            for i, item_rect in enumerate(self._item_rects()):
                if item_rect.collidepoint(event.pos):
                    self._hovered_item = i
        return False

    def _item_rects(self) -> list[pygame.Rect]:
        rects = []
        for i in range(len(self.options)):
            rects.append(pygame.Rect(
                self.rect.x,
                self.rect.bottom + i * self.rect.height,
                self.rect.width,
                self.rect.height,
            ))
        return rects

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, colors.BTN, self.rect, border_radius=6)
        pygame.draw.rect(surface, colors.ACCENT, self.rect, 1, border_radius=6)
        text = font.render(self.value, True, colors.BTN_TEXT)
        surface.blit(text, text.get_rect(center=self.rect.center))
        # Arrow
        arrow = font.render("▼" if not self._open else "▲", True, colors.TEXT_DIM)
        surface.blit(arrow, (self.rect.right - 22, self.rect.centery - 8))

        if self._open:
            for i, (item_rect, opt) in enumerate(zip(self._item_rects(), self.options)):
                color = colors.BTN_HOVER if i == self._hovered_item else colors.BTN
                pygame.draw.rect(surface, color, item_rect)
                pygame.draw.rect(surface, colors.ACCENT, item_rect, 1)
                t = font.render(opt, True, colors.BTN_TEXT)
                surface.blit(t, t.get_rect(center=item_rect.center))


class SpinBox:
    """Liczba z przyciskami + i -."""
    def __init__(
        self,
        rect: pygame.Rect,
        min_val: int,
        max_val: int,
        value: int,
        label: str = "",
    ) -> None:
        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.label = label
        btn_w = 30
        self._btn_minus = pygame.Rect(rect.x, rect.y, btn_w, rect.height)
        self._btn_plus = pygame.Rect(rect.right - btn_w, rect.y, btn_w, rect.height)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_minus.collidepoint(event.pos) and self.value > self.min_val:
                self.value -= 1
                return True
            if self._btn_plus.collidepoint(event.pos) and self.value < self.max_val:
                self.value += 1
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.label:
            lbl = font.render(self.label, True, colors.TEXT_DIM)
            surface.blit(lbl, (self.rect.x, self.rect.y - 20))
        pygame.draw.rect(surface, colors.BTN, self.rect, border_radius=6)
        pygame.draw.rect(surface, colors.ACCENT, self.rect, 1, border_radius=6)
        # minus
        pygame.draw.rect(surface, colors.BTN_HOVER, self._btn_minus, border_radius=6)
        m = font.render("−", True, colors.BTN_TEXT)
        surface.blit(m, m.get_rect(center=self._btn_minus.center))
        # plus
        pygame.draw.rect(surface, colors.BTN_HOVER, self._btn_plus, border_radius=6)
        p = font.render("+", True, colors.BTN_TEXT)
        surface.blit(p, p.get_rect(center=self._btn_plus.center))
        # value
        val = font.render(str(self.value), True, colors.TEXT)
        surface.blit(val, val.get_rect(center=self.rect.center))
