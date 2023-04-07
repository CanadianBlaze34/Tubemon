from ITEMS.item import Item
from monster import Monster
from player import Player

class Potion(Item):

    def __init__(self) -> None:
        super().__init__('Assets/Assets/Items/Potion.png')
        self.heal = 20

    def activate(self, **kwargs) -> None:
        """Heals the kwargs['target'] by 20.\n
         Subtracts 1 potion from the kwargs['player'] bag."""
        player : Player = kwargs['player']
        target : Monster = kwargs['target']
        health_to_add = min(self.heal,  target.max_health - target.health)
        #print(f'Player used a potion on {target.name()}. {target.name()} healed for {health_to_add} health.')
        target.health += health_to_add
        player.remove_items(Item.POTION, 1)
        