from __future__ import annotations
from typing import TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

import exceptions
import render_functions
import action_queue as action_q
import actions
from message_log import MessageLog

import lzma
import pickle

if TYPE_CHECKING:
    from game_map import GameMap,GameWorld
    from entity import Actor
    from action_queue import TimeSchedule

class Engine:
    game_map: GameMap
    game_world: GameWorld
    action_queue: TimeSchedule

    def __init__(self, player: Actor ):
        self.message_log = MessageLog()
        self.player = player
        self.mouse_location = (0,0)
        self.game_turn = 0.0
        self.action_queue = action_q.TimeSchedule()

    def handle_enemy_turns(self)->None:
        for entity in set(self.game_map.actors) - {self.player}:
            try:
                action = entity.ai.next_action()
                if isinstance(action, actions.Action):
                    self.action_queue.schedule_action(action, action.delay)
            except exceptions.Impossible:
                pass

    def update_fov(self)-> None:
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x,self.player.y),
            radius = 8,)

        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console)->None:
        self.game_map.render(console)
        render_functions.render_health_bar(console = console,
            current_value = self.player.fighter.hp,
            maximum_value = self.player.fighter.max_hp,
            total_width = 20
        )
        render_functions.render_dungeon_level(
            console = console,
            dungeon_level = self.game_world.current_floor,
            location=(0,47)
        )
        render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine = self)
        render_functions.render_turn(console = console, x= 0, y=48, engine = self)
        self.message_log.render(console = console, x=21, y=45, width = 40, height = 5)

    def save_as(self, filename:str)->None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)
