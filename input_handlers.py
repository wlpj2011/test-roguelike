from __future__ import annotations

from typing import Callable, Optional,Tuple, TYPE_CHECKING, Union
import os

import tcod.event

from actions import (
    Action,
    BumpAction,
    WaitAction,
    PickupAction,
    DropItem,
    TakeUpStairsAction,
    TakeDownStairsAction,
    EquipAction
    ## TODO: convert all to action.Action
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    tcod.event.K_UP: (0,-1),
    tcod.event.K_DOWN: (0,1),
    tcod.event.K_RIGHT: (1,0),
    tcod.event.K_LEFT: (-1,0),
    tcod.event.K_HOME: (-1,-1),
    tcod.event.K_END: (-1,1),
    tcod.event.K_PAGEUP: (1,-1),
    tcod.event.K_PAGEDOWN: (1,1),
    tcod.event.K_KP_1: (-1,1),
    tcod.event.K_KP_2: (0,1),
    tcod.event.K_KP_3: (1,1),
    tcod.event.K_KP_4: (-1,0),
    tcod.event.K_KP_6: (1,0),
    tcod.event.K_KP_7: (-1,-1),
    tcod.event.K_KP_8: (0,-1),
    tcod.event.K_KP_9: (1,-1),
    tcod.event.K_h: (-1,0),
    tcod.event.K_j: (0,1),
    tcod.event.K_k: (0,-1),
    tcod.event.K_l: (1,0),
    tcod.event.K_y: (-1,-1),
    tcod.event.K_u: (1,-1),
    tcod.event.K_b: (-1,1),
    tcod.event.K_n: (1,1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}

ActionOrHandler = Union[Action,"BaseEventHandler"]
"""An event handler return value which can trigger an action or switch active handlers.
If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""

class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event:tcod.event.Event)->BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state,BaseEventHandler):
            return state
        assert not isinstance(state,Action), f"{self!r} can not handle actions"
        return self

    def on_render(self, console: tcod.Console)->None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit)->Optional[Action]:
        raise SystemExit()

class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console)->None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width//2,
            console.height//2,
            self.text,
            fg = color.white,
            bg = color.black,
            alignment = tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown)->Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent

class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event)->BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)
        return self

    def handle_action(self,action: Optional[Action])->bool:
        """Handle actions returned from event methods.
        Returns True if the action will advance a turn."""
        if action is None:
            return False

        self.engine.action_queue.schedule_action(action,action.delay)
        delay = action.delay
        self.engine.handle_enemy_turns()

        while self.engine.action_queue.next_actor() is not self.engine.player:
            action = self.engine.action_queue.next_action()
            if not action.can_perform():
                print(False)
            else:
                action.perform()
            #else:
                ## TODO: make AI pick new action and insert into action_queue with reduced delay.

        try:
            self.engine.action_queue.next_action().perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0],color.impossible)
            return False

        self.engine.update_fov()
        self.engine.game_turn += delay
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion)->None:
        if self.engine.game_map.in_bounds(event.tile.x,event.tile.y):
            self.engine.mouse_location = event.tile.x,event.tile.y

    def on_render(self,console: tcod.Console) -> None:
        self.engine.render(console)

class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self,event: tcod.event.KeyDown)->Optional[ActionOrHandler]:
        if event.sym in {
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self,event: tcod.event.MouseButtonDown)->Optional[ActionOrHandler]:
        return self.on_exit()

    def on_exit(self)->Optional[ActionOrHandler]:
        return MainGameEventHandler(self.engine)

class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console)->None:
        super().on_render(console)
        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0
        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x = x,
            y = y,
            width = width,
            height = 9,
            title = self.TITLE,
            clear = True,
            fg = (255,255,255),
            bg = (0,0,0),
        )

        console.print(
            x = x + 1, y = y + 1, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x = x + 1, y = y + 2, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x = x + 1, y = y + 3, string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}"
        )
        console.print(
            x=x + 1, y=y + 4, string=f"Strength: {self.engine.player.fighter.base_strength}"
        )
        console.print(
            x=x + 1, y=y + 5, string=f"Dexterity: {self.engine.player.fighter.base_dexterity}"
        )
        console.print(
            x=x + 1, y=y + 6, string=f"Constitution: {self.engine.player.fighter.base_constitution}"
        )
        console.print(
            x=x + 1, y=y + 7, string=f"Intelligence: {self.engine.player.fighter.base_intelligence}"
        )

class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        if self.engine.player.x <= 30:
            x = 35
        else:
            x = 0
        console.draw_frame(
            x = x,
            y = 0,
            width = 50,
            height = 10,
            title = self.TITLE,
            clear = True,
            fg = (255,255,255),
            bg = (0,0,0),
        )

        console.print(x = x + 1, y = 1, string = "Congratulations! You level up.")
        console.print(x = x + 1, y = 2, string = "Select an attribute to increase.")

        console.print(
            x = x + 1,
            y = 4,
            string = f"a) Constitution (+1 Constitution, from {self.engine.player.fighter.base_constitution})",
        )
        console.print(
            x = x + 1,
            y = 5,
            string = f"b) Strength (+1 Strength, from {self.engine.player.fighter.base_strength})",
        )
        console.print(
            x = x + 1,
            y = 6,
            string = f"c) Dexterity (+1 Dexterity, from {self.engine.player.fighter.base_dexterity})",
        )
        console.print(
            x = x + 1,
            y = 7,
            string = f"d) Intelligence (+1 Dexterity, from {self.engine.player.fighter.base_intelligence})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown)->Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0<= index <= 3:
            if index == 0:
                player.level.increase_constitution()
            elif index == 1:
                player.level.increase_strength()
            elif index == 2:
                player.level.increase_agility()
            else:
                player.level.increase_intelligence()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown)->Optional[ActionOrHandler]:
        """Don't allow the player to click to exit the menu, like normal."""
        return None

class InventoryEventHandler(AskUserEventHandler):
    TITLE = "<Missing Title>"

    def on_render(self, console: tcod.Console)-> None:
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2
        if height <= 3:
            height = 3
        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0
        y = 0
        width = len(self.TITLE) + 4

        console.draw_frame(
            x = x,
            y = y,
            width = width,
            height = height,
            title = self.TITLE,
            clear = True,
            fg = (255,255,255),
            bg = (0,0,0),
        )

        if number_of_items_in_inventory > 0:
            inventory = self.engine.player.inventory.items
            for i,item_name in enumerate(self.engine.player.inventory.item_names):
                item_key = chr(ord("a")+i)
                for item in self.engine.player.inventory.items:
                    if item.name == item_name:
                        selected_item = item
                        pass
                is_equipped = self.engine.player.equipment.item_is_equipped(selected_item)
                item_string = f"({item_key}) {self.engine.player.inventory.item_num(item_name)}x {item_name}"

                if is_equipped:
                    item_string = f"{item_string} (E)"

                console.print(x+1, y+i+1,item_string)
        else:
            console.print(x+1,y+1,"(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown)->Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a
        if 0<=index<=26:
            try:
                selected_item_name = player.inventory.item_names[index]
                for item in player.inventory.items:
                    if item.name == selected_item_name:
                        selected_item = item
                        pass
            except IndexError:
                self.engine.message_log.add_message("Invalid Entry.",color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item:Item)->Optional[ActionOrHandler]:
        raise NotImplementedError

class InventoryActivateHandler(InventoryEventHandler):
    TITLE = "Select an item to use"
    def on_item_selected(self,item: Item)->Optional[ActionOrHandler]:
        if item.consumable:
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return EquipAction(self.engine.player, item)
        else:
            return None

class InventoryDropHandler(InventoryEventHandler):
    TITLE = "Select an item to drop"
    def on_item_selected(self,item:Item)->Optional[ActionOrHandler]:
        return DropItem(self.engine.player,item)

class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self,engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self,console: tcod.Console)->None:
        super().on_render(console)
        x,y = self.engine.mouse_location
        console.tiles_rgb["bg"][x,y] = color.white
        console.tiles_rgb["fg"][x,y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown)->Optional[ActionOrHandler]:
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1
            if event.mod &( tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_LCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_LALT):
                modifier *= 20
            x,y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x+= dx*modifier
            y+= dy*modifier
            x = max(0,min(x,self.engine.game_map.width -1))
            y = max(0,min(y,self.engine.game_map.height -1))
            self.engine.mouse_location = x,y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown)->Optional[ActionOrHandler]:
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button==1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self,x: int, y:int)->Optional[ActionOrHandler]:
        raise NotImplementedError()

class LookHandler(SelectIndexHandler):
    def on_index_selected(self,x: int, y:int)->MainGameEventHandler:
        return MainGameEventHandler(self.engine)

class SingleRangedAttackHandler(SelectIndexHandler):
    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int,int]],Optional[Action]],
    ):
        super().__init__(engine)
        self.callback = callback

    def on_index_selected(self, x: int, y: int)->Optional[Action]:
        return self.callback((x,y))

class AreaRangedAttackHandler(SelectIndexHandler):
    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int,int]],Optional[Action]],
    ):
        super().__init__(engine)
        self.radius = radius
        self.callback = callback

    def on_render(self,console: tcod.Console):
        super().on_render(console)
        x,y = self.engine.mouse_location
        console.draw_frame(
            x = x - self.radius - 1,
            y = y - self.radius - 1,
            width = self.radius ** 2,
            height = self.radius ** 2,
            fg = color.red,
            clear = False
        )

    def on_index_selected(self, x: int, y: int)->Optional[Action]:
        return self.callback((x,y))

class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & (tcod.event.K_LSHIFT | tcod.event.K_RSHIFT):
            return TakeDownStairsAction(player)
        if key == tcod.event.K_COMMA and modifier & (tcod.event.K_LSHIFT | tcod.event.K_RSHIFT):
            return TakeUpStairsAction(player)

        if key in MOVE_KEYS:
            dx,dy = MOVE_KEYS[key]
            action = BumpAction(player,dx,dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        elif key == tcod.event.K_COMMA:
            action = PickupAction(player)
        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)


        return action

class GameOverEventHandler(EventHandler):
    def on_quit(self)->None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")
        raise exceptions.QuitWithoutSaving()

    def ev_quit(self, event: tcod.event.Quit)->None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        key = event.sym
        if key == tcod.event.K_ESCAPE:
            self.on_quit()
        elif key == tcod.event.K_v:
            self.engine.event_handler = HistoryViewer(self.engine)

class HistoryViewer(EventHandler):
    def __init__(self,engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console)->None:
        super().on_render(console)
        log_console = tcod.Console(console.width - 6, console.height - 6)

        log_console.draw_frame(0,0,log_console.width, log_console.height)
        log_console.print_box(0,0,log_console.width,1,"┤Message history├", alignment=tcod.CENTER)

        self.engine.message_log.render_messages(
            console = log_console,
            x = 1,
            y = 1,
            width = log_console.width - 2,
            height = log_console.height - 2,
            messages = self.engine.message_log.messages[:self.cursor+1]
        )
        log_console.blit(console,3,3)

    def ev_keydown(self, event: tcod.event.KeyDown)->Optional[MainGameEventHandler]:
        key = event.sym
        if key in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[key]
            if adjust < 0 and self.cursor == 0:
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                self.cursor = 0
            else:
                self.cursor = max(0,min(self.cursor + adjust, self.log_length - 1))
        elif key == tcod.event.K_HOME:
            self.cursor = 0
        elif key == tcod.event.K_END:
            self.cursor = self.log_length - 1
        else:
            return MainGameEventHandler(self.engine)
        return None
