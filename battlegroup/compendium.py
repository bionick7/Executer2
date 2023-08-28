import re

from data_backend import load, can_load
from battlegroup.npc import *

DEFAULT_COUNTERS = {"lockon": 0, "greywash": 0}

class Compendium:

    def __init__(self, p_message_queue: list, p_error_queue: list) -> None:
        self.message_queue = p_message_queue
        self.error_queue = p_error_queue
        
        self.capitalship_compendium = {}
        self.escorts_compendium = {}
    
    def load_compendium(self, name: str) -> list:
        path = "battlegroup/" + name
        res = []
        if can_load(path):
            lib: dict[str, list[dict]] = load(path)
            for capitalship in lib.get("npc-capital", []):
                self.capitalship_compendium[capitalship.get("name", "__UNNAMED__")] = capitalship
            for escort in lib.get("npc-escorts", []):
                self.escorts_compendium[escort.get("name", "__UNNAMED__")] = escort
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
    
    def get_stats_action(self, abilities: list[Obj], parent: str) -> list[Obj]:
        res = []
        for action in abilities:
            range_str = action.get("range", "5-0")
            if re.match(r'\d-\d', range_str) is None: range_str = "5-0"
            rmax, rmin = map(int, range_str.split("-"))
            rmax, rmin = max(rmax, rmin), min(rmax, rmin)
            if "name" not in action:
                self.error_queue.append(f"No key 'name' in action from {parent}")
                continue
            if action.get("type", "INVALID").lower() not in ["gun", "trait", "system", "maneuver", "tactic"]:
                self.error_queue.append(f"No key 'type' in action from {parent} or value invalid (must be either 'Gun', 'Trait', 'System', 'Maneuver' or 'Tactic'])")
                continue
            reformated = {
                "min": rmin,
                "max": rmax,
                "name": action["name"].lower(),
                "type": action["type"].lower(),
                "effect": action.get("effect", "No provided"),
                "description": action.get("description", "No provided"),
            }
            if reformated["type"] == "gun":
                reformated["dammage"] = action.get("dammage", 0)       # TODO: validating input
                reformated["size"] = action.get("size", "Superheavy")  # TODO: validating input
                reformated["target"] = action.get("target", "Single")  # TODO: validating input
                reformated["tags"] = action.get("tags", [])            # TODO: reformating + validating input
                reformated["charge"] = action.get("charge", -1)
            res.append(reformated)
        return res
    
    def get_stats_charge_weapons(self, abilites: list[Obj]) -> Obj:
        charge_objs = {}
        i = 1
        for ability in abilites:
            if ability["type"] != "gun":
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
        comp = self.capitalship_compendium.get(name.lower(), {})
        abilities = self.get_stats_action(comp.get("abilities", []), name)
        wing_objs = self.get_stats_wings(comp.get("wings", []))
        charge_objs = self.get_stats_charge_weapons(abilities)
        return {
            "_name": name.lower(),
            "_defense": comp.get("defense", 5),
            "_interdiction": comp.get("interdiction", "1d6"),
            "_valid": name.lower() in self.capitalship_compendium,
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
        comp = self.escorts_compendium.get(name.lower(), {})
        abilities = self.get_stats_action(comp.get("abilities", []), name)
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
            "_valid": name.lower() in self.escorts_compendium,
            KEY_PREFIX: [{
                "hp": x,
                **comp.get("counters", {}),
                **DEFAULT_COUNTERS,
            } for x in comp.get("hp", [])],
            **wing_objs,
            **charge_objs,
        }
