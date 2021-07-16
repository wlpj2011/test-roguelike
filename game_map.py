from __future__ import annotations

from typing import Iterable, Iterator, Optional,TYPE_CHECKING

import numpy as np
from tcod.console import Console

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

from entity import Actor, Item
import tile_types

class GameWorld:
    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 1,
        max_floor: int = 0,
        game_levels: List[GameMap] = []
    ):
        self.engine = engine
        self.map_width = map_width
        self.map_height = map_height
        self.max_rooms = max_rooms
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size
        self.current_floor = current_floor
        self.max_floor = max_floor
        self.game_levels = game_levels

    def generate_floor(self)->None:
        from procgen import generate_dungeon

        self.max_floor += 1

        self.engine.game_map = generate_dungeon(
            max_rooms = self.max_rooms,
            room_min_size = self.room_min_size,
            room_max_size = self.room_max_size,
            map_width = self.map_width,
            map_height = self.map_height,
            engine = self.engine
        )
        self.max_floor = self.game_levels.append(self.engine.game_map)

class GameMap:
    def __init__(self, engine: Engine, width:int, height:int, entities: Iterable[Entity] = ()):
        self.engine = engine
        self.width = width
        self.height = height
        self.entities = set(entities)

        self.tiles = np.full((width,height),fill_value = tile_types.wall, order = "F")
        self.visible = np.full((width,height),fill_value = False, order = "F")
        self.explored = np.full((width,height),fill_value = False, order = "F")

        self.downstairs_location = (0,0)
        self.upstairs_location = (0,0)

    @property
    def game_map(self):
        return self

    @property
    def actors(self)->Iterator[Actor]:
        yield from(
            entity for entity in self.entities
            if isinstance(entity,Actor) and entity.is_alive
        )

    @property
    def items(self)->Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity,Item))

    def get_blocking_entity_at_location(self, location_x: int, location_y: int)->Optional[Entity]:
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity
        return None

    def get_actor_at_location(self,x: int, y: int)->Optional[Actor]:
        for actor in self.actors:
            if actor.x==x and actor.y == y:
                return actor
        return None

    def in_bounds(self,x:int,y:int)->bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self,console: Console)->None:
        console.tiles_rgb[0:self.width, 0:self.height] = np.select(
            condlist = [self.visible,self.explored],
            choicelist=[self.tiles["light"],self.tiles["dark"]],
            default = tile_types.SHROUD
        )
        entities_sorted_for_rendering = sorted(self.entities, key=lambda x: x.render_order.value)
        for entity in entities_sorted_for_rendering:
            if self.visible[entity.x,entity.y]:
                console.print(
                    entity.x, entity.y, entity.char, entity.color
                )
