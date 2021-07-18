from __future__ import annotations

from typing import Dict,Tuple, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item

class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: Dict[str,List[int,Item]] = dict()

    def drop(self, item: Item) -> None:
        """
        Removes an item from the inventory and restores it to the game map, at the player's current location.
        """
        if item.name in self.items:
            self.items[item.name][0] -= 1
        if self.items[item.name][0] == 0:
            self.items.pop(item.name)
        item.place(self.parent.x,self.parent.y,self.game_map)
        self.engine.message_log.add_message(f"You dropped the {item.name}.")
