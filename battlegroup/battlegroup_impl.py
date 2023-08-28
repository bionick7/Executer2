import re
import json
import os.path

import dictdiffer

from data_backend import load, can_load
from battlegroup.output import format_bg
from battlegroup.npc import *

DEFAULT_COUNTERS = {"lockon": 0, "greywash": 0}
 
class BGBattleData:
    def  __init__(self, p_message_queue, p_error_queue) -> None:
        self.filepath = "__INVALID"

        self.current_state: Obj = {}

        self.last_state: Obj = {}
        self.history: list = []
        self.history_pointer = 0  # current state
        self.filehash: int = 0
        self.message_queue = p_message_queue
        self.error_queue = p_error_queue
    
    def watch_or_dump(self) -> bool:
        if self.filepath == "__INVALID":
            return False
        if not os.path.isfile(self.filepath):
            self._dump_current()
            return False
        else:
            return self.watch()

    def watch(self) -> bool:
        ''' Returns if data has been changed '''
        if self.filepath == "__INVALID":
            return False
        if not os.path.isfile(self.filepath):
            self.error_queue.append(f"Watch file ({self.filepath}) does not exist")
            return False
        with open(self.filepath, "r") as f:
            txt = f.read()
            hash2 = hash(txt)
            if hash2 == self.filehash:
                return False
            else:
                self._deserialize(json.loads(txt))
                return True
    
    def _dump_current(self) -> None:
        if self.filepath == "__INVALID":
            return
        txt = json.dumps(self._serialize(), indent="  ")
        self.filehash = hash(txt)
        with open(self.filepath, "w") as f:
            f.write(txt)

    def _serialize(self) -> list:
        return [self.last_state, self.history, self.history_pointer]
    
    def _deserialize(self, inp: list) -> None:
        self.last_state, self.history, self.history_pointer = inp
        self.current_state = self.last_state
        while self.history_pointer > 0:
            self.undo()
    
    def save_to(self, filepath: str) -> None:
        true_filepath = "save/" + filepath + ".json"
        with open(true_filepath, "w") as f:
            json.dump(self._serialize(), f, indent="  ")
        self.message_queue.append(f"Saved game to \"{filepath}\"")

    def load_from(self, filepath: str) -> None:
        true_filepath = "save/" + filepath + ".json"
        if not os.path.isfile(true_filepath):
            self.message_queue.append(f"No such file: {true_filepath}")
            return
        with open(true_filepath, "r") as f:
            self._deserialize(json.load(f))
        self.message_queue.append(f"Loaded game from \"{filepath}\"")

    def reset_history(self) -> None:
        self.push_new_state(self.current_state)
        self.history = []
        self.history_pointer = 0
        self._dump_current()

    def push_new_state(self, new_data: Obj) -> None:
        if self.history_pointer == 0:
            diff = list(dictdiffer.diff(self.current_state, new_data))
            self.history.insert(0, diff)
            self.last_state = dictdiffer.deepcopy(new_data)
            self.current_state = self.last_state
        else:  # Overwrite current history
            diff = list(dictdiffer.diff(self.current_state, new_data))
            self.history = [diff] + self.history[:self.history_pointer]
            self.last_state = dictdiffer.deepcopy(new_data)
            self.current_state = self.last_state
            self.history_pointer = 0

        while len(self.history) > 100:
            self.history.pop()
        self._dump_current()

    def get_current(self) -> Obj:
        return self.current_state

    def undo(self) -> None:
        if self.history_pointer == len(self.history):
            return
        self.current_state = dictdiffer.revert(self.history[self.history_pointer], self.current_state)
        self.history_pointer += 1

    def redo(self) -> None:
        if self.history_pointer == 0:
            return
        self.current_state = dictdiffer.patch(self.history[self.history_pointer - 1], self.current_state)
        self.history_pointer -= 1


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

        self.datamanager = BGBattleData(self.message_queue, self.error_queue)

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
            self.message_queue.append("Added compendium: " + path)
        else:
            self.message_queue.append("No such compendium: " + path)
        return res

    def open(self, p_gm: str, *p_modifiers: str) -> None:
        self.modifiers = list(p_modifiers)
        self.opened = True
        self.gm_id = p_gm
        self.npcs = {}
        self.payloads = []
        self.turn = 1
        self.message_queue.append("Constructing legion...")
        self.message_queue.append("$WAIT:0.5")
        self.message_queue.append(f"Authorisation granted to {p_gm}")
        self.on_modified()

    def close(self) -> None:
        self.gm = "NO-ONE"
        self.opened = False
        self.modifiers = []
        self.npcs = {}
        self.payloads = []
        self.turn = -1
        self.on_modified()

    def connect_to(self, path: str) -> None:
        self.datamanager.filepath = "save/" + path + ".json"
        if self.datamanager.watch_or_dump():
            self.opened = True
            self.sync()

    def _get_stats_wings(self, wings: list) -> Obj:
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
    
    def _get_stats_charge_weapons(self, charge_weapons: dict) -> Obj:
        charge_objs = {}
        for i, (k, v) in enumerate(charge_weapons.items()):
            charge_objs[f"{KEY_PREFIX}c{i+1}"] = {
                "_name": k,
                KEY_PREFIX: {
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
            KEY_PREFIX: {
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
            KEY_PREFIX: [{
                "hp": x,
                **comp.get("counters", {}),
                **DEFAULT_COUNTERS,
            } for x in comp.get("hp", [])],
            **wing_objs,
            **charge_objs,
        }

    def on_modified(self) -> None:
        self.datamanager.push_new_state(self.get_data())

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
        self.on_modified()
        return npc_bg

    def check_path_valid(self, path: list[str], include_property: bool=False) -> bool:
        if include_property:
            path = path[:-1]
        if len(path) == 0:
            return False
        if path == ["**"]:
            return True
        if path[0] == "*":
            for bg in self.npcs.values():
                res = bg.is_path_valid(path[1:])
                if res != "":
                    self.error_queue.append(res)
                    return False
            return True
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
        if path[0] == "*":
            for bg in self.npcs.values():
                bg.set_attribute(path[1:], value)
        elif path[0] == "**":
            for bg in self.npcs.values():
                bg.set_attribute(["**", path[-1]], value)
        else:
            bg = self.npcs[path[0]]
            bg.set_attribute(path[1:], value)
        self.on_modified()
        
    def get_attribute(self, path: list[str]) -> int:
        if not self.check_path_valid(path, True):
            self.error_queue.append(f"Requested invalid attribute path:{'.'.join(path)}")
            return -1
        if path[0] == "*":
            for bg in self.npcs.values():
                return bg.get_attribute(path[1:])
        elif path[0] == "**":
            for bg in self.npcs.values():
                return bg.get_attribute(["**", path[-1]])
        bg = self.npcs[path[0]]
        return bg.get_attribute(path[1:])
        
        
    def inc_attribute(self, path: list[str], value: int) -> None:
        if not self.check_path_valid(path, True):
            self.error_queue.append(f"Requested invalid attribute path:{'.'.join(path)}")
            return
        if path[0] == "*":
            for bg in self.npcs.values():
                bg.inc_attribute(path[1:], value)
        elif path[0] == "**":
            for bg in self.npcs.values():
                bg.inc_attribute(["**", path[-1]], value)
        else:
            bg = self.npcs[path[0]]
            bg.inc_attribute(path[1:], value)
        self.on_modified()
        
    def reset_counter(self, path: list[str]) -> None:
        if not self.check_path_valid(path, False):
            self.error_queue.append(f"Requested invalid attribute path:{'.'.join(path)}")
            return
        if path[0] == "*":
            for bg in self.npcs.values():
                bg.reset_counter(path[1:])
        elif path[0] == "**":
            for bg in self.npcs.values():
                bg.reset_counter(["**"])
        else:
            bg = self.npcs[path[0]]
            bg.reset_counter(path[1:])
        self.on_modified()
    
    def logistics_phase(self) -> None:
        charge_triggers = []
        for npc in self.npcs.values():
            charge_triggers += npc.logistics_phase()
        for bg, weapon in charge_triggers:
            self.message_queue.append(f"BG: {bg} - {weapon} charged")  # TODO
        self.turn += 1
        self.on_modified()
                
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
                self.on_modified()
                return True
            else:
                self.error_queue.append(f"Cannot reassign battlegroup {bg_name}")
                return False
        escort = bg1.remove(escort_path)
        if bg2_name != "":
            self.npcs[bg2_name].add_escort(escort)
        self.on_modified()
        return True

    def get_player_rapport(self) -> None:
        res = ""
        for npc in self.npcs.values():
            res += format_bg(npc, False) + "\n"
        if res == "":
            self.message_queue.append("No hostile detected")
            return
        self.message_queue.append("$LONG" + res)

    def get_gm_rapport(self) -> None:
        res = ""
        for npc in self.npcs.values():
            res += format_bg(npc, True) + "\n"
        if res == "":
            self.message_queue.append("No npcs")
            return
        self.message_queue.append("$LONG" + res)
        
    def get_gm_detail(self, query: str):
        if query not in self.npcs:
            self.error_queue.append(f"No such battlegroup: {query}")
            return
        self.message_queue.append("$LONG" + format_bg(self.npcs[query], True) + "\n")

    def compile_actions(self, path: list[str], ) -> None:
        pass

    def get_data(self) -> dict:
        ''' Shallow copy '''
        return {
            "npcs": [x.save() for x in self.npcs.values()],
            "modifiers": self.modifiers,
            "turn": self.turn
        }

    def set_data(self, data: dict) -> None:
        ''' Shallow Copy '''
        self.npcs = dict((x["name"], NPCBattleGroup.load(x)) for x in data["npcs"])
        self.modifiers = data["modifiers"]
        self.turn = data["turn"]

    def sync(self) -> None:
        self.set_data(dictdiffer.deepcopy(self.datamanager.get_current()))
            
    def try_update(self, explicit: bool=True) -> None:
        if self.datamanager.watch():
            if explicit:
                self.message_queue.append("State changed; updating")
            self.sync()