from __future__ import annotations
from typing import Callable
from pygame import Color, Rect, Surface, mouse
from GUI.label import Label
from GUI.button import Button

class Slider(Label):

    def __init__(self, groups, 
                 rects   : tuple[Rect, Rect, Rect], # text, button, bar
                 colors  : tuple[Color, Color, Color],
                 text    : None | tuple[str, int, Color, str | None, tuple[int, int] | None, tuple[bool, bool] | None] = None, # text, size, color, font_path, position
                 border  : None | tuple[Color, int]      = None,
                 active  : bool = True,
                 visible : bool = True,
                 ) -> None:

        colors = colors if colors else (None, None, None)
        super().__init__(groups, rects[0], None, text, border, visible)
        
        # colors:
        # [0] = button color
        # [1] = hover/pressed button color
        # [2] = bar color

        # the button that moves along the bar
        self.button = Button(groups, rects[1], (colors[0], colors[1], colors[1]), None, None, active, visible)
        self.bar = Label(groups, rects[2], colors[2], None, None, visible)

        self.holding = False
        self.active = active
        self.clicked_position = None

    def update(self, *args) -> None:

        super().update(*args)
        self.bar.update(*args)
        self.button.update(*args)

        mp : tuple[int, int] = args[0]
        clicked_position : tuple[int, int] = args[1]
        pressing_left_mouse : bool = args[2]

        # clicked_position is set when pressing_left_mouse is True
        if pressing_left_mouse:
            
            # holding is true when the mouse originally clicked inside the button.
            # this prevents the mouse from holding the mouse button outside of the button and
            # going into it while pressed then activating the holding bool
            if not self.holding:
                self.holding = self.button.rect.collidepoint(clicked_position)

            # the mouse button originally pressed inside this button and
            # is currently being held down
            if self.holding:
                # move the slider along the bar
                # the slider position shouldn't be less than the bars x position
                # the slider position shouldn't be greater than the bars width position
                slider_x_position = min(max(self.bar.rect.x, mp[0]), self.bar.rect.right)
                self.button.rect.centerx = slider_x_position
        
        else:
            self.holding = False

    def deactivate(self) -> None:
        super().deactivate()
        self.button.deactivate()
        self.bar.deactivate()
        self.active = False

    def activate(self) -> None:
        super().activate() 
        self.button.activate()
        self.bar.activate()
        self.active = True

    def draw(self, display_surface : Surface) -> None:
        super().draw(display_surface) # text
        self.bar.draw(display_surface)
        self.button.draw(display_surface)
