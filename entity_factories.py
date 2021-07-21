from components.ai import HostileEnemy
from components.fighter import Fighter
from components import consumable,equippable
from components.equipment import Equipment
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

player = Actor(
    char = "@",
    color = (255,255,255),
    name = "Player",
    ai_cls = HostileEnemy,
    equipment = Equipment(),
    fighter = Fighter(
        hit_dice_num = 1,
        hit_dice_size = 8,
        base_strength = 20,
        base_dexterity = 11,
        base_constitution = 11,
        base_intelligence = 11,
        damage_die_size = 2,
        damage_die_number = 1,
        resistance = 0,
    ),
    inventory = Inventory(capacity = 26),
    level = Level(level_up_base = 200),
)

goblin = Actor(
    char = "g",
    color = (63,127,63),
    name = "Goblin",
    ai_cls = HostileEnemy,
    equipment = Equipment(),
    fighter = Fighter(
        hit_dice_num = 1,
        hit_dice_size = 6,
        base_strength = 10,
        base_dexterity = 13,
        base_constitution = 9,
        base_intelligence = 8,
        damage_die_size = 1,
        damage_die_number = 1,
        resistance = 0,
    ),
    inventory = Inventory(capacity = 26),
    level = Level(xp_given = 20),
)

orc = Actor(
    char = "o",
    color = (63,127,63),
    name = "Orc",
    ai_cls = HostileEnemy,
    equipment = Equipment(),
    fighter = Fighter(
        hit_dice_num = 1,
        hit_dice_size = 8,
        base_strength = 12,
        base_dexterity = 10,
        base_constitution = 12,
        base_intelligence = 9,
        damage_die_size = 2,
        damage_die_number = 1,
        resistance = 0,
    ),
    inventory = Inventory(capacity = 26),
    level = Level(xp_given = 35),
)

troll = Actor(
    char = "T",
    color = (0,127,0),
    name = "Troll",
    ai_cls = HostileEnemy,
    equipment = Equipment(),
    fighter = Fighter(
        hit_dice_num = 2,
        hit_dice_size = 8,
        base_strength = 14,
        base_dexterity = 10,
        base_constitution = 14,
        base_intelligence = 8,
        damage_die_size = 4,
        damage_die_number = 1,
        resistance = 0,
    ),
    inventory = Inventory(capacity = 26),
    level = Level(xp_given = 100),
)


health_potion = Item(
    char = "!",
    color = (127,0,255),
    name = "Health Potion",
    consumable = consumable.HealingConsumable(amount = 4),
)


lightning_scroll = Item(
    char = "?",
    color = (255,255,0),
    name = "Lightning Scroll",
    consumable = consumable.LightningDamageConsumable(damage = 20, maximum_range = 5),
)

confusion_scroll = Item(
    char = "?",
    color = (207,63,255),
    name = "Confusion Scroll",
    consumable = consumable.ConfusionConsumable(number_of_turns = 10),
)

fireball_scroll = Item(
    char = "?",
    color = (255,0,0),
    name = "Fireball Scroll",
    consumable = consumable.FireballDamageConsumable(damage = 12, radius = 3),
)


dagger = Item(
    char = "/",
    color = (0,191,255),
    name = "Dagger",
    equippable = equippable.Dagger()
)

sword = Item(
    char = "/",
    color = (0,191,255),
    name = "Sword",
    equippable = equippable.Sword()
)


leather_armor = Item(
    char = "[",
    color = (139,69,19),
    name = "Leather Armor",
    equippable = equippable.LeatherArmor()
)

chain_mail = Item(
    char = "[",
    color = (139,69,19),
    name = "Chain Mail",
    equippable = equippable.ChainMail()
)
