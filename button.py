import pygame as pg
import constants as c


class Button:
    """A simple clickable button drawn entirely in code."""

    FONT = None  # initialised lazily after pg.init()

    def __init__(self, x, y, width, height, text, colour=c.GREY, hover_colour=None):
        self.rect = pg.Rect(x, y, width, height)
        self.text = text
        self.colour = colour
        self.hover_colour = hover_colour or self._lighten(colour)
        self.is_hovered = False
        self.enabled = True

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def draw(self, surface):
        if Button.FONT is None:
            Button.FONT = pg.font.SysFont("arial", 14, bold=True)

        bg = self.hover_colour if (self.is_hovered and self.enabled) else self.colour
        if not self.enabled:
            bg = self._darken(self.colour)

        pg.draw.rect(surface, bg, self.rect, border_radius=6)
        pg.draw.rect(surface, c.WHITE, self.rect, width=1, border_radius=6)

        label = Button.FONT.render(self.text, True, c.WHITE)
        lx = self.rect.centerx - label.get_width() // 2
        ly = self.rect.centery - label.get_height() // 2
        surface.blit(label, (lx, ly))

    def handle_event(self, event):
        """Return True on a valid left-click, False otherwise."""
        if event.type == pg.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.enabled and self.rect.collidepoint(event.pos):
                return True
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _lighten(colour):
        return tuple(min(255, v + 40) for v in colour)

    @staticmethod
    def _darken(colour):
        return tuple(max(0, v - 40) for v in colour)
