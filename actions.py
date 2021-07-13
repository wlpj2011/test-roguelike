from __future__ import annotations

from typing import Optional,Tuple,TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor,Entity


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

class EscapeAction(Action):
    def perform(self)->None:
        raise SystemExit()

class WaitAction(Action):
    def perform(self)->None:
        pass

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
        if not target:
            return

        damage = self.entity.fighter.power - target.fighter.defense
        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if damage > 0:
            print(f"{attack_desc} for {damage} hit points.")
            target.fighter.hp -= damage
        else:
            print(f"{attack_desc} but does no damage")

class MovementAction(ActionWithDirection):
    def perform(self)->None:
        dest_x, dest_y = self.dest_xy
        if not self.engine.game_map.in_bounds(dest_x,dest_y):
            return #Destination not in bounds
        if not self.engine.game_map.tiles["walkable"][dest_x,dest_y]:
            return #Destination is blocked
        if self.engine.game_map.get_blocking_entity_at_location(dest_x,dest_y):
            return

        self.entity.move(self.dx,self.dy)

class BumpAction(ActionWithDirection):
    def perform(self)->None:
        if self.target_actor:
            MeleeAction(self.entity,self.dx,self.dy).perform()
        else:
            MovementAction(self.entity,self.dx,self.dy).perform()
