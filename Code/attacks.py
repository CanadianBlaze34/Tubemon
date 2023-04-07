from typing import Any
from pygame import Color
from random import randint, shuffle
# Attack Types
NORMAL = 'Normal'
FIRE   = 'Fire'
WATER  = 'Water'
NATURE = 'Nature'

FONT_COLOR : dict[str, Color] = {
    NORMAL : 'black',
    FIRE   : 'red',
    WATER  : 'blue',
    NATURE : 'green',
}

# ATTACK MOVES
# NORMAL TYPE
TACKLE : dict[str, Any] = {
    'name'   : 'Tackle',
    'damage' : 10,
    'type'   : NORMAL
}
POUND : dict[str, Any] = {
    'name'   : 'Pound',
    'damage' : 15,
    'type'   : NORMAL
}
SCRATCH : dict[str, Any] = {
    'name'   : 'Scratch',
    'damage' : 15,
    'type'   : NORMAL
}
# FIRE TYPE
FIREBALL : dict[str, Any] = {
    'name'   : 'Fireball',
    'damage' : 25,
    'type'   : FIRE
}
# WATER TYPE
WATERGUN : dict[str, Any] = {
    'name'   : 'Watergun',
    'damage' : 25,
    'type'   : WATER
}
# GRASS TYPE
PEDALBLADE : dict[str, Any] = {
    'name'   : 'Pedal Blade',
    'damage' : 25,
    'type'   : NATURE
}

all_attacks = [TACKLE, POUND, SCRATCH, FIREBALL, WATERGUN, PEDALBLADE]

def int_to_attack(attack_index : int) -> dict[str, Any]:
    return all_attacks[attack_index]

def attack_to_int(attack_name : str) -> int:
    for index, attack in enumerate(all_attacks):
        if attack['name'] == attack_name:
            return index
    return -1

# functions
def random_attacks(attacks_num : int = randint(1, 4)) -> list[dict[str, Any]]:
    all_attacks_copy = all_attacks.copy()
    attacks = list()
    # dont allow duplicates
    for _ in range(attacks_num):
        shuffle(all_attacks_copy)
        attacks.append(all_attacks_copy.pop())
    return attacks










