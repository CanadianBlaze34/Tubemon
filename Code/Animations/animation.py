import pygame
import math
import time

class Animation:

    # animation types
    FLASH : int = 0

    def __init__(self, animation_type : int, duration : float) -> None:
        self.animation_type = animation_type
        self.duration = duration

    def start(self) -> None:
        self.finished = False
        self.start_time = time.time()

    def update(self):
        if self.finished:
            return 
        current_time = time.time()
        self.finished = current_time - self.start_time > self.duration

    def draw(self, display_surface : pygame.surface.Surface) -> None:
        pass