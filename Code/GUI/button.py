from __future__ import annotations
from typing import Callable
from pygame import Color, Rect, mouse
from GUI.label import Label
from sound import try_sound, try_play
from pygame.mixer import Sound
from settings import MASTER_VOLUME

class Button(Label):

    SOUND : Sound = None 

    def __init__(self, groups, 
                 rect    : Rect, 
                 colors  : tuple[Color, Color, Color] | None = None,
                 text    : None | tuple[str, int, Color, str | None, tuple[int, int] | None, tuple[bool, bool] | None] = None, # text, size, color, font_path, position
                 border : None | tuple[Color, int]      = None,
                 active : bool = True,
                 visible : bool = True,
                 task : Callable = None,
                 ) -> None:

        colors = colors if colors else (None, None, None)
        super().__init__(groups, rect, colors[0], text, border, visible)
        
        if not Button.SOUND: 
            Button.INIT()
        
        # colors:
        # [0] = button color
        # [1] = hover color
        # [2] = clicked color
        # clicked feature
        self.clicked_position = None # should be a singleton variable
        self.clicked : bool = False # true when mouse presses in the button and releases in the button
        self.task : Callable = task
        
        # entered and exit features
        self.last_position = mouse.get_pos() # should be a singleton variable 
        self.entered : bool = False
        self.exit    : bool = False
        #
        self.colors = colors
        self.active = active

    def refresh_states(self) -> None:
        # clicked, entered and exit will only be active for one frame
        # click
        self.clicked = False
        # enter and exit
        self.entered = False
        self.exit = False
        # color should be first color unless something happens
        self.color = self.colors[0]

    def click(self, *args) -> None:

        mp : tuple[int, int] = args[0]
        clicked_position : tuple[int, int] = args[1]
        pressing_left_mouse : bool = args[2]
        
        if pressing_left_mouse: # left mouse button
            
            # the mouse button originally clicked inside this button and
            # is currently being held down inside this button
            if self.rect.collidepoint(clicked_position) and self.rect.collidepoint(mp):
                self.color = self.colors[2]

        else:
            
            # the mouse is inside the button this frame
            if self.rect.collidepoint(mp):

                # has clicked and released the mouse button inside this button
                if clicked_position and self.rect.collidepoint(clicked_position):
                    #print(f'{self.text[0]}: released')
                    self.clicked = True
                    try_play(Button.SOUND)
                
                # the mouse is hovering over this button and the mouse button is not being held
                self.color = self.colors[1]
       
    def enter_exit(self, *args) -> None:

        mp : tuple[int, int] = args[0]
        
        # mouse hasn't moved since last frame
        if self.last_position != mp:
            last_position_inside    : bool = self.rect.collidepoint(self.last_position)
            current_position_inside : bool = self.rect.collidepoint(mp)
            # last position is outside of button and current mouse position is inside the button
            self.entered = not last_position_inside and     current_position_inside
            # last position is inside of button and current mouse position is outside the button
            self.exit    =     last_position_inside and not current_position_inside

        #if self.entered: print(f'{self.text[0]}: entered.')
        #if self.exit:    print(f'{self.text[0]}: exit.')

        self.last_position = mp

    def update(self, *args) -> None:
        self.refresh_states()
        if not self.active: return
        self.click(*args)
        self.enter_exit(*args)

    def deactivate(self) -> None:
        super().deactivate()
        self.active = False

    def activate(self) -> None:
        super().activate()
        self.active = True

    @staticmethod
    def INIT() -> None:
        Button.SOUND = try_sound('Assets/NinjaAdventure(SupporterEdition)/Sounds/Menu/Menu4.wav')

    @staticmethod
    def update_all_tasks(buttons : list[Button]) -> None:
        for button in buttons:
            button.update()
            if button.clicked:
                button.task()

    @staticmethod
    def deactivate_all(buttons : list[Button]) -> None:
        for button in buttons:
            button.deactivate()

    @staticmethod
    def activate_all(buttons : list[Button]) -> None:
        for button in buttons:
            button.activate()