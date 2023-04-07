from __future__ import annotations
from pygame import Color, Rect, Surface, draw, font, draw, Vector2
from pygame.sprite import Sprite
from typing import Optional

class Label(Sprite):

    def __init__(self, groups,
                 rect   : Rect,
                 color  : Color | None = None,
                 text   : None | tuple[str, int, Color, Optional[str], Optional[tuple[int, int]], Optional[tuple[bool, bool]]] = None, # text, size, color, font_path, position
                 border : None | tuple[Color, int] = None,
                 visible : bool = True,
                 ) -> None:
        super().__init__(groups)
        
        #self.image = Surface(rect.size)
        #self.image.fill(color)
        self.rect  : Rect = rect
        self.image : Surface = None
        self.color = color
        self.text = text
        self.border = border
        self.visible : bool = visible

    def update(self, *args) -> None:
        pass
    
    def deactivate(self) -> None:
        self.visible = False

    def activate(self) -> None:
        self.visible = True

    def message(self, msg : str) -> None:
        l = len(self.text)
        self.text = (msg, # text
                     self.text[1], # size
                     self.text[2], # color
                     self.text[3] if l > 3 else None, # font_path
                     self.text[4] if l > 4 else None, # position 
                     self.text[5] if l > 5 else None) # center

    def update_message(self, msg : Optional[str] = None, size : Optional[int] = None, color : Color | None = None, font_path : str | None = None, pos : tuple[int, int] | None = None, center : tuple[bool, bool] | None = None) -> None:
        l = len(self.text)
        self.text = (msg       or self.text[0], # text
                     size      or self.text[1], # size
                     color     or self.text[2], # color
                     font_path if font_path else self.text[3] if l > 3 else None, # font_path
                     pos       if pos       else self.text[4] if l > 4 else None,  # position
                     center    if center    else self.text[5] if l > 5 else None
        )

    def draw(self, display_surface : Surface) -> None:
        if not self.visible: return
        #display_surface.blit(self.image, self.rect)
        if self.image:
            display_surface.blit(self.image, self.rect)
        # rect does not have an area to draw itself, or color is none
        elif self.rect.bottomright != self.rect.topleft and self.color: # rect has an area to draw 
            draw.rect(display_surface, self.color, self.rect)
        if self.text:
            self.draw_text(display_surface, self)
        if self.border:
            draw.rect(display_surface, self.border[0], self.rect, self.border[1])

    @staticmethod
    def draw_text(display_surface : Surface, label : Label) -> None:
        text_str : str             = label.text[0]
        size     : int             = label.text[1]
        color    : Color           = label.text[2]
        
        font_path: str             = label.text[3] if len(label.text) > 3 else None
        if font_path: font_ : font.Font = font.Font(font_path, size)
        else:         font_ : font.Font = font.SysFont('comicsans', size)
        
        text     : Surface         = font_.render(text_str, True, color)

        # (False, False) if there is no center or center is null 
        center : tuple[bool, bool] = label.text[5] if len(label.text) > 5 and label.text[5] else (False, False)

        # position
        # if given a position to place the text
        if len(label.text) > 4 and label.text[4]:
            position : Vector2 = Vector2(label.rect.x + label.text[4][0], label.rect.y + label.text[4][1])
            # center the x position
            if center[0]: position.x = label.rect.x + round((label.rect.w - text.get_width() ) / 2)
            # center the y position
            if center[1]: position.y = label.rect.y + round((label.rect.h - text.get_height()) / 2)
       
        else: # text centered in the button
            position : tuple[int, int] = (label.rect.x + round((label.rect.w - text.get_width() ) / 2),
                                          label.rect.y + round((label.rect.h - text.get_height()) / 2))
        #display_surface.blit(text, position)
        Label.blit_text(display_surface, text_str, position, font_, color)

    @staticmethod
    def blit_text(surface : Surface, text : str, pos : tuple[int, int], font : font.Font, color = Color('black')):
        # https://stackoverflow.com/questions/42014195/rendering-text-with-multiple-lines-in-pygame
        words = [word.split(' ') for word in text.splitlines()]  # 2D array where each row is a list of words.
        space = font.size(' ')[0]  # The width of a space.
        max_width, _ = surface.get_size() # max_width, max_height
        x, y = pos
        for line in words:
            for word in line:
                word_surface = font.render(word, 0, color)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width:
                    x = pos[0]  # Reset the x.
                    y += word_height  # Start on new row.
                surface.blit(word_surface, (x, y))
                x += word_width + space
            x = pos[0]  # Reset the x.
            y += word_height  # Start on new row.







