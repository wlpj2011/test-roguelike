#! /usr/bin/env python3
import tcod
from actions import EscapeAction, MovementAction
from entity import Entity
from engine import Engine
from procgen import generate_dungeon
from input_handlers import EventHandler


def main() -> None:
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 45

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    tileset = tcod.tileset.load_tilesheet("dejavu10x10_gs_tc.png",
                                          32, 8, tcod.tileset.CHARMAP_TCOD)

    event_handler = EventHandler()

    player = Entity(screen_width//2, screen_height//2, "@", (255,255,255))
    npc = Entity(screen_width//2 - 5, screen_height//2 , "@", (255,255,0))
    entities = {npc, player}

    game_map = generate_dungeon(max_rooms,room_min_size,room_max_size,map_width,map_height,player)

    engine = Engine(entities = entities, event_handler = event_handler, game_map = game_map, player = player)

    with tcod.context.new_terminal(screen_width,
                                   screen_height,
                                   tileset=tileset,
                                   title = "Test Roguelike",
                                   vsync = True) as context:
        root_console = tcod.Console(screen_width, screen_height, order = "F")
        while True:
            engine.render(console=root_console, context = context)
            events = tcod.event.wait()
            engine.handle_events(events)

if __name__=="__main__":
    main()
