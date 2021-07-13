from __future__ import annotations
from typing import TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import MainGameEventHandler
from render_functions import render_bar,render_names_at_mouse_location
from message_log import MessageLog

if TYPE_CHECKING:
    from game_map import GameMap
    from entity import Actor
    from input_handlers import EventHandler

class Engine:
    game_map: GameMap

    def __init__(self, player: Actor ):
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.message_log = MessageLog()
        self.player = player
        self.mouse_location = (0,0)

    def handle_enemy_turn(self)->None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                entity.ai.perform()

    def update_fov(self)-> None:
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x,self.player.y),
            radius = 8,)

        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console)->None:
        self.game_map.render(console)
        render_bar(console = console,
            current_value = self.player.fighter.hp,
            maximum_value = self.player.fighter.max_hp,
            total_width = 20
        )
        render_names_at_mouse_location(console=console, x=21, y=44, engine = self)
        self.message_log.render(console = console, x=21, y=45, width = 40, height = 5)
