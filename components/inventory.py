from __future__ import annotations

from typing import Dict,List,Tuple, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item

class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[Item] = list()

    def drop(self, item: Item) -> None:
        """
        Removes an item from the inventory and restores it to the game map, at the player's current location.
        """
        self.items.remove(item)
        item.place(self.parent.x,self.parent.y,self.game_map)
        self.engine.message_log.add_message(f"You dropped the {item.name}.")

    @property
    def current_size(self):
        return len(self.item_names)

    @property
    def item_names(self):
        names = []
        for item in self.items:
            if item.name not in names:
                names.append(item.name)
        return names

    def item_num(self, name: str):
        number = 0
        for item in self.items:
            if item.name == name:
                number += 1
        return number
