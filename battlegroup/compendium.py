import re

from data_backend import load, can_load
from battlegroup.npc import *

DEFAULT_COUNTERS = {"lockon": 0, "greywash": 0}

class Compendium:

    def __init__(self, p_message_queue: list, p_error_queue: list) -> None:
        self.message_queue = p_message_queue
        self.error_queue = p_error_queue
        
        self.capitalships = {}
        self.escorts = {}
    
    def load_compendium(self, name: str) -> list:
        path = "battlegroup/" + name
        res = []
        if can_load(path):
            lib: dict[str, list[dict]] = load(path)
            for capitalship in lib.get("npc-capital", []):
                if "name" in capitalship:
                    self.capitalships[capitalship["name"].lower()] = capitalship
            for escort in lib.get("npc-escorts", []):
                if "name" in escort:
                    self.escorts[escort["name"].lower()] = escort
            res.append(lib["__meta__"])
            self.message_queue.append("Added compendium: " + path)
        else:
            self.message_queue.append("No such compendium: " + path)
        return res
    
    def get_stats_wings(self, wings: list) -> Obj:
        if not isinstance(wings, list):
            wings = [wings]
        wing_objs = {}
        for i, w in enumerate(wings):
            wing_objs[f"{KEY_PREFIX}w{i+1}"] = {
                "_name": w.get("name", "UNNAMED"),
                "_range": w.get("range", "0-0"),
                "_tenacity": w.get("tenacity", 0),
                KEY_PREFIX: [{"hp": x, **DEFAULT_COUNTERS} for x in w["hp"]]
            }
        return wing_objs
    
    def get_stats_abilities(self, abilities: list[Obj], parent: str, page: int) -> list[Obj]:
        res = []
        for ability in abilities:
            range_str = ability.get("range", "5-0")
            if re.match(r'\d-\d', range_str) is None: range_str = "5-0"
            rmax, rmin = map(int, range_str.split("-"))
            rmax, rmin = max(rmax, rmin), min(rmax, rmin)
            if "name" not in ability:
                self.error_queue.append(f"No key 'name' in ability from {parent}")
                continue
            if ability.get("type", "INVALID").lower() not in ["charge", "trait", "system", "maneuver", "tactic"]:
                self.error_queue.append(f"No key 'type' in ability from {parent} or value invalid (must be either 'Charge', 'Trait', 'System', 'Maneuver' or 'Tactic')")
                continue
            reformated = {
                "min": rmin,
                "max": rmax,
                "name": ability["name"].lower(),
                "type": ability["type"].lower(),
                "effect": ability.get("effect", ""),
                "description": ability.get("description", ""),
                "reloading": ability.get("reloading", -1),
                "tags": ability.get("tags", []),            # TODO: reformating + validating input
                "page": page,
            }
            if reformated["type"] == "charge" and "charge" not in ability:
                self.error_queue.append(f"Charge weapon in {parent} does not have 'charge' key (or value is not a positive integer)")
            if reformated["type"] in ["charge", "maneuver"]:
                reformated["dammage"] = ability.get("dammage", 0)       # TODO: validating input
                reformated["size"] = ability.get("size", "Superheavy")  # TODO: validating input
                reformated["target"] = ability.get("target", "Single")  # TODO: validating input
                reformated["charge"] = ability.get("charge", -1)
            res.append(reformated)
        return res
    
    def get_stats_charge_weapons(self, abilites: list[Obj]) -> Obj:
        charge_objs = {}
        i = 1
        for ability in abilites:
            if ability["type"] != "charge":
                continue
            c = ability["charge"]
            if c < 0:
                continue
            charge_objs[f"{KEY_PREFIX}c{i}"] = {
                "_name": ability.get("name", "UNNAMED ABILITY"),
                KEY_PREFIX: {
                    "total": c,
                    "current": c
                }
            }
            i += 1
        return charge_objs

    def get_stats_capitalship(self, name: str) -> Obj:
        comp = self.capitalships.get(name.lower(), {})
        abilities = self.get_stats_abilities(comp.get("abilities", []), name, comp.get("page", -1))
        wing_objs = self.get_stats_wings(comp.get("wings", []))
        charge_objs = self.get_stats_charge_weapons(abilities)
        return {
            "_name": name.lower(),
            "_defense": comp.get("defense", 5),
            "_interdiction": comp.get("interdiction", "1d6"),
            "_valid": name.lower() in self.capitalships,
            "_hp0": comp.get("hp", 1),
            "_abilities": abilities,
            KEY_PREFIX: {
                "hp": comp.get("hp", 1),
                "max_hp": comp.get("hp", 1),
                **comp.get("counters", {}),
                **DEFAULT_COUNTERS
            },
            **wing_objs,
            **charge_objs,
        }
    
    def get_stats_escort(self, name: str) -> Obj:
        comp = self.escorts.get(name.lower(), {})
        abilities = self.get_stats_abilities(comp.get("abilities", []), name, comp.get("page", -1))
        wing_objs = self.get_stats_wings(comp.get("wings", []))
        charge_objs = self.get_stats_charge_weapons(abilities)
        tags = [x.lower() for x in comp.get("tags", [])]
        return {
            "_name": name.lower(),
            "_defense": comp.get("defense", 5),
            "+defense": comp.get("+defense", 0),
            "+interdiction": comp.get("+interdiction", ""),
            "+hp": comp.get("+hp", 0),
            "_is_template": "template" in tags,
            "_is_unique": "unique" in tags,
            "_abilities": abilities,
            "_valid": name.lower() in self.escorts,
            KEY_PREFIX: [{
                "hp": x,
                **comp.get("counters", {}),
                **DEFAULT_COUNTERS,
            } for x in comp.get("hp", [])],
            **wing_objs,
            **charge_objs,
        }
