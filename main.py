from dataclasses import dataclass
from math import sqrt
from sys import stderr

# - - - - - - DICTS - - - - - -

STRUCTURE_TYPES = {
    -1: None,
    2: "BARRACKS",
}

OWNER_TYPES = {
    -1: None,
    0: "PLAYER",
    1: "ENEMY",
}

UNIT_TYPES = {
    -1: "QUEEN",
    0: "KNIGHT",
    1: "ARCHER",
}

UNIT_COSTS = {
    "KNIGHT": 80,
    "ARCHER": 100,
}


# - - - - - - CLASSES - - - - - -


@dataclass
class Structure:
    owner: str


@dataclass
class Barrack(Structure):
    army_type: str
    cooldown: int


@dataclass
class Site:
    id: int
    x: int
    y: int
    radius: int
    structure: Structure
    owner: str = None


@dataclass
class Unit:
    x: int
    y: int
    owner: str
    type: str
    hp: int


# - - - - - - GLOBALS - - - - - -

ROUND = 0
SITES = {}
GOLD = 100
TOUCHED_SITE = None
UNITS = []


# - - - - - - LOGS - - - - - -


def log(message):
    print(message, file=stderr, flush=True)


def log_sites():
    log("\n - SITES:")
    for site in SITES:
        log(
            f"      {SITES[site].id} {SITES[site].x} {SITES[site].y} {SITES[site].radius} {SITES[site].owner}"
        )
        if SITES[site].structure is not None:
            log(f"              {SITES[site].structure}")


def log_units():
    log("\n - UNITS:")
    for unit in UNITS:
        log(f"      {unit}")


def log_round():
    log(f"\n\n - - - - - ROUND {ROUND} - - - - - \n\n")
    log(f" - GOLD: {GOLD}")
    log(f" - TOUCHED SITE: {TOUCHED_SITE}")
    log(f" - PLAYER QUEEN: {get_player_queen()}")
    log(f" - ENEMY QUEEN: {get_enemy_queen()}")
    log_sites()
    log_units()


# - - - - - - HELPER - - - - - -


def distance_between_two_circles(x1, y1, x2, y2, r1, r2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) - (r1 + r2)


def find_nearest_circle_from_list(circle_list):
    nearest_site = None
    nearest_distance = float("inf")
    for site in circle_list:
        distance = distance_between_two_circles(
            get_player_queen().x, get_player_queen().y, site.x, site.y, 30, site.radius
        )
        if distance < nearest_distance:
            nearest_site = site
            nearest_distance = distance
    return nearest_site


def find_nearest_circle_from_list_from_enemy(circle_list):
    nearest_site = None
    nearest_distance = float("inf")
    for site in circle_list:
        distance = distance_between_two_circles(
            get_enemy_queen().x, get_enemy_queen().y, site.x, site.y, 30, site.radius
        )
        if distance < nearest_distance:
            nearest_site = site
            nearest_distance = distance
    return nearest_site


def get_player_queen():
    for unit in UNITS:
        if unit.owner == "PLAYER" and unit.type == "QUEEN":
            return unit
    return None


def get_enemy_queen():
    for unit in UNITS:
        if unit.owner == "ENEMY" and unit.type == "QUEEN":
            return unit
    return None


def get_player_units():
    return [unit for unit in UNITS if unit.owner == "PLAYER"]


def get_player_sites():
    return [site for site in SITES.values() if site.structure.owner == "PLAYER"]


def get_empty_sites():
    return [site for site in SITES.values() if site.structure is None]


def find_nearest_empty_site():
    return find_nearest_circle_from_list(get_empty_sites())


def get_available_barracks():
    return [
        site
        for site in SITES.values()
        if site.structure is not None
        and type(site.structure) == Barrack
        and site.structure.owner == "PLAYER"
    ]


def find_nearest_available_barrack(army_type):
    return find_nearest_circle_from_list_from_enemy(
        [
            b
            for b in get_available_barracks()
            if b.structure.army_type == army_type and b.structure.cooldown == 0
        ]
    )


def is_unit_affordable(unit_type):
    return GOLD >= UNIT_COSTS[unit_type]


# - - - - - - GAME ACTIONS - - - - - -


def train_unit(site):
    global GOLD

    GOLD -= UNIT_COSTS[site.structure.army_type]

    return f"TRAIN {site.id}"


def move_toward_point(x2, y2, limit):
    x1 = get_player_queen().x
    y1 = get_player_queen().y
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) > limit:
        dx = limit * dx / abs(dx)
    if abs(dy) > limit:
        dy = limit * dy / abs(dy)
    return f"MOVE {int(x1+dx)} {int(y1+dy)}"


def build_structure(_id, structure_type, param):
    return f"BUILD {_id} {structure_type}-{param}"


# - - - - - - GAME LOGIC - - - - - -


def find_next_unit_to_train():
    player_units = get_player_units()
    knights = [unit for unit in player_units if unit.type == "KNIGHT"]
    archers = [unit for unit in player_units if unit.type == "ARCHER"]
    if len(knights) <= len(archers):
        return "KNIGHT"
    else:
        return "ARCHER"


def find_next_barrack_type_to_build():
    player_barracks = [
        s.structure
        for s in SITES.values()
        if type(s.structure) == Barrack and s.structure.owner == "PLAYER"
    ]
    knights = [b for b in player_barracks if b.army_type == "KNIGHT"]
    archers = [b for b in player_barracks if b.army_type == "ARCHER"]
    if len(knights) <= len(archers):
        return "KNIGHT"
    else:
        return "ARCHER"


def try_train_units():
    next_unit = find_next_unit_to_train()
    log(f" - next_unit {next_unit}")
    log(f" - is_unit_affordable {is_unit_affordable(next_unit)}")
    if next_unit is None:
        return None
    if not is_unit_affordable(next_unit):
        return None
    nearest_available_barrack = find_nearest_available_barrack(next_unit)
    log(f" - get_available_barracks() {get_available_barracks()}")
    log(f" - nearest_available_barrack {nearest_available_barrack}")
    if nearest_available_barrack is None:
        return None

    log(f" - TRYING TO TRAIN {next_unit} in {nearest_available_barrack}")
    return train_unit(nearest_available_barrack)


def try_build_barrack():
    nearest_empty_site = find_nearest_empty_site()
    if nearest_empty_site is None:
        return None
    if not is_unit_affordable("KNIGHT"):
        return None

    if not TOUCHED_SITE == nearest_empty_site.id:
        log(f" - MOVING TOWARD {nearest_empty_site.id}")
        return move_toward_point(nearest_empty_site.x, nearest_empty_site.y, 60)

    log(f" - TRYING TO BUILD BARRACK")
    return build_structure(
        nearest_empty_site.id, "BARRACKS", find_next_barrack_type_to_build()
    )


def get_next_action():
    train_action = try_train_units()
    queen_action = try_build_barrack()

    print(queen_action if queen_action is not None else "WAIT")
    print(train_action if train_action is not None else "TRAIN")


# - - - - - - GAME LOOP - - - - - -


def init():
    log(" - - - - - INIT - - - - - ")
    num_sites = int(input())
    for i in range(num_sites):
        site_id, x, y, radius = [int(j) for j in input().split()]
        SITES[site_id] = Site(site_id, x, y, radius, None)
    log_sites()


def game_loop():
    global ROUND, UNITS, SITES, GOLD, TOUCHED_SITE

    GOLD, TOUCHED_SITE = [int(i) for i in input().split()]
    if TOUCHED_SITE == -1:
        TOUCHED_SITE = None

    for i in range(len(SITES)):
        # ignore_1: used in future leagues
        # ignore_2: used in future leagues
        # structure_type: -1 = No structure, 2 = Barracks
        # owner: -1 = No structure, 0 = Friendly, 1 = Enemy
        site_id, ignore_1, ignore_2, structure_type, owner, param_1, param_2 = [
            int(j) for j in input().split()
        ]
        if structure_type == 2:
            SITES[site_id].structure = Barrack(
                OWNER_TYPES[owner], UNIT_TYPES[param_2], param_1
            )

    num_units = int(input())
    UNITS = []
    for i in range(num_units):
        # unit_type: -1 = QUEEN, 0 = KNIGHT, 1 = ARCHER
        x, y, owner, unit_type, health = [int(j) for j in input().split()]
        UNITS.append(Unit(x, y, OWNER_TYPES[owner], UNIT_TYPES[unit_type], health))

    log_round()

    get_next_action()

    ROUND += 1


init()
while True:
    game_loop()
