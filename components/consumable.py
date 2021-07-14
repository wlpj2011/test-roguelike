from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import actions
import color
from components.base_component import BaseComponent
import components.inventory
from exceptions import Impossible

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):
    parent: Item

    def get_action(self,consumer: Actor)->Optional[actions.Action]:
        return actions.ItemAction(consumer,self.parent)

    def activate(self, action: actions.ItemAction)->None:
        raise NotImplementedError()

    def consume(self)->None:
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):
            inventory.items.remove(entity)


class HealingConsumable(Consumable):
    def __init__(self, amount: int):
        self.amount = amount

    def activate(self, action: actions.ItemAction)->None:
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You consume the {self.parent.name} and recover {amount_recovered} health.",
                color.health_recovered
            )
            self.consume()
        else:
            raise Impossible("Your health is already full.")
