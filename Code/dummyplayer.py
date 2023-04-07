import pygame
from settings import *

class DummyPlayer(pygame.sprite.Sprite):
    def __init__(self, pos, groups) -> None:
        super().__init__(groups)
        self.image = pygame.image.load('Assets/Assets/Images/playerDown.png').convert_alpha()
        # number of sprites contained in self.image
        sprites_per_width : int = self.image.get_width() / (TILE_WIDTH * MAP_ZOOM)
        #image_sprites_vertical : int = self.image.get_height() / (TILE_HEIGHT * MAP_ZOOM)
        self.image = self.image.subsurface((0, 0), (self.image.get_width() / sprites_per_width, self.image.get_height()))
        self.rect  = self.image.get_rect(topleft = pos)
        self.speed = 3
    
    def update(self) -> None:
        pass