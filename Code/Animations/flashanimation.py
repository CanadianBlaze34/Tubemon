import pygame
import math
import time
from Animations.animation import Animation

class FlashAnimation(Animation):


    def __init__(self, duration : float, flash_cycles : float, color: pygame.color.Color) -> None:
        super().__init__(Animation.FLASH, duration)
        self.start_time = time.time()
        self.color = color
        self.finished = True
        # fade from nothing to color per 1 cycle. every added cycle should fade back into nothing and then into the color
        self.final_flash_step = (math.pi * (flash_cycles - 0.5)) / self.duration
        self.effect_area = pygame.Surface(pygame.display.get_surface().get_rect().size)
        self.effect_area.fill(self.color)
        
    def draw(self, display_surface : pygame.surface.Surface) -> None:
        # lerping the animation
        elapsed_time = time.time() - self.start_time
        current_step = elapsed_time * self.final_flash_step
        current_alpha = abs(int(255 * math.sin(current_step) )) # 255 is the max/total alpha value 
        self.effect_area.set_alpha(current_alpha)
        display_surface.blit(self.effect_area, self.effect_area.get_rect())