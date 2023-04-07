from __future__ import annotations
from typing import Any
import pygame
from sprite import Sprite
import random
#from random import choice
from settings import FPS, MASTER_VOLUME
from math import pi, sin, degrees, atan2
import time
from rtgw_timer import Timer
from attacks import *
from sound import try_sound, try_play, try_stop

class Monster:

    class Animation:
        def __init__(self, duration : float, cycles : float, distance : float, next : tuple[float, float, float, tuple | None] | None = None) -> None:
            self.duration   : float = duration
            self.end        : float = pi * cycles / self.duration
            self.distance   : float = distance
            self.next       : tuple[float, float, float, tuple | None] | None = next
            self.start_time : float = None
            self.finished   : bool  = False
            self.elapsed_time : float = None
            self.last_lerp : float = 0

        def start(self) -> None:
            self.finished = False
            self.start_time = time.time()
            self.elapsed_time = min(time.time() - self.start_time, self.duration)

        def update(self) -> None:
            if self.finished: return 
            self.elapsed_time = time.time() - self.start_time
            self.elapsed_time = min(time.time() - self.start_time, self.duration)
            if self.elapsed_time >= self.duration:
                if self.next:
                    self.last_lerp += self.distance * sin(self.duration * self.end)
                    self.duration   = self.next[0]
                    self.end        = (0 + (pi * self.next[1] - 0)) / self.duration
                    self.distance   = self.next[2]
                    self.next       = self.next[3]
                    self.start_time = time.time()
                    self.elapsed_time = min(self.elapsed_time, self.duration)
                else:
                    self.finished = True

        def lerped(self) -> float:
            return self.last_lerp + self.distance * sin(self.elapsed_time * self.end)

    MONSTERS    : dict[int, tuple[str, pygame.surface.Surface]] = None 
    DRAGGLE     : int = 0
    EMBY        : int = 1
    COONTAIL    : int = 2
    TENTACLEAF  : int = 3
    FUZZBEAK    : int = 4
    GECKODANCE  : int = 5
    GROOVESTALK : int = 6
    HYDROGLOOP  : int = 7
    MURKWISKER  : int = 8
    MUSCLEMIGHT : int = 9

    @staticmethod
    def random() -> int:
        chance = random.choice(range(len(Monster.MONSTERS)))
        return chance

    @staticmethod
    def spawn_random(pos : tuple[int, int], attack_moves : int = None, is_player_monster : bool = False) -> Monster:
        if attack_moves:
            return Monster(pos, Monster.random(), random_attacks(attack_moves), is_player_monster)
        return Monster(pos, Monster.random(), random_attacks(), is_player_monster)


    @staticmethod
    def _INITIALIZE_SPRITES() -> None:
        size = (86, 89)
        num_sprites = (2, 4)
        Monster.MONSTERS = {
            #Monster.DRAGGLE : ['Draggle', Sprite.load_surfaces_alpha('Assets/Assets/Images/draggleSprite.png', size, num_sprites)],
            #Monster.EMBY    : ['Emby'   , Sprite.load_surfaces_alpha('Assets/Assets/Images/embySprite.png'   , size, (4, 1))],
            Monster.DRAGGLE     : ['Draggle'    , Sprite.load_monsters('Assets/Assets/Images/monsters/Draggle.png'    , num_sprites)],
            Monster.EMBY        : ['Emby'       , Sprite.load_monsters('Assets/Assets/Images/monsters/Emby.png'       , num_sprites)],
            Monster.COONTAIL    : ['Coontail'   , Sprite.load_monsters('Assets/Assets/Images/monsters/Coontail.png'   , num_sprites)],
            Monster.TENTACLEAF  : ['Tentacleaf' , Sprite.load_monsters('Assets/Assets/Images/monsters/Tentacleaf.png' , num_sprites)],
            Monster.FUZZBEAK    : ['Fuzzbeak'   , Sprite.load_monsters('Assets/Assets/Images/monsters/Fuzzbeak.png'   , num_sprites)],
            Monster.GECKODANCE  : ['Geckodance' , Sprite.load_monsters('Assets/Assets/Images/monsters/Geckodance.png' , num_sprites)],
            Monster.GROOVESTALK : ['Groovestalk', Sprite.load_monsters('Assets/Assets/Images/monsters/Groovestalk.png', num_sprites)],
            Monster.HYDROGLOOP  : ['Hydrogloop' , Sprite.load_monsters('Assets/Assets/Images/monsters/Hydrogloop.png' , num_sprites)],
            Monster.MURKWISKER  : ['Murkwisker' , Sprite.load_monsters('Assets/Assets/Images/monsters/Murkwisker.png' , num_sprites)],
            Monster.MUSCLEMIGHT : ['Musclemight', Sprite.load_monsters('Assets/Assets/Images/monsters/Musclemight.png', num_sprites)],
        }

    def __init__(self, position : tuple[int, int], monster_no : int, attacks : list[dict[str, Any]], is_player_monster : bool = False) -> None:
        self.position = position
        self.monster_no = monster_no

        # animations
        self.is_player_monster = is_player_monster
        self.frames : int = 0
        self.elapsed : int = 0
        self.elapsed_max : int = FPS // 2 # dependent on the FPS, 30
        # attack
        self.attack_visual : list[pygame.surface.Surface] = None
        self.attack_visual_path : tuple[Monster.Animation, Monster.Animation] = None

        # animation steps
        self.animations : Monster.Animation = None
        # 
        self.attacking = False
        # stats
        self.attacks = attacks
        self.max_health = 40
        self.health = self.max_health
        # vulnerable
        self.alpha : int = 255
        self.hit : bool = False
        self.hit_timer : Timer = None
        self.hit_duration : float = 0.5
        # audio
        self.tackle_audio = try_sound('Assets\Assets\Audio\\tackleHit.wav')

    def update(self) -> None:
        self.animate()
        # both of these animate funcitons should update
        self.attacking = self.animate_steps()
        self.attacking = self.animate_visual_steps() or self.attacking
        self.flicker()

    def draw(self, display_surface : pygame.surface.Surface) -> None:

        if self.no_health(): return


        image = self.back_sprites()[self.frames] if self.is_player_monster else self.front_sprites()[self.frames]
        pygame.Surface.set_alpha(image, self.alpha)
        x_offset = self.animations.lerped() if self.animations else 0
        display_surface.blit(image, (self.position[0] + x_offset, self.position[1]))
        
        if self.attack_visual:
            r = pygame.Rect(self.position, self.sprites_size()) # start rendering from the mid right of the monster
            so = pygame.Vector2(self.attack_visual[0].get_size()) // 2
            #o  = pygame.Vector2(r.midright) - so # offset
            o  = pygame.Vector2(r.center) - so # offset
            p = (o.x + self.attack_visual_path[0].lerped(),
                 o.y + self.attack_visual_path[1].lerped())
            display_surface.blit(self.attack_visual[0], p)
    
    def animate(self) -> None:
        
        animation_frames = len(self.front_sprites())
        if animation_frames > 1:
            self.elapsed += 1

        if self.elapsed % self.elapsed_max == 0:
            if self.frames < animation_frames - 1:
                self.frames += 1
            else:
                self.frames = 0

    def name(self) -> str:
        return Monster.MONSTERS[self.monster_no][0]
    
    def sprites_size(self) -> tuple[int, int]:
        return self.front_sprites()[0].get_size()

    def sprites(self) -> list[list[pygame.Surface]]:
        return Monster.MONSTERS[self.monster_no][1]
    
    def front_sprites(self) -> list[pygame.Surface]:
        return self.sprites()[0]
    
    def back_sprites(self) -> list[pygame.Surface]:
        return self.sprites()[1]

    def animate_steps(self) -> bool:
        
        if not self.animations: return False

        self.animations.update()
        
        if self.animations.finished:
            self.animations = None
            return False
        return True

    def animate_visual_steps(self) -> bool:
        
        if not self.attack_visual: return False

        self.attack_visual_path[0].update()
        self.attack_visual_path[1].update()
        
        if self.attack_visual_path[0].finished and self.attack_visual_path[1].finished:
            self.attack_visual_path = None
            self.attack_visual = None
            return False
        return True

    def attack(self, attack : dict[str, Any], target : Monster, reverse_animation : bool = False) -> None:
        if self.attacking or target.no_health(): return
        self.attacking = True
        #print(f'{self.name()} used {attack["name"]} on {target.name()}')
        rm : int = -1 if reverse_animation else 1 # reverse multiplier
        if   attack == TACKLE   :
            self.animations = Monster.Animation(0.5, rm * -0.5, 20, (0.125, rm * 0.90, 60, None))
            self.animations.start()

        elif attack == FIREBALL : 
            #self.animations = Monster.Animation(0.5, rm * -0.5, 20, (0.125, rm * 0.90, 60, None))
            self.attack_visual : list[pygame.surface.Surface] = Sprite.load_surfaces_alpha('Assets\\Assets\\Images\\fireball.png',(258 // 4, 64), (4, 1))
            fireball_audio = try_sound('Assets\Assets\Audio\\fireballHit.wav')
            try_play(fireball_audio)
            # center the attack_visual sprite at this monsters center / mid right
            r = pygame.Rect(self.position, self.front_sprites()[0].get_size()) # start from the mid right of the monster, rect
            so = pygame.Vector2(self.attack_visual[0].get_size()) // 2 # sprite offset
            #o  = pygame.Vector2(r.midright) - so # offset
            o  = pygame.Vector2(r.center) - so # offset

            # get the end position at the targets center with the attack_visual sprite centered on it
            tr = pygame.Rect(target.position, target.front_sprites()[0].get_size()) # target rect
            d = pygame.Vector2(tr.center) - so - o # difference

            # rotate the sprite toward the target
            angle : float = degrees(atan2(d.y, d.x))
            for i, sprite in enumerate(self.attack_visual):
                self.attack_visual[i] = pygame.transform.rotate(sprite, angle)

            d *= rm
            self.attack_visual_path = (Monster.Animation(0.5, rm * 0.5, d.x), Monster.Animation(0.5, rm * 0.5, d.y))
            self.attack_visual_path[0].start()
            self.attack_visual_path[1].start()  

        target.hurt(attack["damage"])

    def hurt(self, damage: int) -> None:
        try_play(self.tackle_audio)
        self.health = max(self.health - damage, 0)
        self.hit = True
        self.hit_timer = Timer(self.hit_duration)
        #print(f'{self.name()} health at: {self.health}')

    def flicker(self) -> None:

        if self.hit_timer and self.hit_timer.complete():
            self.hit_timer = None
            self.hit = False
            try_stop(self.tackle_audio)

        if not self.hit:
            self.alpha = 255
        else:
            alpha = sin(pygame.time.get_ticks())
            self.alpha = (255 if alpha >= 0 else 0)

    def no_health(self) -> bool:
        return self.health <= 0

    def health_percent(self) -> float:
        return self.health / self.max_health

    def kill(self) -> None:
        self.health = 0







