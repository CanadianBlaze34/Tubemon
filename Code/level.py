import pygame
from network import *
from settings import *
from player import Player
from dummyplayer import DummyPlayer
from sprite import Sprite
from camera import Camera
from typing import Any
import threading
import _thread
from boundary import Boundary
from battlezones import BattleZone
import random
from Animations.flashanimation import FlashAnimation
from monster import Monster
from GUI.label import Label
from GUI.button import Button
from GUI.slider import Slider
from GUI.buttonsingleton import ButtonSingleton
import pygame.rect as rect
from pygame.rect import Rect
from rtgw_timer import Timer
from attacks import *
from pygame.surface import Surface
from math import sin, cos
from sound import try_sound, try_play, try_stop, try_update_all
from ITEMS.item import Item
from ITEMS.potion import Potion
from ITEMS.tubebox import Tubebox
import os
import sys
#import multiprocessing as mp

class Level:

    PLAYER_TURN  : int = 0
    PLAYER2_TURN : int = 1
    ENEMY_TURN   : int = 2
    ENEMY2_TURN  : int = 3

    EMPTY        : str = 'Empty'


    def __init__(self, client : Network, buttons : ButtonSingleton) -> None:
        
        # GENERAL --------------------------------------------------------------------
        
        self.buttons = buttons

        self.font_path : str = 'Assets\\Assets\\fonts\\Press_Start_2P\\PressStart2P-Regular.ttf'
        Monster._INITIALIZE_SPRITES()
        Item.ITEM : dict[str, Item] = {
            Item.POTION : Potion(),
            Item.TUBEBOX : Tubebox(),
        }

        # state
        #self.game_state = GAME_STATE
        #self.game_state = BATTLE_STATE 
        #self.game_state = PAUSE_STATE 
        self.game_state = MENU_STATE 

        self.display_surface : pygame.surface.Surface = pygame.display.get_surface()
        
        # Group
        self.battle_zone_group = pygame.sprite.Group()
        self.visible_sprites = pygame.sprite.Group()
        self.collide_sprites = pygame.sprite.Group()
        
        # Save
        self.save_file_path : str = ''

        # GAME STATE --------------------------------------------------------------------
        
        # backgrounds
        if MAP_ZOOM == 4:
            #self.background      = Sprite.load_image((0, 0), 'Assets/Assets/Tiled/Pellet Town 400%.png')
            #self.foreground_objects = Sprite.load_image_alpha((0, 0),'Assets\Assets\Tiled\ForegroundObjects400%.png')
            self.background      = Sprite.load_image_scaled('Assets/Assets/Tiled/Pellet Town.png', scale = MAP_ZOOM)
            self.foreground_objects = Sprite.load_image_scaled('Assets\Assets\Tiled\ForegroundObjects.png', scale = MAP_ZOOM, alpha = True)
        else:
            print(f'MAP_ZOOM in settings is {MAP_ZOOM} and not the default 4.')
            self.background      = Sprite.load_image((0, 0), 'Assets/Assets/Tiled/Pellet Town.png')
        
        # player
        self.player : Player = None #= Player((1226, 880), self.visible_sprites, self.collide_sprites)
        # player monsters
        #player_monster : Monster = Monster((280, 325), Monster.EMBY, [TACKLE, FIREBALL, WATERGUN, PEDALBLADE], True)
        #PLAYER_MONSTERS = 2
        #player_monsters : list[Monster] = []
        #for _ in range(PLAYER_MONSTERS):
        #    player_monsters.append(Monster.spawn_random((280, 325), is_player_monster = True))
        #self.player.add_tubemon(*player_monsters)

        # camera
        self.camera = Camera()

        # Collisions
        self.collisions : list[Boundary] = Boundary.spawn_collisions(self.collide_sprites)

        # battle zones
        self.battle_zones : list[BattleZone] = BattleZone.spawn_battle_zones(self.battle_zone_group)
        
        # audio
        self.ambiance_music = try_sound('Assets\Assets\Audio\map.wav')

        if self.game_state == GAME_STATE or self.game_state == MENU_STATE or self.game_state == PAUSE_STATE:
            try_play(self.ambiance_music, -1)
        
        self.save_variables_init()

        # PAUSE STATE ----------------------------------------------------------------------

        #self.pause_gui_init()
        
        # MENU STATE -----------------------------------------------------------------------

        def create_menu_background(self):
            menu_background_scale             : float   = 2.0
            # self.menu_background_y is used for floating accuracy and smooth as possible scrolling
            # pygame.Rects use integers which causes incremental rounding issues when adding small floats
            self.menu_background_y            : float   = 0.0 
            menu_background_scaled_image      : Surface = Sprite.load_image_scaled('Assets/Assets/Tiled/Pellet Town.png', scale = menu_background_scale).image
            menu_background_centered_position : tuple   = ((WIDTH - menu_background_scaled_image.get_width()) / 2, (HEIGHT - menu_background_scaled_image.get_height()) / 2)
            self.menu_background              : Sprite  = Sprite(menu_background_centered_position, menu_background_scaled_image)
        create_menu_background(self)
        if self.game_state == MENU_STATE:
            self.menu_gui_init()
        
        # BATTLE STATE --------------------------------------------------------------------
        
        # background
        self.battle_background = Sprite.load_image((0, 0), 'Assets/Assets/Images/battleBackground.png')
        self.battle_background.smooth_scale(self.display_surface.get_rect().size)
        
        # animation
        self.flash_animation = FlashAnimation(1.5, 4.0, pygame.color.Color('black'))
        
        # Monsters
        self.enemy_monster : Monster = None
        #self.enemy_monster : Monster = Monster((800, 100), Monster.DRAGGLE, [TACKLE, WATERGUN, POUND, SCRATCH])
        #self.player_monster : Monster = Monster((280, 325), Monster.EMBY, [TACKLE, FIREBALL, WATERGUN, PEDALBLADE], True)
        self.turn : int = Level.PLAYER_TURN
        self.timer_seconds = 1.3
        self.turn_timer : Timer = None
        self.battle_finished_timer : Timer = None


        # audio
        self.init_battle_audio = try_sound('Assets\Assets\Audio\initBattle.wav')
        self.battle_audio = try_sound('Assets\Assets\Audio\\battle.mp3')
        self.battle_victory_audio = try_sound('Assets\Assets\Audio\\victory.wav')

        if self.game_state == BATTLE_STATE:
            self.create_battle_gui()
            try_play(self.battle_audio, -1)

        # NETWORKING --------------------------------------------------------------------------
        if ONLINE:
            self.client          : Network                = client
            self.online_players  : dict[int, DummyPlayer] = {}
            self.thread_stop     : bool                   = False
            self.mutex           : threading.Lock         = threading.Lock()
            self.thread          : threading.Thread       = threading.Thread(target=self.thread_network, name='client-network', daemon=True)
            self.thread.start()

    def clean_up(self) -> None:
        if ONLINE:
            with self.mutex:
                self.thread_stop = True
            self.thread.join()
        
    def run(self, delta_time : float, events : list[pygame.event.Event]) -> None:
        if self.game_state == GAME_STATE:
            self.game_update(delta_time, events)
            self.game_draw()
        elif self.game_state == BATTLE_TRANSITION:
            if not self.flash_animation.finished:
                self.game_draw()
                self.flash_animation.update()
                self.flash_animation.draw(self.display_surface)
            else:
                self.game_state = BATTLE_STATE
                self.create_battle_gui()
                self.battle_update(delta_time, events)
                self.battle_draw()
                try_stop(self.init_battle_audio)
                try_play(self.battle_audio, -1)
        elif self.game_state == BATTLE_STATE:
            self.battle_update(delta_time, events)
            self.battle_draw()
        elif self.game_state == MENU_STATE:
            self.menu_update(delta_time)
            self.menu_draw()
        elif self.game_state == PAUSE_STATE:
            self.pause_update(delta_time, events)
            self.pause_draw()
        self.buttons.draw(self.display_surface)

    # NEW SAVE --------------------------------

    def save_variables_init(self) -> None:
        self._PLAYER_POSITION_X_BYTES         : int = 4
        self._PLAYER_POSITION_Y_BYTES         : int = 4
        self._PLAYER_DIRECTION_BYTES          : int = 1
        self._PLAYER_CARRIED_TUBEMON_BYTES    : int = 1
        self._PLAYER_TUBEMON_NUMBER_BYTES     : int = 1
        self._PLAYER_TUBEMON_HEALTH_BYTES     : int = 2
        self._PLAYER_TUBEMON_ATTACK_BYTES     : int = 1
        self._PLAYER_ITEMS_IN_BAG_BYTES       : int = 1
        self._PLAYER_BAG_ITEM_BYTES           : int = 1
        self._PLAYER_BAG_ITEM_QUANTITY_BYTES  : int = 4

        self._PRINT_SAVE_MESSAGES             : bool = False

    def new_save(self) -> None:
        # player
        self.player = Player((1226, 880), self.visible_sprites, self.collide_sprites)
        # player monsters
        #player_monster : Monster = Monster((280, 325), Monster.EMBY, [TACKLE, FIREBALL, WATERGUN, PEDALBLADE], True)
        PLAYER_MONSTERS = 1
        player_monsters : list[Monster] = []
        for _ in range(PLAYER_MONSTERS):
            player_monsters.append(Monster.spawn_random((280, 325), is_player_monster = True))
        self.player.add_tubemon(*player_monsters)

        self.player.add_items(Item.POTION, 6)
        self.player.add_items(Item.TUBEBOX, 5)

        self.save_player()

    def load_save(self) -> None:
        # player
        self.player = Player((0, 0), self.visible_sprites, self.collide_sprites)
        self.load_player()

    def save_player(self) -> None:
        with open(self.save_file_path, 'wb+') as save_file:
            # Start of file
            save_file.seek(0)

            # Save the players position
            #player_position : tuple[int, int] = self.player.rect.topleft
            #player_position : tuple[str, str] = str(player_position[0]), str(player_position[1])
            #player_position : tuple[bytes, bytes] = player_position[0].encode(), player_position[1].encode()
            save_file.write(self.player.rect.x.to_bytes(self._PLAYER_POSITION_X_BYTES, signed = True))
            save_file.write(self.player.rect.y.to_bytes(self._PLAYER_POSITION_Y_BYTES, signed = True))
            
            # Save the players direction
            save_file.write(direction_to_int(self.player.direction_str).to_bytes(self._PLAYER_DIRECTION_BYTES))

            # save the number of tubemon first
            save_file.write(self.player.carried_tubemon().to_bytes(self._PLAYER_CARRIED_TUBEMON_BYTES))
            if self._PRINT_SAVE_MESSAGES:
                s : str = 's' if self.player.carried_tubemon() != 1 else ''
                save_message : str = f'Saving player at ({self.player.rect.x}, {self.player.rect.y}) looking towards {self.player.direction_str} carrying {self.player.carried_tubemon()} monster{s}.\n'

            # Save the players Tubemon number, health and moves
            for tubemon in self.player.tubemon:
                # monster number
                save_file.write(tubemon.monster_no.to_bytes(self._PLAYER_TUBEMON_NUMBER_BYTES))
                # monster health
                save_file.write(tubemon.health.to_bytes(self._PLAYER_TUBEMON_HEALTH_BYTES))
                # monster attack moves
                attack_len = len(tubemon.attacks)
                move_1 = attack_to_int(tubemon.attacks[0]['name'])
                move_2 = attack_to_int(tubemon.attacks[1]['name']) if attack_len > 1 else -1
                move_3 = attack_to_int(tubemon.attacks[2]['name']) if attack_len > 2 else -1
                move_4 = attack_to_int(tubemon.attacks[3]['name']) if attack_len > 3 else -1
                save_file.write(move_1.to_bytes(self._PLAYER_TUBEMON_ATTACK_BYTES))
                save_file.write(move_2.to_bytes(self._PLAYER_TUBEMON_ATTACK_BYTES, signed = True))
                save_file.write(move_3.to_bytes(self._PLAYER_TUBEMON_ATTACK_BYTES, signed = True))
                save_file.write(move_4.to_bytes(self._PLAYER_TUBEMON_ATTACK_BYTES, signed = True))
                if self._PRINT_SAVE_MESSAGES:
                    save_message += f'Saving monster # {tubemon.monster_no} ({tubemon.health} health), with the moves {move_1}, {move_2}, {move_3} and {move_4}.\n'

            # Save the players Items
            items_in_bag = len(self.player.bag)
            save_file.write(items_in_bag.to_bytes(self._PLAYER_ITEMS_IN_BAG_BYTES))
            if self._PRINT_SAVE_MESSAGES:
                s : str = 's' if items_in_bag != 1 else ''
                save_message += f'Saving players {items_in_bag} item{s}.\n'
            for item_name, quantity in self.player.bag.items():
                save_file.write(Item.to_id(item_name).to_bytes(self._PLAYER_BAG_ITEM_BYTES))
                save_file.write(quantity.to_bytes(self._PLAYER_BAG_ITEM_QUANTITY_BYTES))
                if self._PRINT_SAVE_MESSAGES:
                    save_message += f'Saving players {quantity} {item_name}.\n'

            if self._PRINT_SAVE_MESSAGES:
                # remove the trailing '\n'
                save_message = save_message[:-1]
                print(save_message)

    def load_player(self) -> None:
        #print(f'Loading Player information from {self.save_file_path}.')
        with open(self.save_file_path, 'rb') as save_file:
            # Start of file
            save_file.seek(0)
            
            # load the players position
            self.player.rect.x = int.from_bytes(save_file.read(self._PLAYER_POSITION_X_BYTES), signed = True)
            self.player.rect.y = int.from_bytes(save_file.read(self._PLAYER_POSITION_Y_BYTES), signed = True)
            
            # load the players direction
            self.player.direction_str = int_to_direction(int.from_bytes(save_file.read(self._PLAYER_DIRECTION_BYTES)))

            # save the number of tubemon first
            carried_tubemon : int = int.from_bytes(save_file.read(self._PLAYER_CARRIED_TUBEMON_BYTES))
            if self._PRINT_SAVE_MESSAGES:
                s : str = 's' if carried_tubemon != 1 else ''
                load_message : str = f'Loading player at ({self.player.rect.x}, {self.player.rect.y}) looking towards {self.player.direction_str} carrying {carried_tubemon} monster{s}.\n'

            # Save the players Tubemon number, health and moves
            player_monsters : list[Monster] = []
            for _ in range(carried_tubemon):

                # tubemon
                monster_number = int.from_bytes(save_file.read(self._PLAYER_TUBEMON_NUMBER_BYTES))
                # health
                monster_health = int.from_bytes(save_file.read(self._PLAYER_TUBEMON_HEALTH_BYTES))

                move_1_int = int.from_bytes(save_file.read(self._PLAYER_TUBEMON_ATTACK_BYTES))
                move_2_int = int.from_bytes(save_file.read(self._PLAYER_TUBEMON_ATTACK_BYTES), signed = True)
                move_3_int = int.from_bytes(save_file.read(self._PLAYER_TUBEMON_ATTACK_BYTES), signed = True)
                move_4_int = int.from_bytes(save_file.read(self._PLAYER_TUBEMON_ATTACK_BYTES), signed = True)
                if self._PRINT_SAVE_MESSAGES:
                    load_message += f'Loading monster # {monster_number} ({monster_health} health), with the moves {move_1_int}, {move_2_int}, {move_3_int} and {move_4_int}.\n'
                # attack moves
                move_1 = int_to_attack(move_1_int)
                move_2 = int_to_attack(move_2_int) if move_2_int != -1 else None
                move_3 = int_to_attack(move_3_int) if move_3_int != -1 else None
                move_4 = int_to_attack(move_4_int) if move_4_int != -1 else None
                attacks : list = [move_1]
                # there will only be 4 moves if there are 3 moves and 3 moves if there are 2 moves
                # if move_2 is None then move_3 and move_4 will be None
                if move_2: 
                    attacks.append(move_2)
                    if move_3: 
                        attacks.append(move_3)
                        if move_4:
                            attacks.append(move_4)

                # make the tubemon
                monster = Monster((280, 325), monster_number, attacks, True)
                monster.health = monster_health
                player_monsters.append(monster)

            # load the players items
            items_in_bag = int.from_bytes(save_file.read(self._PLAYER_ITEMS_IN_BAG_BYTES))
            if self._PRINT_SAVE_MESSAGES:
                s : str = 's' if items_in_bag != 1 else ''
                load_message += f'Loading players {items_in_bag} item{s}.\n'
            for _ in range(items_in_bag):

                self.player.add_items(Item.POTION, 2)
                item_name = Item.to_name(int.from_bytes(save_file.read(self._PLAYER_BAG_ITEM_BYTES)))
                quantity = int.from_bytes(save_file.read(self._PLAYER_BAG_ITEM_QUANTITY_BYTES))
                self.player.add_items(item_name, quantity)
                if self._PRINT_SAVE_MESSAGES:
                    load_message += f'Loading players {quantity} {item_name}.\n'

            self.player.add_tubemon(*player_monsters)
            if self._PRINT_SAVE_MESSAGES:
                # remove the trailing '\n'
                load_message = load_message[:-1]
                print(load_message)

    # GAME ---------------------------

    def game_update(self, delta_time : float, events : list[pygame.event.Event]) -> None:
        
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = PAUSE_STATE
                self.pause_gui_init()

        if ONLINE:
            with self.mutex:
                self.visible_sprites.update()
                self.camera.update(self.player.rect)
                self.battle_detect()
        else:
            self.visible_sprites.update()
            self.camera.update(self.player.rect)
            self.battle_detect()

    def game_draw(self) -> None:
        self.camera.draw([self.background])
        #BattleZone.draw(self.battle_zones, self.display_surface, self.camera.offset)
        if ONLINE:
            with self.mutex:
                self.camera.draw(self.visible_sprites.sprites())
                for i in self.visible_sprites.sprites():
                    print(f'{i}')
        else:
            self.camera.draw(self.visible_sprites.sprites())
            #self.player.draw_collision_box(self.display_surface, self.camera.offset)
        #Boundary.draw(self.collisions, self.display_surface, self.camera.offset)
        self.camera.draw([self.foreground_objects])
    
    # BATTLE ------------------------

    def create_battle_gui(self) -> None:
        # first in list will be drawn first and
        # rendered under any labels/buttons after in the list
        r         = pygame.Rect(0, 0, WIDTH, 140) # rect
        g         = [] # group
        # attack button attributes
        ab_border = None #('black', 1)
        self.abtscs    = 13, 'black', self.font_path # text size, color, src
        self.battle_colors = ('#ddddddff', '#b1b1b1ff', 'dark gray')
        ab_size   = ((2 * r.w / 3) // 3, r.h // 2)
        
        self.reset_battle_variables()
        self.active_tubemon_index = self.player.active_tubemon_index
        self.tubemon_list = self.player.copy_tubemon_list()
        # bag
        self.bag_open = False
        self.item_labels          : list[list[str]] = []
        self.bag_background_label : str = 'Bag Background'
        # general battle GUI
        bag_label            : str = 'Bag'
        run_label            : str = 'Run'
        attack_move_1_label  : str = 'Attack Move 1'
        attack_move_2_label  : str = 'Attack Move 2'
        attack_move_3_label  : str = 'Attack Move 3'
        attack_move_4_label  : str = 'Attack Move 4'
        attack_type_label    : str = 'Attak Type'
        dialog_box_label     : str = 'dialog box' # dialog_box
        top_border_label         : str = 'top border' # top_border
        seperator_border_label   : str = 'seperator border' # seperator_border
        seperator_border_2_label : str = 'seperator border 2' # seperator_border 2 
        enemy_monster_interface_label         : str = 'enemy monster interface' # enemy_monster_interface
        enemy_monster_health_background_label : str = 'enemy monster health background' # enemy_monster_health_background
        enemy_monster_health_label            : str = 'enemy monster health' # enemy_monster_health
        player_monster_interface_label         : str = 'player monster interface' # player_monster_interface
        player_monster_health_background_label : str = 'player monster health background' # player_monster_health_background
        player_monster_health_label            : str = 'player monster health' # player_monster_health
        tubemon_switch_label : str = 'Tubemon Switch'

        def bag_task(buttons : ButtonSingleton):
            bag_background = None
            self.bag_open = not self.bag_open

            def create_bag_gui() -> None:
                """Initialize the battle bags graphical interface."""
                nonlocal bag_background

                background_color = 'white'
                border_color = 'black'
                text_color = 'black'

                # action bools
                self.battle_bag_used_item = None

                bag_background = Label([], Rect((0, 0), (350, 0)), background_color, ("Bag", 25, text_color, self.font_path, (0, 12), (True, False)), (border_color, 4))

                # positions
                margins = 20
                bag_background.rect.topleft = (margins, margins)
                # ??
                bag_background.rect.__setattr__('height', HEIGHT - self.attack_type.rect.height - margins * 2)  
                #bag_background.rect.height = HEIGHT - self.battle_gui[self.at].rect.height - margins * 2
                
                self.buttons.create(self.bag_background_label, bag_background, None, 0)

            # opened bag
            if self.bag_open:

                create_bag_gui()
                # item offsets
                margin = 10
                width = bag_background.rect.width - margin * 2
                height = 40
                x = bag_background.rect.left + margin
                position_under_bag_text = bag_background.rect.top + 45

                # initialize buttons into the battle_bag_gui
                # append all the items the player has
                for index, (name, quantity) in enumerate(self.player.bag.items()):
                    
                    bag_item_gui = []

                    # text label
                    name_label = Label([], Rect(x, 0, width - 50 * 2 - margin * 3, height), None, (f'{name}', 15, 'black', self.font_path, (10, 0), (False, True)), None, True)
                    name_label.rect.top = position_under_bag_text + (height + margin) * index
                    name_id : str = f'{name}'
                    bag_item_gui.append(name_id)
                    self.buttons.create(name_id, name_label, None, 1)
                    
                    # quantity label
                    quantity_label = Label([], Rect(0, 0, 50, height), None, (f'{quantity}', 15, 'black', self.font_path, (0, 0), (True, True)), None, True)
                    quantity_label.rect.top = name_label.rect.top
                    quantity_label.rect.left = name_label.rect.right + margin
                    quantity_id : str = f'{name} {quantity}'
                    bag_item_gui.append(quantity_id)
                    self.buttons.create(quantity_id, quantity_label, None, 1)
                    
                    # Use button
                    if   name == Item.POTION  : 
                        target = self.player.active_tubemon()
                        def custom_func():
                            self.refresh_monster_health()
                            health_to_add = min(Item.ITEM[Item.POTION].heal,  target.max_health - target.health)
                            self.enable_battle_dialog(f'Player\'s {target.name()} healed {health_to_add} health.')
                            self.battle_bag_used_item = Item.POTION

                    elif name == Item.TUBEBOX :
                        target = self.enemy_monster
                        def custom_func(t = target):
                            self.enable_battle_dialog(f'Player used a Tubebox.\nPlayer caught a wild {t.name()}.')
                            #self.enemy_monster.kill()
                            #self.refresh_monster_health()
                            self.battle_bag_used_item = Item.TUBEBOX

                    def use_task(buttons : ButtonSingleton, ql = quantity_label, n = name, t = target, cf = custom_func): # function decorator with closures
                        # do the items specified action
                        Item.ITEM[n].activate(player = self.player, target = t)
                        # update the quantity in the gui
                        if self.player.has_item(n):
                            ql.message(f'{self.player.bag[n]}')
                        # call the additional function
                        cf()
                        # close the bag and start the dialog
                        self.turn_timer = Timer(self.timer_seconds)
                        self.close_bag_gui()
                        bag_open = False

                    use_id : str = f'Use {name}'
                    bag_item_gui.append(use_id)
                    # make the use button
                    use = Button([], Rect(0, 0, 50, height), self.battle_colors, ('Use', 15, 'black', self.font_path, (0, 0), (True, True)))
                    # set the use button position
                    use.rect.top = name_label.rect.top
                    use.rect.left = quantity_label.rect.right + margin
                    self.buttons.create(use_id, use, [use_task], 1)

                    # append for deletion when closing bag
                    self.item_labels.append(bag_item_gui)
            
            else:
                self.close_bag_gui()

        def run_task(buttons : ButtonSingleton):
            if self.bag_open:
                self.close_bag_gui()
            self.enable_battle_dialog(f'Player has ran away.')
            self.turn_timer = Timer(self.timer_seconds)
            self.battle_run_away = True

        def spawn_gui() -> None:

            # The attack_type and tubemon_switch size
            attack_switch_size = (r.w / 3) // 2, r.h

            self.attack_move_1                    = Button(g, rect.Rect(r.topleft,         ab_size), self.battle_colors, (Level.EMPTY, self.abtscs[0], self.abtscs[1], self.abtscs[2]),     ab_border)
            self.attack_move_2                    = Button(g, rect.Rect(r.topleft,         ab_size), self.battle_colors, (Level.EMPTY, self.abtscs[0], self.abtscs[1], self.abtscs[2]),     ab_border, False)
            self.attack_move_3                    = Button(g, rect.Rect(r.topleft,         ab_size), self.battle_colors, (Level.EMPTY, self.abtscs[0], self.abtscs[1], self.abtscs[2]),     ab_border, False)
            self.attack_move_4                    = Button(g, rect.Rect(r.topleft,         ab_size), self.battle_colors, (Level.EMPTY, self.abtscs[0], self.abtscs[1], self.abtscs[2]),     ab_border, False)
            self.attack_type                      = Label(g, rect.Rect(r.topleft, attack_switch_size),   'white', ('TYPE',       16,  'black',   self.abtscs[2]), border = None)
            self.dialog_box                       = Label(g, r, 'white', text = ('Dialog.', 16, 'black', self.abtscs[2], (12, 12)), border = None, visible = False)
            top_border                            = Label(g, rect.Rect(r.topleft,        (r.w, 4)),   'black') # border on top of the guis
            self.seperator_border                 = Label(g, rect.Rect(r.topleft,        (4, r.h)),   'black') # border seperating attack type from run and bag button
            self.seperator_border_2               = Label(g, rect.Rect(r.topleft,        (4, r.h)),   'black') # border seperating attack moves from run and bag button
            self.enemy_monster_interface          = Label(g, rect.Rect(     50,                50,     250, 12 + 16 + 10 + 5 + 12 + 4), 'white', text = ('Name', 16, 'black', self.abtscs[2], (12, 12)), border = ('black', 4))
            self.enemy_monster_health_background  = Label(g, rect.Rect(50 + 12, 50 + 12 + 16 + 10, 250 - 24,                        5), '#ccccccff', text = None, border = None)
            self.enemy_monster_health             = Label(g, rect.Rect(50 + 12, 50 + 12 + 16 + 10, 250 - 24,                        5), 'dark green', text = None, border = None)
            self.player_monster_interface         = Label(g, rect.Rect(0, 330,      250, 12 + 16 + 10 + 5 + 12 + 4), 'white', text = ('Name', 16, 'black', self.abtscs[2], (12, 12)), border = ('black', 4))
            self.player_monster_health_background = Label(g, rect.Rect(0,   0, 250 - 24,                         5), '#ccccccff', text = None, border = None)
            self.player_monster_health            = Label(g, rect.Rect(0,   0, 250 - 24,                         5), 'dark green', text = None, border = None)
            self.bag = Button([], Rect((0, 0), ab_size), self.battle_colors, ('Bag', self.abtscs[0], self.abtscs[1], self.abtscs[2]))
            self.run_button = Button([], Rect((0, 0), ab_size), self.battle_colors, ('Run', self.abtscs[0], self.abtscs[1], self.abtscs[2]))
            self.tubemon_switch = Button(g, Rect((0, 0), (attack_switch_size)), self.battle_colors, ('Tubemon', self.abtscs[0], self.abtscs[1], self.abtscs[2]))

            # repositioning
            #self.battle_gui[0].rect.bottomleft = (0, HEIGHT)
            self.attack_move_1.rect.topleft = (0, HEIGHT - r.h)
            self.attack_move_2.rect.topleft = self.attack_move_1.rect.topright
            self.attack_move_3.rect.topleft = self.attack_move_1.rect.bottomleft
            self.attack_move_4.rect.topleft = self.attack_move_3.rect.topright
            self.attack_type.rect.bottomright = (WIDTH, HEIGHT)
            self.set_attack_moves(self.player.active_tubemon())
            # borders
            top_border.rect.topleft = self.attack_move_1.rect.topleft
            self.seperator_border.rect.topright = self.attack_type.rect.topleft
            self.seperator_border_2.rect.topleft = self.attack_move_2.rect.topright
            # enemy monster interface
            self.enemy_monster_health.rect.w = int(self.enemy_monster_health_background.rect.w * self.enemy_monster.health_percent())
            # player monster interface
            self.player_monster_interface.rect.right = WIDTH - 50
            self.player_monster_health_background.rect.topleft = (self.player_monster_interface.rect.left + 12, self.player_monster_interface.rect.top + 12 + 16 + 10)
            self.player_monster_health.rect.topleft = self.player_monster_health_background.rect.topleft
            self.player_monster_health.rect.w = int(self.player_monster_health_background.rect.w * self.player.active_tubemon().health_percent())
            self.refresh_monster_Names()
            self.refresh_monster_health()
            # dialog box
            self.dialog_box.rect.topleft = self.attack_move_1.rect.topleft

            self.bag.rect.topleft = self.attack_move_2.rect.topright
            self.run_button.rect.topleft = self.attack_move_4.rect.topright
            self.tubemon_switch.rect.bottomleft = self.run_button.rect.bottomright

            self.battle_labels = [self.attack_move_1, self.attack_move_2, self.attack_move_3, self.attack_move_4, self.attack_type, self.seperator_border, self.seperator_border_2, self.bag, self.run_button, self.tubemon_switch]

            def create_Buttons() -> None:
                
                # Create tasks for attack move buttons
                attack_move_tasks = []
                attack_move_entered_tasks = []
                for i in range(4):
                    def attack_move_task(buttons : ButtonSingleton, index = i) -> None:
                        attack = self.player.active_tubemon().attacks[index]
                        self.player.active_tubemon().attack(attack, self.enemy_monster)
                        self.enable_battle_dialog(f'{self.player.active_tubemon().name()} used {attack["name"]} on {self.enemy_monster.name()}.')
                        self.refresh_monster_health()
                        if self.bag_open:
                            self.close_bag_gui()
                        self.turn_timer = Timer(self.timer_seconds)
                    attack_move_tasks.append(attack_move_task)

                    def attack_move_entered_task(button: ButtonSingleton, index = i) -> None:
                        attack = self.player.active_tubemon().attacks[index]
                        # update the attack type label text
                        self.attack_type.update_message(msg = attack['type'], color = FONT_COLOR[attack['type']])
                        return 1
                    attack_move_entered_tasks.append(attack_move_entered_task)

                self.buttons.create(attack_move_1_label, self.attack_move_1, [attack_move_tasks[0], attack_move_entered_tasks[0]], 0)
                self.buttons.create(attack_move_2_label, self.attack_move_2, [attack_move_tasks[1], attack_move_entered_tasks[1]], 0)
                self.buttons.create(attack_move_3_label, self.attack_move_3, [attack_move_tasks[2], attack_move_entered_tasks[2]], 0)
                self.buttons.create(attack_move_4_label, self.attack_move_4, [attack_move_tasks[3], attack_move_entered_tasks[3]], 0)
                self.buttons.create(attack_type_label, self.attack_type, None, 0)
                self.buttons.create(top_border_label, top_border, None, 1)
                self.buttons.create(seperator_border_label, self.seperator_border, None, 1)
                self.buttons.create(seperator_border_2_label, self.seperator_border_2, None, 1)
                self.buttons.create(enemy_monster_interface_label, self.enemy_monster_interface, None, 0)
                self.buttons.create(enemy_monster_health_background_label, self.enemy_monster_health_background, None, 0)
                self.buttons.create(enemy_monster_health_label, self.enemy_monster_health, None, 0)
                self.buttons.create(player_monster_interface_label, self.player_monster_interface, None, 0)
                self.buttons.create(player_monster_health_background_label, self.player_monster_health_background, None, 0)
                self.buttons.create(player_monster_health_label, self.player_monster_health, None, 0)
                self.buttons.create(run_label, self.run_button, [run_task], 0)
                self.buttons.create(bag_label, self.bag, [bag_task], 0)
                self.buttons.create(dialog_box_label, self.dialog_box, None, 0)
                self.buttons.create(tubemon_switch_label, self.tubemon_switch, [lambda button : self.tubemon_switch_task()], 0)
            create_Buttons()

        spawn_gui()

    def reset_player_tubemon_list(self) -> None:
        self.player.active_tubemon_index = self.active_tubemon_index
        self.player.paste_tubemon_list(self.tubemon_list)

    def close_bag_gui(self) -> None:
        self.buttons.remove(self.bag_background_label)
        for labels in self.item_labels:
            self.buttons.remove(*labels)
        self.item_labels.clear()
        self.bag_background_label = None
        self.bag_open = False

    def set_attack_moves(self, monster : Monster) -> None:
        length : int = len(monster.attacks)
        message : str = None
        buttons : list[Button] = [self.attack_move_1, # top    left
                                self.attack_move_2, # top    right
                                self.attack_move_3, # bottom left
                                self.attack_move_4] # bottom right
        # set the button active if the monster has a move for that button
        # set the text of the button 
        for index, button in enumerate(buttons):
            button.active = length - 1 >= index
            message = monster.attacks[index]['name'] if button.active else Level.EMPTY
            button.message(message)

    def tubemon_switch_task(self, force_swap : bool = False) -> None:
        
        # reset attack type
        self.attack_type.update_message(msg = 'TYPE', color = 'black')
        buttons = self.buttons
        
        def create_tubemon_switch_gui() -> None:
            
            if self.bag_open:
                self.close_bag_gui()

            def remove_tubemon_switch_labels() -> None:
                if force_swap:
                    buttons.remove(background_label, *labels)
                else:
                    buttons.remove(back_label, background_label, *labels)

            RENDER_LAYER = 2
            BACKGROUND_LAYER = RENDER_LAYER
            LABEL_LAYER = BACKGROUND_LAYER + 1
            LABEL_IMAGE_LAYER = LABEL_LAYER + 1
            LABEL_HEALTH_LAYER = LABEL_IMAGE_LAYER + 1
            TUBEMON_LABELS = 6
            # labels position and size
            screen_horizontal_margins = 30
            label_horizontal_margins = 30
            screen_top_margins = 30
            screen_bottom_margins = 80
            label_vertical_margins = 30 
            width = (WIDTH - screen_horizontal_margins * 2 - label_horizontal_margins * 1) / 2
            height = (HEIGHT - screen_top_margins - screen_bottom_margins - label_vertical_margins * 2) / 3
            size = width, height
            topleft = screen_top_margins, label_horizontal_margins
            # labels image position and size
            image_vertical_margins = 10
            image_horizontal_margins = 10
            image_resized_height = height - image_vertical_margins * 2
            image_size = self.player.active_tubemon().sprites_size()
            image_height_ratio = image_resized_height / image_size[1]
            image_resized_width = image_size[0] * image_height_ratio
            image_topleft = image_horizontal_margins, image_vertical_margins
            image_resize = image_resized_width, image_resized_height
            # label health bar properties
            health_vertical_margins = 35
            health_horizontal_margins = 20
            health_bar_height = 5
            health_bar_background_width = width - (image_resized_width + image_horizontal_margins + health_horizontal_margins * 2)
            # label properties
            text_properties = 25, 'black', self.font_path, (160, 15), (False, False) # size, color, src_path, position, centering
            border = 'black', 4

            # The string labels representing the phsyical Labels 
            labels : list[str] = []

            # Create the labels showing the Tubemon
            for i in range(TUBEMON_LABELS):
                top  = topleft[0] + (label_vertical_margins   + height) * (i // 2)
                left = topleft[1] + (label_horizontal_margins + width ) * (i % 2)
                rect = Rect((left, top), size)

                tubemon = self.player.tubemon[i] if self.player.carried_tubemon() - 1 >= i else None
                if tubemon:
                    name = tubemon.name()
                    # Button shouldn't be clickable if it's the active Tubemon on the field
                    # or the tubemon has no health
                    switchable = i != self.player.active_tubemon_index and not tubemon.no_health()
                    image_sprite = tubemon.front_sprites()[0].copy()
                    image_sprite = pygame.transform.scale(image_sprite, image_resize)
                    image_color = None
                else:
                    name = ''
                    switchable = False
                    image_sprite = None
                    image_color = '#ADADADFF'

                # Text
                text = name, *text_properties

                # Creating the Button with the Tubemon info
                button = Button([], rect, self.battle_colors, text, border, switchable, True, None)
                label = f'Tubemon Switch Box {i}'
                labels.append(label)
                def swap_tubemon(buttons : ButtonSingleton, monster_index = i, monster_name = name, forced_swap = force_swap) -> None:
                    remove_tubemon_switch_labels()
                    if forced_swap:
                        self.enable_battle_dialog(f'Go {self.player.active_tubemon().name()}!')
                    else:
                        self.enable_battle_dialog(f'Switched {monster_name} for {self.player.active_tubemon().name()}.')
                    #self.player.swap_active_tubemon(monster_index)
                    self.player.active_tubemon_index = monster_index
                    self.refresh_monster_Names()
                    self.refresh_monster_health()
                    self.set_attack_moves(self.player.active_tubemon())
                    self.turn_timer = Timer(self.timer_seconds)
                buttons.create(label, button, [swap_tubemon], LABEL_LAYER)

                # Tubemon sprite image
                image = Label([], Rect(pygame.Vector2(rect.topleft) + pygame.Vector2(image_topleft), image_resize), image_color)
                image.image = image_sprite
                image_label = f'Tubemon Switch image box {i}'
                labels.append(image_label)
                buttons.create(image_label, image, None, LABEL_IMAGE_LAYER)

                # Health bar
                if tubemon:
                    health_bar_left = image.rect.right + health_horizontal_margins
                    health_bar_top = rect.top + text_properties[0] + health_vertical_margins
                    health_bar_background_width = button.rect.right - (image.rect.right + health_horizontal_margins * 2)
                    health_bar_width = health_bar_background_width * tubemon.health_percent()
                    
                    health_bar = Label([], Rect(health_bar_left, health_bar_top, health_bar_width, health_bar_height), 'dark green')
                    health_bar_label = f'Tubemon Switch Health Bar {i}'
                    labels.append(health_bar_label)
                    buttons.create(health_bar_label, health_bar, None, LABEL_HEALTH_LAYER + 1)

                    health_bar_background = Label([], Rect(health_bar_left, health_bar_top, health_bar_background_width, health_bar_height), '#ccccccff')
                    health_bar_background_label = f'Tubemon Switch Health Bar Background {i}'
                    labels.append(health_bar_background_label)
                    buttons.create(health_bar_background_label, health_bar_background, None, LABEL_HEALTH_LAYER)

            # Back button creation
            if not force_swap:
                back_vertical_margins = 10
                screen_bottom_margins_position = HEIGHT - screen_bottom_margins
                back_height = screen_bottom_margins - back_vertical_margins * 2
                back_size = width / 2, back_height
                back_top = screen_bottom_margins_position + (screen_bottom_margins - back_height) / 2
                back_topleft = label_horizontal_margins, back_top
                back_label = 'Tubemon Switch Back'
                back_text = 'Back', *self.abtscs
                back = Button([], Rect(back_topleft, back_size), self.battle_colors, back_text, border)
                def back_task(buttons : ButtonSingleton) -> None:
                    remove_tubemon_switch_labels()
                    self.enable_battle_labels()
                buttons.create(back_label, back, [back_task], LABEL_LAYER)

            # Background button creation
            background_label = 'Tubemon Switch Background'
            background = Label([], Rect(0, 0, WIDTH, HEIGHT), '#7F7F7FFF')
            buttons.create(background_label, background, None, BACKGROUND_LAYER)

        self.disable_battle_labels()

        create_tubemon_switch_gui()

    def reset_battle_variables(self) -> None:
        self.turn = Level.PLAYER_TURN
        self.battle_run_away = False
        self.battle_finished_timer = None
        self.battle_bag_used_item = None

    def refresh_monster_health(self) -> None:
        # update monster hotbars
        self.enemy_monster_health.rect.w = int(self.enemy_monster_health_background.rect.w * self.enemy_monster.health_percent())
        self.player_monster_health.rect.w = int(self.player_monster_health_background.rect.w * self.player.active_tubemon().health_percent())

    def refresh_monster_Names(self) -> None:
        # update monster name hotbars
        self.enemy_monster_interface.message(self.enemy_monster.name())
        self.player_monster_interface.message(self.player.active_tubemon().name())
    
    def enable_battle_dialog(self, message : str) -> None:
        self.disable_battle_labels()
                
        # activate dialog box label
        self.dialog_box.activate()
        self.dialog_box.text = (message, 25, 'black', self.font_path, (12, 22))

    def disable_battle_dialog(self) -> None:
        
        self.enable_battle_labels()

        # activate dialog box label
        self.dialog_box.deactivate()
        self.dialog_box.text = None

    def disable_battle_labels(self) -> None:
        # disable all unneeded labels, attack buttons, attack type label, seperation border
        for label in self.battle_labels:
            label.deactivate()

    def enable_battle_labels(self) -> None:
        
        # enable all needed labels, attack buttons, attack type label, seperation border
        for label in self.battle_labels:
            label.activate()
        
        # enable all the attack moves that are Empty
        for button in [self.attack_move_1, self.attack_move_2, self.attack_move_3, self.attack_move_4]:
            if button.text[0] == Level.EMPTY:
                button.active = False   

    def delete_Buttons(self) -> None:
        self.buttons.remove_all()
        self.battle_labels.clear()
        self.battle_labels : list[Button] = None
        self.attack_move_1 : Button = None
        self.attack_move_2 : Button = None
        self.attack_move_3 : Button = None
        self.attack_move_4 : Button = None
        self.attack_type : Label = None
        self.dialog_box : Label = None
        self.top_border : Label = None
        self.seperator_border : Label = None
        self.seperator_border_2 : Label = None
        self.enemy_monster_interface : Label = None
        self.enemy_monster_health_background : Label = None
        self.enemy_monster_health : Label = None
        self.player_monster_interface : Label = None
        self.player_monster_health_background : Label = None
        self.player_monster_health : Label = None
        self.bag : Button = None
        self.run_button : Button = None
        self.tubemon_switch : Button = None

    def battle_update(self, delta_time : float, events : list[pygame.event.Event]) -> None:
        left_mouse_clicked : bool = False
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                self.battle_finished_timer = Timer(0)
            if event.type == pygame.MOUSEBUTTONDOWN:
                LEFT_MOUSE_BUTTON = 1
                left_mouse_clicked = event.button == LEFT_MOUSE_BUTTON
        
        # no turns should be checked when the finished battle timer has begun
        if self.battle_finished_timer:
            if self.battle_finished_timer.complete():
                try_stop(self.battle_audio)
                # Leave the message display up until the user presses the left mouse button
                if left_mouse_clicked:
                    self.disable_battle_dialog()
                    self.reset_battle_variables()
                    self.delete_Buttons()
                    self.reset_player_tubemon_list()
                    self.game_state = GAME_STATE
                    try_stop(self.battle_victory_audio)
                    try_play(self.ambiance_music, -1)

        elif self.turn == Level.PLAYER_TURN:
            
            # user clicked something and there are animations running
            if self.turn_timer and self.turn_timer.complete():
                self.turn_timer = None

                # player is running away or using the tubebox item
                if self.battle_run_away:
                    self.battle_finished_timer = Timer(0)
                elif self.battle_bag_used_item == Item.TUBEBOX:
                    self.battle_finished_timer = Timer(0)
                    try_play(self.battle_victory_audio, -1)
                elif self.enemy_monster.no_health():
                    self.enable_battle_dialog(f'The enemy\'s {self.enemy_monster.name()} has fainted.')
                    self.battle_finished_timer = Timer(self.timer_seconds)
                    try_stop(self.battle_audio)
                    try_play(self.battle_victory_audio)
                else:
                    self.turn = Level.ENEMY_TURN
                    #self.disable_battle_dialog()

        elif self.turn == Level.ENEMY_TURN:
            # enemy hasn't started their attack
            if not self.turn_timer:
                random_attack = random.choice(self.player.active_tubemon().attacks)
                self.enemy_monster.attack(random_attack, self.player.active_tubemon(), True)
                self.enable_battle_dialog(f'{self.enemy_monster.name()} used {random_attack["name"]} on {self.player.active_tubemon().name()}.')
                self.refresh_monster_health()
                self.turn_timer = Timer(self.timer_seconds)

            # enemy has start their attack and finished its animations
            if self.turn_timer and self.turn_timer.complete():
                self.turn_timer = None
                
                if self.player.active_tubemon().no_health():
                    
                    if self.player.non_fainted_tubemon() < 1:
                        self.enable_battle_dialog(f'Your {self.player.active_tubemon().name()} has fainted.')
                        self.battle_finished_timer = Timer(self.timer_seconds)
                        try_stop(self.battle_audio)
                    else:
                        self.tubemon_switch_task(True)
                else:
                    self.turn = Level.PLAYER_TURN
                    self.disable_battle_dialog()

        self.enemy_monster.update()
        self.player.active_tubemon().update()

    def battle_draw(self) -> None:
        #pygame.draw.rect(self.display_surface, 'white', self.display_surface.get_rect())
        self.display_surface.blit(self.battle_background.image, self.battle_background.rect)
        self.enemy_monster.draw(self.display_surface)
        self.player.active_tubemon().draw(self.display_surface)

    def battle_detect(self) -> None:

        if not self.player.moving: return

        collided_battle_zones: list[BattleZone] = self.player.collision_rect.collideobjectsall(self.battle_zone_group.sprites())
        # nothing has been collided with
        if not collided_battle_zones:
            return
            
        removed_battle_zones : list[BattleZone] = []
        # no battle if the player is less than 25% on the grass
        # remove the collided areas that the player is less than 25% in
        for battle_zone in collided_battle_zones:
            
            overlapping_area = (min(self.player.collision_rect.right , battle_zone.rect.right)  - \
                                max(self.player.collision_rect.left  , battle_zone.rect.left))  * \
                               (min(self.player.collision_rect.bottom, battle_zone.rect.bottom) - \
                                max(self.player.collision_rect.top   , battle_zone.rect.top))
            
            if overlapping_area < (self.player.collision_rect.w * self.player.collision_rect.h) * 0.3:
                removed_battle_zones.append(battle_zone)
        
        # items can't be removed from a list being itereated
        for battle_zone in removed_battle_zones:
            collided_battle_zones.remove(battle_zone)

        battle = False

        for _ in range(0, len(collided_battle_zones)):
            battle = random.random() < 0.01
            if battle: 
                break

        if battle:
            self.enemy_monster = Monster.spawn_random((800, 100))
            self.game_state = BATTLE_TRANSITION
            self.flash_animation.start()
            try_stop(self.ambiance_music)
            try_play(self.init_battle_audio)

    # MENU --------------------------

    def menu_gui_init(self) -> None:

        # colors
        bgc1 = '#A0654Dff' # label background color 1, button color
        bgc2 = '#BC775Cff' # label background color 2, button hover color
        bgc3 = '#7F4F3Eff' # label background color 3, button click color
        lc1  = '#D38658ff' # label            color 1, button font color

        colors = [bgc1, bgc2, bgc3, lc1]

        # button attributes
        text = [25, colors[3], self.font_path, None, (True, True)] # attributes, size, color, font_path, position, centering
        rect = Rect(0, 0, 300, 80) 

        title_label    : str = 'Title'
        play_label     : str = 'Play'
        settings_label : str = 'Settings'
        exit_label     : str = 'Exit'

        left_save_label   : str = 'Left Save'
        middle_save_label : str = 'Middle Save'
        right_save_label  : str = 'Right Save'
        back_label        : str = 'Back'

        offline_label     : str = 'Offline'
        online_label      : str = 'Online'

        background_label  : str = 'Background'
        volume_label      : str = 'Volume'

        def create_title_buttons(buttons : ButtonSingleton) -> None:
            play_button     = Button([], Rect(rect), tuple(colors[:3]), ('Play'    , text[0], text[1], text[2], text[3], text[4]))
            settings_button = Button([], Rect(rect), tuple(colors[:3]), ('Settings', text[0], text[1], text[2], text[3], text[4]))
            exit_button     = Button([], Rect(rect), tuple(colors[:3]), ('Exit'    , text[0], text[1], text[2], text[3], text[4]))
            title           =  Label([], Rect(0, 0, 450, 100), colors[0], ('TubeMon', 35, colors[3], self.font_path, None, (True, True)))
            
            hs = 25 # horizontal spacing
            title.rect.top = 50 + 20
            play_button.rect.top = title.rect.bottom + hs + 20
            settings_button.rect.top = play_button.rect.bottom + hs
            exit_button.rect.top = settings_button.rect.bottom + hs
            # center all the labels/buttons on the x axis
            center_x = WIDTH // 2
            for button in [title, play_button, settings_button, exit_button]:
                button.rect.centerx = center_x   

            #print(f'Create {play_label}, {settings_label} and {exit_label}.')
            
            buttons.create(title_label   , title          , None    , 0)
            buttons.create(play_label    , play_button    , [play]    , 0)
            buttons.create(settings_label, settings_button, [settings], 0)
            buttons.create(exit_label    , exit_button    , [exit]    , 0)
            
        def remove_title_buttons(buttons : ButtonSingleton) -> None:
            #print(f'Remove {play_label}, {settings_label} and {exit_label}.')
            buttons.remove(title_label, play_label, settings_label, exit_label)
            
        def create_play_buttons(buttons : ButtonSingleton) -> None:

            SAVES_FOLDER_NAME : str = 'saves'
            LEFT_SAVES_FILE_NAME : str = 'save 1'
            MIDDLE_SAVES_FILE_NAME : str = 'save 2'
            RIGHT_SAVES_FILE_NAME : str = 'save 3'
            NEW_SAVE : str = 'New Save'

            def try_saves_folder_path() -> str | None:
                # Get the 'saves' folder in the current directory if it exists
                saves_directory : str = os.path.abspath(SAVES_FOLDER_NAME)
                return saves_directory if os.path.exists(saves_directory) else None

            def try_save_file_path(saves_folder_path : str, save_file_name : str) -> str | None:
                # Get the save file in the 'saves' directory if it exists
                save_file_path : str = os.path.normpath(os.path.join(saves_folder_path, save_file_name))
                return save_file_path if os.path.exists(save_file_path) else None

            # play menu button attributes
            saves_folder_path : str | None = try_saves_folder_path()
            if saves_folder_path:
                left_name   : str = LEFT_SAVES_FILE_NAME   if try_save_file_path(saves_folder_path, LEFT_SAVES_FILE_NAME)   else NEW_SAVE
                middle_name : str = MIDDLE_SAVES_FILE_NAME if try_save_file_path(saves_folder_path, MIDDLE_SAVES_FILE_NAME) else NEW_SAVE
                right_name  : str = RIGHT_SAVES_FILE_NAME  if try_save_file_path(saves_folder_path, RIGHT_SAVES_FILE_NAME)  else NEW_SAVE
            else:
                left_name = NEW_SAVE
                middle_name = NEW_SAVE
                right_name = NEW_SAVE

            text = 25, colors[3], self.font_path # size, color, font_path,
            size = pygame.Vector2(300, 300)

            left_save   = Button([], Rect((0, 100), size), tuple(colors[:3]), (left_name, *text))
            middle_save = Button([], Rect((0, 100), size), tuple(colors[:3]), (middle_name, *text))
            right_save  = Button([], Rect((0, 100), size), tuple(colors[:3]), (right_name, *text))
            back_button = Button([], Rect(15, 0, 80, 40), None, ('<--', 25, colors[0], self.font_path))
            
            online_s = 200, 50 # size
            online_m = 25 # margins

            online      = Button([], Rect((0, left_save.rect.bottom + online_m), online_s), tuple(colors[:3]), ('Online', *text), active = not ONLINE)
            offline     = Button([], Rect((0, left_save.rect.bottom + online_m), online_s), tuple(colors[:3]), ('Offline', *text), active = ONLINE)

            # Set button positions
            hs = 15 # horizontal spacing
            save_button_space       = hs * 2 + size.x * 3
            left_save.rect.left     = (WIDTH - save_button_space) // 2
            middle_save.rect.left   = left_save.rect.right + hs
            right_save.rect.left    = middle_save.rect.right + hs
            back_button.rect.bottom = HEIGHT - 15

            online.rect.x = (WIDTH - (online.rect.w * 2 + online_m)) / 2
            offline.rect.x = online.rect.right + online_m

            def toggle_online(buttons : ButtonSingleton, is_online : bool = True) -> None:
                ONLINE = is_online
                online.active = not ONLINE # False
                offline.active = ONLINE # True

            def save(buttons : ButtonSingleton, save_file_name: str) -> None:

                def get_or_make_save_file(save_file : str) -> tuple[str, bool]:
                    def get_or_make_saves_folder() -> str:
                        # Create a 'saves' folder in the current directory if it doesn't exist
                        saves_directory : str = os.path.abspath(SAVES_FOLDER_NAME)
                        if not os.path.exists(saves_directory):
                            os.mkdir(saves_directory)
                        return saves_directory
                    # Create a save file in the 'saves' directory if it doesn't exist
                    created = False
                    save_file_path : str = os.path.normpath(os.path.join(get_or_make_saves_folder(), save_file))
                    if not os.path.exists(save_file_path):
                        created = True
                        with open(save_file_path, 'x'): pass
                    return save_file_path, created

                self.save_file_path, created = get_or_make_save_file(save_file_name)
                if created:
                    self.new_save()
                else:
                    self.load_save()

                remove_play_buttons(buttons)
                self.game_state = GAME_STATE

            def back(buttons : ButtonSingleton) -> None:
                remove_play_buttons(buttons)
                create_title_buttons(buttons)

            buttons.create(left_save_label  , left_save  , [lambda buttons : save(buttons, LEFT_SAVES_FILE_NAME)], 0)
            buttons.create(middle_save_label, middle_save, [lambda buttons : save(buttons, MIDDLE_SAVES_FILE_NAME)], 0)
            buttons.create(right_save_label , right_save , [lambda buttons : save(buttons, RIGHT_SAVES_FILE_NAME)], 0)
            buttons.create(online_label     , online     , [lambda buttons : toggle_online(buttons, True)], 0)
            buttons.create(offline_label    , offline    , [lambda buttons : toggle_online(buttons, False)], 0)
            buttons.create(back_label       , back_button, [back], 0)

        def remove_play_buttons(buttons : ButtonSingleton) -> None:
            #print(f'Remove {left_save_label}, {middle_save_label}, {right_save_label} and {back_label}.')
            buttons.remove(left_save_label, middle_save_label, right_save_label, back_label, online_label, offline_label)

        def create_settings_buttons(buttons : ButtonSingleton) -> None:
            # play menu button attributes
            text = ('Settings', 25, colors[3], self.font_path, (0, 12), (True, False)) # attributes, size, color, font_path, position, centering
            size = pygame.Vector2(WIDTH - 40, HEIGHT - 80)

            def music(buttons : ButtonSingleton) -> None:
            #def music(buttons : ButtonSingleton) -> None:
                global MASTER_VOLUME

                percentage = (volume.button.rect.centerx - volume.bar.rect.x) / volume.bar.rect.w

                if MASTER_VOLUME != percentage:
                    MASTER_VOLUME = percentage # NOTE: doesn't actually update the global MASTER_VOLUME across all files
                    try_update_all(percentage) # update all the sounds with this volume
            
            background = Label ([], Rect((20, 20), size), colors[2], tuple(text))
            volume = Slider([], (Rect(0, 0, 125, 40), Rect(0, 0, 25, 25), Rect(0, 0, size.x - 125 - 25 - 20, 4)), (colors[0], colors[1], colors[1]), ('Music', 25, text[2], text[3]))

            # Set button positions
            vs = 15 # vertical spacing
            hs = 50 # horizontal spacing
            # music text
            volume.rect.left = background.rect.left + vs
            volume.rect.top = background.rect.top + hs
            # music bar
            volume.bar.rect.x = volume.rect.right + vs
            volume.bar.rect.centery = volume.rect.centery
            # music slider
            percentage = MASTER_VOLUME * volume.bar.rect.w
            volume.button.rect.centerx = volume.bar.rect.x + percentage
            volume.button.rect.centery = volume.bar.rect.centery
            # back button
            def back(buttons : ButtonSingleton) -> None:
                remove_settings_buttons(buttons)
                create_title_buttons(buttons)
            back_button = Button([], Rect(15, 0, 80, 40), None, ('<--', 25, colors[0], self.font_path))
            back_button.rect.bottom = HEIGHT - 15
            buttons.create(back_label       , back_button, [back], 0)
            buttons.create(background_label , background , None, 0)
            buttons.create(volume_label , volume , [music], 0)

        def remove_settings_buttons(buttons : ButtonSingleton) -> None:
            #print(f'Remove {back_label}, {background_label}, volume_label.')
            buttons.remove(background_label, back_label, volume_label) 

        def play(buttons : ButtonSingleton) -> None:
            remove_title_buttons(buttons)
            create_play_buttons(buttons)

        def settings(buttons : ButtonSingleton) -> None:
            remove_title_buttons(buttons)
            create_settings_buttons(buttons)
        
        def exit(buttons : ButtonSingleton) -> None:
            remove_title_buttons(buttons)
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        create_title_buttons(self.buttons)

    def menu_update(self, delta_time : float) -> None:
        def menu_update_background(self, delta_time : float) -> None:
            # apply a scrolling/wraping effect to the background
            # reset the background position to apply the wraping effect
            if self.menu_background.rect.top > HEIGHT: # image is below the screen(not visible)
                self.menu_background.rect.bottom = HEIGHT # position the image's bottom with the screen's bottom
                self.menu_background_y = self.menu_background.rect.top # loop the y position counter
            # move and update the image's y position
            self.menu_background_y += 15 * delta_time # 15 units every second
            self.menu_background.rect.top = self.menu_background_y # update the y position
        # update the moving background
        menu_update_background(self, delta_time)
    
    def menu_draw(self) -> None:
        def menu_draw_background(self) -> None:
            # draw the fake image from the top of the original image to apply a wrapping effect
            self.display_surface.blit(self.menu_background.image, (self.menu_background.rect.x, self.menu_background.rect.top - self.menu_background.rect.height))
            # draw the original image
            self.menu_background.draw(self.display_surface)
        menu_draw_background(self)

    # PAUSE --------------------------

    def pause_gui_init(self) -> None:
        
        # colors
        lbgc1 = '#A0654Dff' # label background color1 inbetween
        lbgc2 = '#BC775Cff' # label background color2 lightest
        lbgc3 = '#7F4F3Eff' # label background color3 darkest
        lc1 = '#D38658ff' # label color 1
        pause_background_color = lc1

        # tubemon
        tubemon_background_label         : str = 'Tubemon Background'
        tubemon_top_left_label           : str = 'Tubemon Top Left'
        tubemon_top_right_label          : str = 'Tubemon Top Right'
        tubemon_mid_left_label           : str = 'Tubemon Mid Left'
        tubemon_mid_right_label          : str = 'Tubemon Mid Right'
        tubemon_bottom_left_label        : str = 'Tubemon Bottom Left'
        tubemon_bottom_right_label       : str = 'Tubemon Bottom Right'
        tubemon_top_left_image_label     : str = 'Tubemon Top Left Image'
        tubemon_top_right_image_label    : str = 'Tubemon Top Right Image'
        tubemon_mid_left_image_label     : str = 'Tubemon Mid Left Image'
        tubemon_mid_right_image_label    : str = 'Tubemon Mid Right Image'
        tubemon_bottom_left_image_label  : str = 'Tubemon Bottom Left Image'
        tubemon_bottom_right_image_label : str = 'Tubemon Bottom Right Image'
        # bag
        bag_background_label : str = 'Bag Background'
        bag_item_labels : list[str] = []


        def create_left_pause_gui() -> None:

            pmr = rect.Rect(25, 50, 250, HEIGHT - 100) # pause_menu_rect
            pbc = [lbgc1,lbgc2,lbgc3] # pause_button_colors
            pbf = [15, lc1, self.font_path, (0, 12), (True, False)] # menu_button_font - attributes, size, color, font_path, position, centering
            pbr = rect.Rect(0, 0, 0, 40) # menu button rect

            background_label : str = 'Background'
            tubemon_label    : str = 'tubemon'
            bag_label        : str = 'bag'
            name_label       : str = 'name'
            save_label       : str = 'save'
            options_label    : str = 'options'
            menu_label       : str = 'menu'

            NON_ACTIVE        : int = -1
            TUBEMON_ACTIVE    : int =  0
            BAG_ACTIVE        : int =  1
            NAME_ACTIVE       : int =  2
            SAVE_ACTIVE       : int =  3
            OPTIONS_ACTIVE    : int =  4
            active_right_menu : int =  NON_ACTIVE

            def clear_right_gui() -> None:
                if   active_right_menu == TUBEMON_ACTIVE : self.buttons.remove(tubemon_background_label,
                                                                               tubemon_top_left_label,
                                                                               tubemon_top_right_label,
                                                                               tubemon_mid_left_label,
                                                                               tubemon_mid_right_label,
                                                                               tubemon_bottom_left_label,
                                                                               tubemon_bottom_right_label,
                                                                               tubemon_top_left_image_label,
                                                                               tubemon_top_right_image_label,
                                                                               tubemon_mid_left_image_label,
                                                                               tubemon_mid_right_image_label,
                                                                               tubemon_bottom_left_image_label,
                                                                               tubemon_bottom_right_image_label)
                elif active_right_menu == BAG_ACTIVE     : 
                    self.buttons.remove(bag_background_label, *bag_item_labels)
                    bag_item_labels.clear()
                elif active_right_menu == NAME_ACTIVE    : pass
                elif active_right_menu == SAVE_ACTIVE    : pass
                elif active_right_menu == OPTIONS_ACTIVE : pass

            def update_right_gui(active_right : bool) -> bool:
                nonlocal active_right_menu
                clear_right_gui()
                if active_right_menu == active_right: 
                    active_right_menu = NON_ACTIVE
                    return True
                active_right_menu = active_right
                return False

            # button tasks
            def tubemon_task(buttons : ButtonSingleton) -> None:
                if update_right_gui(TUBEMON_ACTIVE) : return 

                tubemon_gui : list[Label] = create_tubemon_gui()
                
                SLOTS = 6
                # loop through all the monsters the player curently has and update all the names and images in the gui
                for index, monster in enumerate(self.player.tubemon):
                    
                    text_label = tubemon_gui[index]
                    image_label = tubemon_gui[index + SLOTS]

                    # update the text to the monsters name
                    text_label.message(monster.name())
                    
                    # update the image to the monesters sprite
                    image : Surface = monster.front_sprites()[0].copy()
                    image_label.image = image

                    # center monster image with gui center
                    image_label.rect.topleft = text_label.rect.center
                    left = image_label.rect.x - image.get_width() / 2
                    top  = image_label.rect.y - image.get_height() / 2
                    image_label.rect.topleft = (left, top)
            def bag_task(buttons : ButtonSingleton):
                if update_right_gui(BAG_ACTIVE) : return
                create_bag_gui()
            def name_task(buttons : ButtonSingleton):
                if update_right_gui(NAME_ACTIVE) : return 
                print(f'name')
            def save_task(buttons : ButtonSingleton):
                self.save_player()
            def options_task(buttons : ButtonSingleton):
                if update_right_gui(OPTIONS_ACTIVE) : return 
                print(f'options')
            def menu_task(buttons : ButtonSingleton):
                self.buttons.remove_all()
                self.game_state = MENU_STATE
                # remove player
                self.visible_sprites.remove(self.player)
                self.collide_sprites.remove(self.player)
                del self.player
                self.player = None
                self.menu_gui_init()

            background =  Label([], pmr, pause_background_color, ('PAUSE', 25, lbgc1, self.font_path, (0, 12), (True, False)))
            tubemon    = Button([], Rect(pbr), pbc, ('TubeMon', pbf[0], pbf[1], pbf[2], pbf[3], pbf[4]))
            bag        = Button([], Rect(pbr), pbc, ('Bag'    , pbf[0], pbf[1], pbf[2], pbf[3], pbf[4]))
            name       = Button([], Rect(pbr), pbc, ('Name'   , pbf[0], pbf[1], pbf[2], pbf[3], pbf[4]))
            save       = Button([], Rect(pbr), pbc, ('Save'   , pbf[0], pbf[1], pbf[2], pbf[3], pbf[4]))
            options    = Button([], Rect(pbr), pbc, ('Options', pbf[0], pbf[1], pbf[2], pbf[3], pbf[4]))
            menu       = Button([], Rect(pbr), pbc, ('Menu'   , pbf[0], pbf[1], pbf[2], pbf[3], pbf[4]))

            self.buttons.create(background_label, background, None, -1)
            self.buttons.create(tubemon_label, tubemon, [tubemon_task], 0)
            self.buttons.create(bag_label, bag, [bag_task], 0)
            self.buttons.create(name_label, name, [name_task], 0)
            self.buttons.create(save_label, save, [save_task], 0)
            self.buttons.create(options_label, options, [options_task], 0)
            self.buttons.create(menu_label, menu, [menu_task], 0)

            vs = 10 # vertical spacing
            xm = 5 # x margin
            tubemon.rect.topleft = (background.rect.left + xm, background.rect.top + 70)
            bag.rect.topleft     = (tubemon.rect.left, tubemon.rect.bottom + vs)
            name.rect.topleft    = (tubemon.rect.left, bag.rect.bottom + vs)
            save.rect.topleft    = (tubemon.rect.left, name.rect.bottom + vs)
            options.rect.topleft = (tubemon.rect.left, save.rect.bottom + vs)
            menu.rect.topleft    = (tubemon.rect.left, options.rect.bottom + vs)

            # set the width of each of the buttons
            for button in [tubemon, bag, name, save, options, menu]:
                button.rect.width   = background.rect.width - 2 * xm

        # Right pause menu properties
        right_background_y = 50
        right_background_width = HEIGHT - 100
        right_background_rect = rect.Rect(0, right_background_y, right_background_width, right_background_width)
        right_background_rect.right = WIDTH - 25
        right_background_color = pause_background_color
        RIGHT_BACKGROUND_RENDER_ORDER = 0
        RIGHT_LABEL_1_RENDER_ORDER = RIGHT_BACKGROUND_RENDER_ORDER + 1
        RIGHT_LABEL_2_RENDER_ORDER = RIGHT_LABEL_1_RENDER_ORDER + 1

        def create_tubemon_gui() -> list[Label]:

            pmr = rect.Rect(25, 50, 250, HEIGHT - 100) # pause_menu_rect
            pbc = [lbgc1,lbgc2,lbgc3] # pause_button_colors
            pbf = [15, lc1, self.font_path, (0, 12), (True, False)] # menu_button_font - attributes, size, color, font_path, position, centering
            pbr = rect.Rect(0, 0, 0, 40) # menu button rect

            tgbw = right_background_width # tubemon gui background width
            tgbr = Rect(right_background_rect) # tubemon gui background rect

            tgsmar = 10 # tubemon_gui_slot_margins
            tgsw = (tgbw - tgsmar * 3) // 2 # tubemon_gui_slot_width
            tgsh = (tgbw - tgsmar * 4) // 3 # tubemon_gui_slot_height
            tgss = (tgsw, tgsh) # tubemon_gui_slot_size
            tgsl = tgbr.x + tgsmar * 1 + tgsw * 0 # tubemon gui slot left
            tgsr = tgbr.x + tgsmar * 2 + tgsw * 1 # tubemon gui slot right
            tgst = tgbr.y + tgsmar * 1 + tgsh * 0 # tubemon gui slot top
            tgsmid = tgbr.y + tgsmar * 2 + tgsh * 1 # tubemon gui slot mid
            tgsb = tgbr.y + tgsmar * 3 + tgsh * 2 # tubemon gui slot bottom

            tgsf = ('Empty', 15, lc1, self.font_path, (0, tgsh - 20), (True, False)) # tubemon gui slot font - attributes, size, color, font_path, position, centering

            tgsimar = 20 # tubemon gui slot image margin
            tgsis = (tgsw - tgsimar * 2, tgsh - tgsimar * 2) # tubemon gui slot image size

            tubemon_background         = Label([], Rect(tgbr), right_background_color)
            tubemon_top_left           = Label([], Rect((tgsl, tgst)  , tgss), lbgc1, tuple(tgsf)) # top left slot
            tubemon_top_right          = Label([], Rect((tgsr, tgst)  , tgss), lbgc1, tuple(tgsf)) # top right slot
            tubemon_mid_left           = Label([], Rect((tgsl, tgsmid), tgss), lbgc1, tuple(tgsf)) # mid left slot
            tubemon_mid_right          = Label([], Rect((tgsr, tgsmid), tgss), lbgc1, tuple(tgsf)) # mid right slot
            tubemon_bottom_left        = Label([], Rect((tgsl, tgsb)  , tgss), lbgc1, tuple(tgsf)) # bottom left slot
            tubemon_bottom_right       = Label([], Rect((tgsr, tgsb)  , tgss), lbgc1, tuple(tgsf)) # bottom right slot
            tubemon_top_left_image     = Label([], Rect((tgsl + tgsimar, tgst   + tgsimar), tgsis)) # top left slot image
            tubemon_top_right_image    = Label([], Rect((tgsr + tgsimar, tgst   + tgsimar), tgsis)) # top right slot image
            tubemon_mid_left_image     = Label([], Rect((tgsl + tgsimar, tgsmid + tgsimar), tgsis)) # mid left slot image
            tubemon_mid_right_image    = Label([], Rect((tgsr + tgsimar, tgsmid + tgsimar), tgsis)) # mid right slot image
            tubemon_bottom_left_image  = Label([], Rect((tgsl + tgsimar, tgsb   + tgsimar), tgsis)) # bottom left slot image
            tubemon_bottom_right_image = Label([], Rect((tgsr + tgsimar, tgsb   + tgsimar), tgsis)) # bottom right slot image

            self.buttons.create(tubemon_background_label, tubemon_background, None, RIGHT_BACKGROUND_RENDER_ORDER)
            self.buttons.create(tubemon_top_left_label, tubemon_top_left, None, RIGHT_LABEL_1_RENDER_ORDER)
            self.buttons.create(tubemon_top_right_label, tubemon_top_right, None, RIGHT_LABEL_1_RENDER_ORDER)
            self.buttons.create(tubemon_mid_left_label, tubemon_mid_left, None, RIGHT_LABEL_1_RENDER_ORDER)
            self.buttons.create(tubemon_mid_right_label, tubemon_mid_right, None, RIGHT_LABEL_1_RENDER_ORDER)
            self.buttons.create(tubemon_bottom_left_label, tubemon_bottom_left, None, RIGHT_LABEL_1_RENDER_ORDER)
            self.buttons.create(tubemon_bottom_right_label, tubemon_bottom_right, None, RIGHT_LABEL_1_RENDER_ORDER)
            self.buttons.create(tubemon_top_left_image_label, tubemon_top_left_image, None,  RIGHT_LABEL_2_RENDER_ORDER)
            self.buttons.create(tubemon_top_right_image_label, tubemon_top_right_image, None,  RIGHT_LABEL_2_RENDER_ORDER)
            self.buttons.create(tubemon_mid_left_image_label, tubemon_mid_left_image, None,  RIGHT_LABEL_2_RENDER_ORDER)
            self.buttons.create(tubemon_mid_right_image_label, tubemon_mid_right_image, None,  RIGHT_LABEL_2_RENDER_ORDER)
            self.buttons.create(tubemon_bottom_left_image_label, tubemon_bottom_left_image, None,  RIGHT_LABEL_2_RENDER_ORDER)
            self.buttons.create(tubemon_bottom_right_image_label, tubemon_bottom_right_image, None,  RIGHT_LABEL_2_RENDER_ORDER)

            return [tubemon_top_left, tubemon_top_right,
                    tubemon_mid_left, tubemon_mid_right,
                    tubemon_bottom_left, tubemon_bottom_right,
                    tubemon_top_left_image, tubemon_top_right_image,
                    tubemon_mid_left_image, tubemon_mid_right_image,
                    tubemon_bottom_left_image, tubemon_bottom_right_image]

        def create_bag_gui() -> None:

            # Background
            bag_rect = Rect(right_background_rect)
            bag = Label([], bag_rect, right_background_color)
            self.buttons.create(bag_background_label, bag, None, RIGHT_BACKGROUND_RENDER_ORDER)

            def create_items() -> None:
                
                # position properties
                horizontal_margins = 10
                vertical_margins = 10
                quantity_width = 50
                text_width = bag_rect.w - quantity_width - horizontal_margins * 3
                height = 50
                text = 15, lbgc3, self.font_path # size, color, source
                
                for index, (name, quantity_number) in enumerate(self.player.bag.items()):
                    # text label
                    item_text = Label([], Rect(bag_rect.x + horizontal_margins, 0, text_width, height), None, (f'{name}', *text, (10, 0), (False, True)), None, True)
                    item_text.rect.top = bag_rect.top + vertical_margins + (height + vertical_margins) * index
                    item_text_label : str = f'{name}'
                    bag_item_labels.append(item_text_label)
                    self.buttons.create(item_text_label, item_text, None, RIGHT_LABEL_1_RENDER_ORDER)
                    
                    # quantity label
                    quantity_rect = Rect(item_text.rect.right + horizontal_margins, item_text.rect.y, quantity_width, height)
                    quantity = Label([], quantity_rect, None, (f'{quantity_number}', *text, (0, 0), (True, True)), None, True)
                    quantity_label : str = f'{name} {quantity_number}'
                    bag_item_labels.append(quantity_label)
                    self.buttons.create(quantity_label, quantity, None, RIGHT_LABEL_1_RENDER_ORDER)

            create_items()
            
        create_left_pause_gui()

    def pause_update(self, delta_time : float, events : list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.buttons.remove_all()
                self.game_state = GAME_STATE
                return

    def pause_draw(self) -> None:
        # render the game as the background
        self.game_draw()

    # NETWORKING ---------------------

    def thread_network(self)-> None:
        global ONLINE
        while ONLINE and not self.thread_stop: # race condition
            
            # send data to server
            data : dict[int, dict[int, Any]] = {self.client.client_id : {}}
            with self.mutex:
                data[self.client.client_id][MOVEMENT_ID] = self.player.rect.topleft
            b_data_str : bytes = dict_to_str_bytes(data)
            self.client.send_all(b_data_str)

            # receive data from server
            recieved_data, connected = self.client.receive()
            if not connected or not recieved_data:
                print(f'Going Offline.')
                ONLINE = False # possible race condition
                return
            
            # convert from string bytes to dictionary
            new_data_str : str = recieved_data.decode()
            
            # No connections to connect to
            if new_data_str == GRIZZLY_CO:
                #print(f'Code: {new_data_str}')
                # remove all players
                if self.online_players:
                    with self.mutex:
                        for _, player in self.online_players.items():
                            self.visible_sprites.remove(player)
                        self.online_players.clear()
                continue
            
            new_data : dict[int, dict[int, Any]] = str_to_dict(new_data_str)
   
            # new
            # new player_ids are not in old players_ids
            for new_player_id in new_data.keys():
                with self.mutex:
                    if not new_player_id in self.online_players.keys():
                        print(f'player #{new_player_id} joined.')
                        self.online_players[new_player_id] = DummyPlayer(new_data[new_player_id][MOVEMENT_ID], self.visible_sprites)

            # delete
            # old player_ids are not in the new players_ids
            # fetch the old players to delete
            deleted_player_ids = []
            with self.mutex:
                for old_player_id in self.online_players.keys():
                    if not old_player_id in new_data.keys():
                        print(f'player #{old_player_id} left.')
                        deleted_player_ids.append(old_player_id)
            # remove other players and their sprites
            for player_id in deleted_player_ids:
                self.mutex.acquire()
                self.visible_sprites.remove(self.online_players[player_id])
                self.online_players.pop(player_id)
                self.mutex.release()

            # update online players stats
            with self.mutex:
                for player_id in self.online_players.keys():
                    # update online player stats
                    self.online_players[player_id].rect.topleft = new_data[player_id][MOVEMENT_ID]

