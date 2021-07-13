from __future__ import annotations
import copy
from typing import Optional,Tuple,TypeVar,TYPE_CHECKING

if TYPE_CHECKING:
    from game_map import GameMap

T = TypeVar("T",bound="Entity")

class Entity:
    """
    A generic object to represent players, enemies, items, etc...
    """

    game_map: GameMap

    def __init__(
        self,
        game_map: Optional[GameMap] = None,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255,255,255),
        name: str = "<Unnamed>",
        blocks_movement: bool = False,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        if game_map:
            self.game_map = game_map
            game_map.entities.add(self)

    def spawn(self: T, game_map: GameMap, x: int, y: int)->T:
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.game_map = game_map
        game_map.entities.add(clone)
        return clone

    def place(self, x: int, y: int, game_map: Optional[GameMap] = None):
        self.x = x
        self.y = y
        if game_map:
            if hasattr(self,"game_map"):
                self.game_map.entities.remove(self)
            self.game_map = game_map
            game_map.entities.add(self)

    def move(self, dx: int, dy: int) -> None:
        #Move the entity by a given amount
        self.x += dx
        self.y += dy
