import re
import json
import os.path

from data_backend import load, can_load
from battlegroup.output import format_bg
from battlegroup.npc import *

DEFAULT_COUNTERS = {"lockon": 0, "greywash": 0}
 
class BGBattle:
    def __init__(self):
        self.modifiers = []
        self.npcs = {}
        self.payloads = []
        self.error_queue = []
        self.message_queue = []

        self.capitalship_compendium = {}
        self.escorts_compendium = {}

        self.opened = False
        self._load_compendium("core")

        self.gm_id :str = "NO-ONE"
        self.turn = -1

        self.undo_stack = []
        self.undo_pointer = 0

    def _load_compendium(self, name: str) -> list:
        path = "battlegroup/" + name
        res = []
        if can_load(path):
            lib: dict[str, list[dict]] = load(path)
            for capitalship in lib.get("npc-capital", []):
                self.capitalship_compendium[capitalship.get("name", "__UNNAMED__")] = capitalship
            for escort in lib.get("npc-escorts", []):
                self.escorts_compendium[escort.get("name", "__UNNAMED__")] = escort
            res.append(lib["__meta__"])
            print("Added compendium: " + path)
        else:
            print("No such compendium: " + path)
        return res

    def open(self, p_gm: str, *p_modifiers: str):
        self.modifiers = p_modifiers
        self.opened = True
        self.gm_id = p_gm
        self.turn = 1
        self.message_queue.append("Constructing legion...")
        self.message_queue.append("$WAIT:0.5")
        self.message_queue.append(f"Authorisation granted to {p_gm}")

    def close(self):
        self.gm = "NO-ONE"
        self.opened = False
        self.modifiers = []
        self.npcs = {}
        self.payloads = []
        self.turn = -1

    def _get_stats_wings(self, wings: list) -> Obj:
        if not isinstance(wings, list):
            wings = [wings]
        wing_objs = {}
        for i, w in enumerate(wings):
            wing_objs[f".w{i+1}"] = {
                "_name": w.get("name", "UNNAMED"),
                "_range": w.get("range", "0-0"),
                "_tenacity": w.get("tenacity", 0),
                ".": [{"hp": x, **DEFAULT_COUNTERS} for x in w["hp"]]
            }
        return wing_objs
    
    def _get_stats_charge_weapons(self, charge_weapons: dict) -> Obj:
        charge_objs = {}
        for i, (k, v) in enumerate(charge_weapons.items()):
            charge_objs[f".c{i+1}"] = {
                "_name": k,
                ".": {
                    "total": v,
                    "current": v
                }
            }
        return charge_objs

    def _get_stats_capitalship(self, name: str) -> Obj:
        comp = self.capitalship_compendium.get(name.lower(), {})
        wing_objs = self._get_stats_wings(comp.get("wings", []))
        charge_objs = self._get_stats_charge_weapons(comp.get("charges", {}))
        return {
            "_name": name.lower(),
            "_defense": comp.get("defense", 5),
            "_interdiction": comp.get("interdiction", "1d6"),
            "_valid": name.lower() in self.capitalship_compendium,
            "_hp0": comp.get("hp", 1),
            ".": {
                "hp": comp.get("hp", 1),
                "max_hp": comp.get("hp", 1),
                **comp.get("counters", {}),
                **DEFAULT_COUNTERS
            },
            **wing_objs,
            **charge_objs,
        }
    
    def _get_stats_escort(self, name: str) -> Obj:
        comp = self.escorts_compendium.get(name.lower(), {})
        wing_objs = self._get_stats_wings(comp.get("wings", []))
        charge_objs = self._get_stats_charge_weapons(comp.get("charges", {}))
        tags = [x.lower() for x in comp.get("tags", [])]
        return {
            "_name": name.lower(),
            "_defense": comp.get("defense", 5),
            "+defense": comp.get("+defense", 0),
            "+interdiction": comp.get("+interdiction", ""),
            "+hp": comp.get("+hp", 0),
            "_is_template": "template" in tags,
            "_is_unique": "unique" in tags,
            "_valid": name.lower() in self.escorts_compendium,
            ".": [{
                "hp": x,
                **comp.get("counters", {}),
                **DEFAULT_COUNTERS,
            } for x in comp.get("hp", [])],
            **wing_objs,
            **charge_objs,
        }

    def add_npc(self, flagship_name: str, escorts_names: list[str], name: str) -> typing.Optional[NPCBattleGroup]:
        flagship_stats = self._get_stats_capitalship(flagship_name)
        if not flagship_stats["_valid"]:
            self.error_queue.append(f"Invalid capitalship name: {flagship_name}")
        npc_bg = NPCBattleGroup(name, flagship_stats)
        for escort_name in escorts_names:
            escort_stats = self._get_stats_escort(escort_name)
            if not escort_stats["_valid"]:
                self.error_queue.append(f"Invalid escort name: {escort_name}")
            npc_bg.add_escort(escort_stats)

        self.npcs[name] = npc_bg
        return npc_bg

    def check_path_valid(self, path: list[str], include_property: bool=False) -> bool:
        if include_property:
            path = path[:-1]
        if len(path) == 0:
            return False
        if path[0] not in self.npcs:
            return False
        bg = self.npcs[path[0]]
        res = bg.is_path_valid(path[1:])
        if res != "":
            self.error_queue.append(res)
            return False
        return True

    def set_attribute(self, path: list[str], value: int) -> None:
        if not self.check_path_valid(path, True):
            return
        bg = self.npcs[path[0]]
        #if bg.is_path_valid(path[1:-1]):
        #    return
        bg.set_counter(path[1:], value)
        #self.get_gm_detail(path[0])
        
    def inc_attribute(self, path: list[str], value: int) -> None:
        if not self.check_path_valid(path, True):
            return
        bg = self.npcs[path[0]]
        #if bg.is_path_valid(path[1:-1]):
        #    return
        bg.inc_counter(path[1:], value)
        #self.get_gm_detail(path[0])
        
    def reset_attribute(self, path: list[str]) -> None:
        if not self.check_path_valid(path, True):
            return
        bg = self.npcs[path[0]]
        if bg.is_path_valid(path[1:-1]):
            return
        res = bg.reset_counter(path[1:])
        #if res != "":
        #    self.error_queue.append(res)
        #self.get_gm_detail(path[0])
    
    def logistics_phase(self) -> None:
        charge_triggers = []
        for npc in self.npcs.values():
            charge_triggers += npc.logistics_phase()
        for bg, weapon in charge_triggers:
            self.message_queue.append(f"BG: {bg} - {weapon} charged")  # TODO
        self.turn += 1
                
    def reassign_escort(self, path: list[str], bg2_name: str = "") -> bool:
        if not self.check_path_valid(path, False):
            return False
        bg_name = path[0]
        escort_path = path[1:]
        if bg_name not in self.npcs:
            self.error_queue.append(f"no such battlegroup: {bg_name}")
            return False
        if bg2_name not in self.npcs and bg2_name != "":
            self.error_queue.append(f"no such battlegroup: {bg2_name}")
            return False
        if bg_name == bg2_name:
            return True
        bg1: NPCBattleGroup = self.npcs[bg_name]
        if len(escort_path) == 0:
            if  bg2_name == "":
                del self.npcs[bg_name]
                self.message_queue.append(f"Removed battlegroup {bg_name}")
                return True
            else:
                self.error_queue.append(f"Cannot reassign battlegroup {bg_name}")
                return False
        escort = bg1.remove(escort_path)
        if bg2_name != "":
            self.npcs[bg2_name].add_escort(escort)
        return True

    def get_player_rapport(self) -> None:
        res = ""
        for npc in self.npcs.values():
            res += format_bg(npc, False) + "\n"
        if res == "":
            self.error_queue.append("No hostile detected")
            return
        self.message_queue.append("$LONG" + res)

    def get_gm_rapport(self) -> None:
        res = ""
        for npc in self.npcs.values():
            res += format_bg(npc, True) + "\n"
        if res == "":
            self.error_queue.append("No npcs")
            return
        self.message_queue.append("$LONG" + res)
        
    def get_gm_detail(self, query: str):
        if query not in self.npcs:
            self.error_queue.append(f"No such battlegroup: {query}")
            return
        self.message_queue.append("$LONG" + format_bg(self.npcs[query], True) + "\n")

    def compile_actions(self, path: list[str], ) -> None:
        pass

    def save_to(self, filepath: str) -> None:
        true_filepath = "save/" + filepath + ".json"
        with open(true_filepath, "w") as f:
            save_dict = {
                "npcs": [x.save() for x in self.npcs.values()],
                "modifiers": self.modifiers,
                "opened": self.opened,
                "turn": self.turn
            }
            json.dump(save_dict, f, indent="  ")
        self.message_queue.append(f"Saved game to \"{filepath}\"")

    def load_from(self, filepath: str) -> None:
        true_filepath = "save/" + filepath + ".json"
        if not os.path.isfile(true_filepath):
            self.message_queue.append(f"No such file: {true_filepath}")
            return
        with open(true_filepath, "r") as f:
            save_dict = json.load(f)
            self.npcs = dict((x["name"], NPCBattleGroup.load(x)) for x in save_dict["npcs"])
            self.modifiers = save_dict["modifiers"]
            self.opened = save_dict["opened"]
            self.turn = save_dict["turn"]
        self.message_queue.append(f"Loaded game from \"{filepath}\"")

    def undo(self) -> None:
        pass

    def redo(self) -> None:
        pass
