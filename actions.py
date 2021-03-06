from __future__ import annotations

from typing import Optional,Tuple,TYPE_CHECKING
import random

import color
import exceptions
import tile_types
if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item


class Action:
    def __init__(self, entity:Actor):
        super().__init__()
        self.entity = entity

    @property
    def engine(self)->Engine:
        return self.entity.game_map.engine

    def perform(self)->None:
         """Perform this action with the objects needed to determine its scope.
         'self.engine' is the scope this action is being performed in.
         'self.entity' is the object performing the action.
         This method must be overridden by Action subclasses.
         """
         raise NotImplementedError()

class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""
    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if inventory.current_size > inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full")
                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory

                inventory.items.append(item)

                self.engine.message_log.add_message(f"You picked up the {item.name}.")
                return
        raise exceptions.Impossible("There is nothing here to pick up.")

class ItemAction(Action):
    def __init__(self, entity: Actor, item: Item, target_xy: Optional[Tuple[int,int]] = None):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self)->Optional[Actor]:
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        if self.item.consumable:
            self.item.consumable.activate(self)

class DropItem(ItemAction):
    def perform(self)->None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)
        self.entity.inventory.drop(self.item)

class EquipAction(ItemAction):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity,item)
        self.item = item

    def perform(self)->None:
        self.entity.equipment.toggle_equip(self.item)

class WaitAction(Action):
    def perform(self)->None:
        if random.random()<0.2: #regen rate
            self.entity.fighter.heal(1)

class TakeDownStairsAction(Action):
    def perform(self)->None:
        """Take the stairs, if any exist at the entity's location."""
        if self.engine.game_map.tiles[(self.entity.x,self.entity.y)]==tile_types.down_stairs:
            self.engine.game_world.current_floor+=1
            if self.engine.game_world.current_floor-1 == self.engine.game_world.max_floor:
                self.engine.game_world.generate_floor()
            self.engine.game_map = self.engine.game_world.game_levels[self.engine.game_world.current_floor - 1]
            self.engine.player.place(*self.engine.game_map.upstairs_location,self.engine.game_map)
            self.engine.message_log.add_message(f"You descend the staircase and enter the {self.engine.game_world.current_floor} floor.", color.descend)
        else:
            raise exceptions.Impossible("There are no stairs here.")

class TakeUpStairsAction(Action):
    def perform(self)->None:
        """Take the stairs, if any exist at the entity's location."""
        if self.engine.game_map.tiles[(self.entity.x,self.entity.y)]==tile_types.up_stairs:
            self.engine.game_world.current_floor -=1
            self.engine.game_map = self.engine.game_world.game_levels[self.engine.game_world.current_floor - 1]
            self.engine.player.place(*self.engine.game_map.downstairs_location,self.engine.game_map)
            self.engine.message_log.add_message(f"You ascend the staircase and enter the {self.engine.game_world.current_floor} floor.", color.descend)
        else:
            raise exceptions.Impossible("There are no stairs here.")

class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)
        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self)->Tuple[int,int]:
        return self.entity.x + self.dx,self.entity.y + self.dy

    @property
    def blocking_entity(self)->Optional[Entity]:
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self)->Optional[Actor]:
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self)->None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self)->None:
        target = self.target_actor
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"

        if not target:
            raise exceptions.Impossible("Nothing to Attack")

        # TODO: Change this method, really don't like this, or maybe just needs balancing
        if random.randint(1,20) + self.entity.fighter.strength_mod >= target.fighter.defense:
            damage_die = self.entity.fighter.damage_die_size
            die_number = self.entity.fighter.damage_die_number
            if self.entity.equipment.weapon:
                damage_die = self.entity.equipment.weapon.equippable.damage_die_size
                die_number = self.entity.equipment.weapon.equippable.damage_die_number
            damage = 0
            for i in range(die_number):
                damage += random.randint(1,damage_die)

            damage = damage + self.entity.fighter.damage_mod - target.fighter.resistance

            if damage > 0:
                self.engine.message_log.add_message(f"{attack_desc} for {damage} hit points.",attack_color)
                target.fighter.hp -= damage
            else:
                self.engine.message_log.add_message(f"{attack_desc} but does no damage",attack_color)
        else:
            self.engine.message_log.add_message(f"{attack_desc} but misses.",attack_color)

class MovementAction(ActionWithDirection):
    def perform(self)->None:
        dest_x, dest_y = self.dest_xy
        if not self.engine.game_map.in_bounds(dest_x,dest_y):
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x,dest_y]:
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x,dest_y):
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx,self.dy)
        if random.random()<0.05: #regen rate
            self.entity.fighter.heal(1)

class BumpAction(ActionWithDirection):
    def perform(self)->None:
        if self.target_actor:
            MeleeAction(self.entity,self.dx,self.dy).perform()
        else:
            MovementAction(self.entity,self.dx,self.dy).perform()
