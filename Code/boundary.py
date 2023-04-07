from __future__ import annotations # https://stackoverflow.com/questions/33533148/how-do-i-type-hint-a-method-with-the-type-of-the-enclosing-class
import pygame
from settings import MAP_ZOOM, TILE_WIDTH, TILE_HEIGHT, M_WIDTH, M_HEIGHT, COLLISIONS

class Boundary(pygame.sprite.Sprite):

    _COLOR = 'red'

    def __init__(self, original_position : tuple(int, int), groups) -> None:
        super().__init__(groups)
        width  : int = TILE_WIDTH * MAP_ZOOM # the map is zoomed in by 400%
        height : int = TILE_HEIGHT * MAP_ZOOM # the map is zoomed in by 400%
        self.rect = pygame.Rect(original_position, (width, height))

    @staticmethod
    # only want one boundary image so all the boundaries will reference it
    def draw(boundaries : list[Boundary], display_surface : pygame.surface.Surface, offset : tuple(int, int) = tuple((0, 0))) -> None:
        for boundary in boundaries:
            # move the position away from the offset
            offset_pos = boundary.rect.topleft - offset
            rendered_rect = pygame.Rect(offset_pos, boundary.rect.size)
            # don't render if not visible on the screen
            # if boundary is visible on the screen:
            #   render boundary
            if display_surface.get_rect().colliderect(rendered_rect):
                pygame.draw.rect(display_surface, Boundary._COLOR, rendered_rect)
    
    @staticmethod
    def spawn_collisions(group : pygame.sprite.Group) -> list[Boundary]:
        collisions : list[Boundary] = []
        for y in range(M_HEIGHT):
            for x in range(M_WIDTH):
                # there are only 2 numbers in the collisions list
                # 0 is not the collision block number
                # making boundaries with indices that dont have a value of 0
                if COLLISIONS[x + y * M_WIDTH] != 0:
                    pos_x : int = x * MAP_ZOOM * TILE_WIDTH
                    pos_y : int = y * MAP_ZOOM * TILE_HEIGHT
                    collisions.append(Boundary((pos_x, pos_y), group))
        return collisions