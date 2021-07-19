from __future__ import annotations

from typing import TYPE_CHECKING

import random

from components.base_component import BaseComponent
from render_order import RenderOrder
import color

if TYPE_CHECKING:
    from entity import Actor

class Fighter(BaseComponent):
    parent: Actor

    def __init__(
        self,
        hit_dice_num: int,
        hit_dice_size: int,
        base_strength: int,
        base_dexterity: int,
        base_constitution: int,
        base_intelligence: int,
        damage_die_size: int,
        damage_die_number: int,
        resistance: int = 0,
    ):
        self.max_hp = 0
        self.hit_dice_num = hit_dice_num
        self.hit_dice_size = hit_dice_size
        self.base_strength = base_strength
        self.base_dexterity = base_dexterity
        self.base_constitution = base_constitution
        self.base_intelligence = base_intelligence
        self.damage_die_size = damage_die_size
        self.damage_die_number = damage_die_number
        self.resistance = resistance

    @property
    def strength_mod(self)->int:
        return (self.base_strength - 10)//2

    @property
    def dexterity_mod(self)->int:
        return (self.base_dexterity - 10)//2

    @property
    def constitution_mod(self)->int:
        return (self.base_constitution - 10)//2

    @property
    def intelligence_mod(self)->int:
        return (self.base_intelligence - 10)//2

    @property
    def hp(self)->int:
        if not hasattr(self,"_hp"):
            return 0
        return self._hp

    @hp.setter
    def hp(self,value: int)-> None:
        self._hp = max(0,min(value,self.max_hp))
        print(self._hp)
        if self._hp == 0 and self.parent.ai and self.max_hp != 0:
            self.die()

    def set_max_hp(self)->None:
        if hasattr(self,"hp"):
            pass
        else:
            self._hp = self.max_hp

        old_max_hp = self.max_hp

        self.max_hp = max(1,self.hit_dice_size + self.constitution_mod)
        if self.hit_dice_num > 1:
            for i in range(0,self.hit_dice_num-1):
                self.max_hp += max(1,random.randint(1,self.hit_dice_size) + self.constitution_mod)
        if self.hp == 0 :
            self._hp = self.max_hp
        elif old_max_hp != 0:
            self.heal(self.max_hp - old_max_hp)
        print(self.hp)


    @property
    def defense(self)->int:
        return 10 + self.dexterity_mod + self.defense_bonus

    @property
    def damage_mod(self)->int:
        return self.strength_mod + self.power_bonus

    @property
    def defense_bonus(self)->int:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def power_bonus(self)->int:
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return 0

    def heal(self, amount: int)->int:
        if self.hp==self.max_hp:
            return 0
        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp
        amount_recovered = new_hp_value - self.hp
        self.hp = new_hp_value
        return amount_recovered

    def take_damage(self,amount: int)->None:
        self.hp -= amount

    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_color = color.player_die
        else:
            death_message = f"{self.parent.name} is dead"
            death_message_color = color.enemy_die


        self.parent.char = "%"
        self.parent.color = (191,0,0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"The remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE

        self.engine.message_log.add_message(death_message,death_message_color)
        self.engine.player.level.add_xp(self.parent.level.xp_given)
