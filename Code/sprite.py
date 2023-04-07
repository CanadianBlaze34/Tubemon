from __future__ import annotations
import pygame
from settings import MAP_ZOOM

class Sprite:
    def __init__(self, position, image : pygame.surface.Surface) -> None:
        # TODO/FIX: image has a rect, sprite doesn't need to exist as a class
        self.image = image
        self.rect  = self.image.get_rect(topleft = position)

    def draw(self, display_surface : pygame.surface.Surface):
        display_surface.blit(self.image, self.rect.topleft)

    def scale(self, size) -> None:
        self.image = pygame.transform.scale(self.image, size)

    def smooth_scale(self, size) -> None:
        self.image = pygame.transform.smoothscale(self.image, size)

    @staticmethod
    def load_image_alpha(position, image_path : str) -> Sprite:
        return Sprite(position, pygame.image.load(image_path).convert_alpha())
    
    @staticmethod
    def load_image(position, image_path : str) -> Sprite:
        return Sprite(position, pygame.image.load(image_path).convert())
    
    @staticmethod
    def load_image_scaled(image_path : str, position : tuple[int, int] = (0, 0),  scale : float = 1, alpha : bool = False) -> Sprite:
        if alpha : image : pygame.Surface = pygame.image.load(image_path).convert_alpha()
        else     : image : pygame.Surface = pygame.image.load(image_path).convert()
    
        image = pygame.transform.scale(image, pygame.Vector2(image.get_size()) * scale)
        return Sprite(position, image)

    @staticmethod
    def load_surfaces_alpha(image_path : str, size : tuple[int, int], sprites_num: tuple[int, int]) -> list[pygame.surface.Surface]:
        full_image = pygame.image.load(image_path).convert_alpha()
        sprites = []
        # Order of sprite image
        # 0, 1, 2
        # 3, 4, 5
        for x in range(sprites_num[0]):
            for y in range(sprites_num[1]):
                sprites.append(full_image.subsurface((x * size[0], y * size[1]), size))
        return sprites

    @staticmethod
    def load_monsters(image_path : str, sprites_num: tuple[int, int]) -> list[list[pygame.surface.Surface]]:
        full_image = pygame.image.load(image_path).convert_alpha()
        # first index is front sprite
        # second index is back sprite
        sprites = [[],[]]
        size = pygame.Vector2(16, 16)
        # order of imported image
        # (0, 0), (1, 0), (2, 0), (3, 0)
        # (0, 1), (1, 1), (2, 1), (3, 1)
        # (0, 2), (1, 2), (2, 2), (3, 2)
        # (0, 3), (1, 3), (2, 3), (3, 3)
        # Order of sprites
        # (0, 0), (0, 1), (0, 2), (0, 3)
        # (1, 0), (1, 1), (1, 2), (1, 3)
        for x in range(sprites_num[0]): # row
            for y in range(sprites_num[1]): # column
                sprites[x].append(pygame.transform.scale(full_image.subsurface((x * size.x, y * size.y), size), size * 6))
                #sprites[x].append(full_image.subsurface((x * size.x, y * size.y), size))
        return sprites


        
