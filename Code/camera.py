import pygame
from settings import *
from threading import Lock

class Camera:
    def __init__(self) -> None:
        self.display_surface = pygame.display.get_surface()
        self.half_width      = self.display_surface.get_width() // 2
        self.half_height     = self.display_surface.get_height() // 2
        self.offset          = pygame.math.Vector2()

    def update(self, rect : pygame.rect.Rect) -> None:
        self.offset.x = rect.centerx - self.half_width
        self.offset.y = rect.centery - self.half_height

    def draw(self, sprites : list):
        for sprite in sprites:
            
            offset_pos = sprite.rect.topleft - self.offset
            # don't render if not visible on the screen
            if self.display_surface.get_rect().colliderect(sprite.image.get_rect(topleft = offset_pos)):
                self.display_surface.blit(sprite.image, offset_pos)