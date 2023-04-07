from ITEMS.item import Item
from player import Player
from monster import Monster

class Tubebox(Item):

    def __init__(self) -> None:
        super().__init__('Assets/Assets/Items/Tubebox.png')

    def activate(self, **kwargs) -> None:
        """Captures the kwargs['target'] and adds it to the kwargs['player'] Tubemon list.\n
        Subtracts 1 tubebox from the kwargs['player'] bag"""
        player : Player = kwargs['player']
        target : Monster = kwargs['target']
        player.add_tubemon(target)
        #print(f'Player used a Tubebox.')
        #print(f'Player caught a wild {target.name()}.')
        #player.bag[Item.TUBEBOX] -= 1
        player.remove_items(Item.TUBEBOX, 1)
