import pygame
from settings import *
from monster import Monster
from ITEMS.item import Item

class Player(pygame.sprite.Sprite):

    # The maximum amount of tubemon that can be carried
    TUBEMON_CAPACITY = 6

    def __init__(self, pos, groups, collide_group : pygame.sprite.Group) -> None:
        super().__init__(groups)

        # chracter sprite
        #self.original_image = pygame.image.load('Assets/Assets/Images/playerDown.png').convert_alpha()
        # number of sprites contained in self.image
        self.ANIMATIONS_FRAMES : int = 4
        #image_sprites_vertical : int = self.image.get_height() / (TILE_HEIGHT * MAP_ZOOM)
        #self.image = self.original_image.subsurface((0, 0), (self.original_image.get_width() / self.sprites_per_image, self.original_image.get_height()))
        
        
        # animation
        self.frames : int = 0
        self.elapsed : int = 0
        self.elapsed_max : int = 10
        self.moving = False
        self.direction_str = DOWN

        r = pygame.image.load('Assets/Assets/Images/playerRight.png').convert_alpha() # right
        l = pygame.image.load('Assets/Assets/Images/playerLeft.png') .convert_alpha() # left
        u = pygame.image.load('Assets/Assets/Images/playerUp.png')   .convert_alpha() # up
        d = pygame.image.load('Assets/Assets/Images/playerDown.png') .convert_alpha() # down
        w = TILE_WIDTH * MAP_ZOOM # width
        h = 68                    # height
        s = (w, h)                # size

        self.sprites : dict[str, list[pygame.Surface]] = {
            RIGHT : [
                r.subsurface(( 48, 0), s),
                r.subsurface((  0, 0), s),
                r.subsurface((144, 0), s),
                r.subsurface(( 96, 0), s)],
            LEFT  : [
                l.subsurface((  0, 0), s),
                l.subsurface(( 48, 0), s),
                l.subsurface(( 96, 0), s),
                l.subsurface((144, 0), s)],
            UP    : [
                u.subsurface((  0, 0), s),
                u.subsurface(( 48, 0), s),
                u.subsurface(( 96, 0), s),
                u.subsurface((144, 0), s)],
            DOWN  : [
                d.subsurface((  0, 0), s),
                d.subsurface(( 48, 0), s),
                d.subsurface(( 96, 0), s),
                d.subsurface((144, 0), s)]
        }

        # collision
        self.collision_rect = pygame.rect.Rect((0, 0), self.sprites[self.direction_str][self.frames].get_size())
        self.collision_rect.inflate_ip(0, - 8 * MAP_ZOOM)

        self.rect  = self.sprites[self.direction_str][self.frames].get_rect(topleft = pos)
        self.update_image()
        
        # stats
        self.speed = 3

        # movement
        self.collide_group = collide_group

        # inventory lists
        self.tubemon : list[Monster] = []
        self.active_tubemon_index = 0
        self.bag : dict[str, int] = {}
    
    def update(self) -> None:
        self.input()
        self.animate()

    def animate(self) -> None:

        if not self.moving: return

        if self.ANIMATIONS_FRAMES > 1:
            self.elapsed += 1

        if self.elapsed % self.elapsed_max == 0:
            if self.frames < self.ANIMATIONS_FRAMES - 1:
                self.frames += 1
            else:
                self.frames = 0

            self.update_image()
    
    def reset_frames(self) -> None:
        self.frames = 0
        self.elapsed = 0

    def reset_animation(self) -> None:
        # reset walking animation to idle
        self.reset_frames()
        self.update_image()

    def update_image(self) -> None:
        self.image = self.sprites[self.direction_str][self.frames]
        self.update_collision_rect()

    def collided(self, direction : pygame.math.Vector2) -> bool:
        # prevent player from passing into collided objects
        for boundary in self.collide_group.sprites():
            future_rect = pygame.Rect(self.collision_rect.topleft + direction, self.collision_rect.size)
            if future_rect.colliderect(boundary.rect):
                return True
        return False

    def input(self) -> None:

        self.moving = False

        # all keys
        keys = pygame.key.get_pressed()

        direction = pygame.math.Vector2(0, 0)

        # horizontal movement
        for key in CONTROLS[LEFT]: 
            if keys[key]:
                direction.x -= 1
                break

        for key in CONTROLS[RIGHT]: 
            if keys[key]: 
                direction.x += 1
                break
        
        # vertical movement 
        for key in CONTROLS[UP]: 
            if keys[key]: 
                direction.y -= 1
                break

        for key in CONTROLS[DOWN]: 
            if keys[key]: 
                direction.y += 1
                break           
        
        if direction.magnitude_squared() != 0:
            direction = direction.normalize() * self.speed
            if not self.collided(direction):
                self.rect.topleft += direction
                self.moving = True
            else:
                self.reset_frames()
        else:
            self.reset_frames()

        if   direction.y > 0: self.direction_str = DOWN
        elif direction.y < 0: self.direction_str = UP
        # prioritize looking horizontal than vertical while movinf both directions
        if   direction.x > 0: self.direction_str = RIGHT
        elif direction.x < 0: self.direction_str = LEFT
        self.update_image()

        if keys[pygame.K_SPACE]: 
            print(self.rect)

    def update_collision_rect(self) -> None:
        self.collision_rect.bottomleft = self.rect.bottomleft

    def draw_collision_box(self, display_surface : pygame.surface.Surface, offset : tuple[int, int] = tuple((0, 0))) -> None:
        #pygame.draw.rect(display_surface, 'blue', pygame.rect.Rect(self.rect.topleft - offset, self.rect.size))
        pygame.draw.rect(display_surface, pygame.color.Color(40, 234, 92, 50), pygame.rect.Rect(self.collision_rect.topleft - offset, self.collision_rect.size))

    def add_tubemon(self, *monsters : Monster) -> bool:
        """
        Args:
            monster (Monster): The monster to add to the tubemon list.

        Returns:
            bool: True if the monster is added to the tubemon list. False if not.
        """
        has_room : bool = self.carried_tubemon() + len(monsters) < Player.TUBEMON_CAPACITY
        if has_room:
            for monster in monsters:
                self.tubemon.append(monster)
        return has_room

    def remove_tubemon(self, monster : Monster) -> None:
        """
        Args:
            monster (Monster): Monster to remove from the tubemon list.
        """
        try:
            self.tubemon.remove(monster)
        except:
            pass

    def active_tubemon(self) -> Monster:
        return self.tubemon[self.active_tubemon_index]

    def swap_active_tubemon(self, index : int) -> None:
        active_monster = self.active_tubemon()
        self.tubemon[self.active_tubemon_index] = self.tubemon[index]
        self.tubemon[index] = active_monster

    def carried_tubemon(self) -> int:
        """
        Returns:
            int: The number of tubemon in the current tubemon list.
        """
        return len(self.tubemon)

    def copy_tubemon_list(self) -> list[Monster]:
        return self.tubemon.copy()

    def paste_tubemon_list(self, loadout : list[Monster]) -> None:
        for index, _ in enumerate(loadout):
            self.tubemon[index] = loadout[index]

    def non_fainted_tubemon(self) -> int:
        non_fainted = 0
        for monster in self.tubemon:
            if not monster.no_health():
                non_fainted += 1
        return non_fainted


    def add_items(self, item_name : str, quantity : int = 1) -> None:
        """Add the quantity of item_name to bag.

        Args:
            item_name (str): Item to add to bag.
            quantity (int): The number of items to add to the bag.
        """
        # The bag contains the item
        if item_name in self.bag:
            # Increament the item by the qauntity
            self.bag[item_name] += quantity
        else:
            # Set the the item with the quantity
            self.bag[item_name] = quantity

    def remove_items(self, item_name : str, quantity : int = 1) -> None:
        """Remove the quantity of item_name from bag.

        Args:
            item_name (str): Item to remove from the bag.
            quantity (int): The number of items to remove from the bag.
        """
        # Item is in bag
        if item_name in self.bag:
            # The quantity removed from the bag will remove all items from the bag
            if self.bag[item_name] - quantity <= 0:
                # Remove the item key from the bag
                self.bag.pop(item_name)
            else:
                # Remove the quantity of the item from the bag
                self.bag[item_name] -= quantity

    def has_item(self, item_name : str) -> bool:
        """Check if item_name is in the players bag.

        Args:
            item_name (str): The item to check for in the players bag.

        Returns:
            bool: True if the player has item_name.\n
             False if the player does not have item_name.
        """
        return item_name in self.bag

