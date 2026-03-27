"""Pasek metryk na dole ekranu."""
from __future__ import annotations
import pygame
from metrics.collector import MetricsCollector
from . import colors


class MetricsPanel:
    def __init__(self, rect: pygame.Rect, collector: MetricsCollector) -> None:
        self.rect = rect
        self.collector = collector

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, font_small: pygame.font.Font) -> None:
        pygame.draw.rect(surface, colors.METRICS_BG, self.rect)
        pygame.draw.line(surface, colors.SHAFT_LINE,
                         (self.rect.x, self.rect.y),
                         (self.rect.right, self.rect.y), 1)

        c = self.collector
        metrics = [
            ("Obsłużeni", str(c.total_served), colors.TEXT_GOOD),
            ("Oczekujący", str(c.total_arrived - c.total_served), colors.TEXT_WARN),
            ("Śr. czas czek.", f"{c.avg_wait_time:.1f}s", colors.TEXT),
            ("Śr. czas jazdy", f"{c.avg_trip_time:.1f}s", colors.TEXT),
            ("Maks. czek.", f"{c.max_wait_time:.1f}s",
             colors.TEXT_BAD if c.max_wait_time > 30 else colors.TEXT),
            ("Przepust.", f"{c.throughput:.1f}/min", colors.TEXT),
        ]

        col_w = self.rect.width // len(metrics)
        for i, (label, value, color) in enumerate(metrics):
            cx = self.rect.x + i * col_w + col_w // 2
            lbl = font_small.render(label, True, colors.TEXT_DIM)
            val = font.render(value, True, color)
            surface.blit(lbl, lbl.get_rect(centerx=cx, y=self.rect.y + 8))
            surface.blit(val, val.get_rect(centerx=cx, y=self.rect.y + 28))
