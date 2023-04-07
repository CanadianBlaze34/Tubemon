from __future__ import annotations
from pygame import Surface

class Item:

    ITEM : dict[str, Item] = None

    # IDs
    POTION = 'Potion'
    TUBEBOX = 'Tubebox'

    POTION_ID = 0
    TUBEBOX_ID = 1

    def __init__(self, image : Surface) -> None:
        self.image = image

    def activate(self, **kwargs) -> None:
        print(f'Using Item.')
    
    @staticmethod
    def to_id(name : str) -> int:
        if name == Item.POTION  : return Item.POTION_ID 
        if name == Item.TUBEBOX : return Item.TUBEBOX_ID 
        raise NameError
    
    @staticmethod
    def to_name(id : str) -> str:
        if id == Item.POTION_ID  : return Item.POTION 
        if id == Item.TUBEBOX_ID : return Item.TUBEBOX
        raise IndexError