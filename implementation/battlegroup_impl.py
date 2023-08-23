import re
import json

from data_backend import load, can_load
from implementation.battlegroup_output import format_bg
from implementation.battlegroup_npc import *

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

    def _load_compendium(self, name: str) -> list:
        path = "battlegroup/" + name
        res = []
        if can_load(path):
            lib: dict[str, list[dict]] = load(path)
            for capitalship in lib.get("npc_capital", []):
                self.capitalship_compendium[capitalship.get("name", "__UNNAMED__")] = capitalship
            for escort in lib.get("npc_escorts", []):
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

    def _get_stats_capitalship(self, name: str) -> Obj:
        comp = self.capitalship_compendium.get(name.lower(), {})
        wing_objs = self._get_stats_wings(comp.get("wings", []))
        return {
            "_name": name.lower(),
            "_defense": comp.get("defense", 5),
            "_interdiction": comp.get("interdiction", "1d6"),
            "_valid": name.lower() in self.capitalship_compendium,
            "_hp0": comp.get("hp", 1),
            ".": {
                "hp": comp.get("hp", 1),
                "max_hp": comp.get("hp", 1),
                **{"&" + k: v for k, v in comp.get("charges", {}).items()},
                **{"0" + k: v for k, v in comp.get("charges", {}).items()},
                **comp.get("counters", {}),
                **DEFAULT_COUNTERS
            },
            **wing_objs
        }
    
    def _get_stats_escort(self, name: str) -> Obj:
        comp = self.escorts_compendium.get(name.lower(), {})
        wing_objs = self._get_stats_wings(comp.get("wings", []))
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
                **{"&" + k: v for k, v in comp.get("charges", {}).items()},
                **{"0" + k: v for k, v in comp.get("charges", {}).items()},
                **DEFAULT_COUNTERS,
            } for x in comp.get("hp", [])],
            **wing_objs,
        }

    def add_npc(self, npc_code: str, name: str="") -> typing.Optional[NPCBattleGroup]:
        """
        code template: 
        "FLAGSHIP ::: (ESCORT_1, ESCORT_2, ...) "
        """
        if re.match(r"^\s*\w+\s*(:::\s*\(\s*\w+(\s*,\s*\w+)*\s*\))?$", npc_code) is None:
            self.error_queue.append(f"Invalid NPC syntax: '{npc_code}'")
            return None

        if ":::" in npc_code:
            flagship_name, escorts_names = npc_code.strip().split(":::")
            escorts_names = [x.strip() for x in escorts_names.strip()[1:-1].split(",")]
        else:
            flagship_name, escorts_names = npc_code, []
        flagship_name = flagship_name.strip()
        flagship_stats = self._get_stats_capitalship(flagship_name)
        if not flagship_stats["_valid"]:
            self.error_queue.append(f"Invalid capitalship name: {flagship_name}")
        if name == "":
            name = f"bg{len(self.npcs) + 1}"
        name = name.lower()
        npc_bg = NPCBattleGroup(name, flagship_stats)
        for escort_name in escorts_names:
            escort_stats = self._get_stats_escort(escort_name)
            if not escort_stats["_valid"]:
                self.error_queue.append(f"Invalid capitalship name: {escort_name}")
            npc_bg.add_escort(escort_stats)

        self.npcs[name] = npc_bg
        return npc_bg

    def check_path_valid(self, path: str, include_property: bool=False) -> bool:
        steps = path.split(".")
        if include_property:
            steps = steps[:-1]
        if steps[0] not in self.npcs:
            return False
        bg = self.npcs[steps[0]]
        res = bg.is_path_valid(steps[1:])
        if res != "":
            self.error_queue.append(res)
            return False
        return True

    def area_dmg(self, fleet_name: str, dmg: int) -> None:
        bg = self.npcs[fleet_name]
        bg.inc_counter(["**", "hp"], -dmg)
        bg.recalc_boni()
        self.get_gm_detail(fleet_name)
        
    def ship_dmg(self, path: str, dmg: int) -> None:
        steps = path.split(".")
        bg = self.npcs[steps[0]]
        bg.inc_counter(steps[1:] + ["hp"], -dmg)
        bg.recalc_boni()
        self.get_gm_detail(path)

    def set_attribute(self, path: str, value: str) -> None:
        steps = path.split(".")
        bg = self.npcs[steps[0]]
        if bg.is_path_valid(steps[1:-1]):
            return
        if value == "r":
            res = bg.reset_counter(steps[1:])
            if res != "":
                self.error_queue.append(res)
        elif re.match(r"[+-]\d+", value) is not None:
            bg.inc_counter(steps[1:], int(value[1:]))
        elif value.isdigit():
            bg.set_counter(steps[1:], int(value))
        self.get_gm_detail(path)
    
    def logistics_phase(self) -> None:
        charge_triggers = []
        for npc in self.npcs.values():
            charge_triggers += npc.logistics_phase()
        for bg, weapon in charge_triggers:
            self.message_queue.append(f"BG: {bg} - {weapon} charged")  # TODO
        self.turn += 1
                
    def reassign_escort(self, path1: str, bg2_name: str = "") -> bool:
        bg_name, *escort_path = path1.split(".")
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
        
    def get_gm_detail(self, path: str):
        if "." in path: path, *_ = path.split(".")
        if path not in self.npcs:
            self.error_queue.append(f"No such battlegroup: {path}")
            return
        self.message_queue.append("$LONG" + format_bg(self.npcs[path], True) + "\n")

    def compile_actions(self, path: str, ) -> None:
        pass

    def save_to(self, path: str) -> None:
        with open(path + ".json", "w") as f:
            save_dict = {
                "npcs": [x.save() for x in self.npcs.values()],
                "modifiers": self.modifiers,
                "opened": self.opened,
                "turn": self.turn
            }
            json.dump(save_dict, f, indent="  ")
        self.message_queue.append(f"Saved game to \"{path}\"")

    def load_from(self, path: str):
        with open(path + ".json", "r") as f:
            save_dict = json.load(f)
            self.npcs = dict((x["name"], NPCBattleGroup.load(x)) for x in save_dict["npcs"])
            self.modifiers = save_dict["modifiers"]
            self.opened = save_dict["opened"]
            self.turn = save_dict["turn"]
        self.message_queue.append(f"Loaded game from \"{path}\"")

def tests():
    battle = BGBattle()
    battle.open("Threading the needle", "LOCAL")
    battle.add_npc("BREAKWATER ::: (LOYAL_GUARDIAN, DEN_MOTHER, BROTHERS_IN_ARMS, ALBEDO_CAVALIER)", "Alpha")
    battle.add_npc("PALADIN ::: (ROUGHNECKS)")
    battle.add_npc("HIGHLINE ::: (BROTHERS_IN_ARMS, STARFIELD_FURIES)")
    battle.add_npc("CORSAIR ::: (ROUGHNECKS)")
    battle.save_to("save/temp")
    assert battle.check_path_valid("bg2"), battle.error_queue[-1]
    assert battle.check_path_valid("bg3.e2.w3"), battle.error_queue[-1]
    assert battle.check_path_valid("bg4.e1.2"), battle.error_queue[-1]
    battle.ship_dmg("bg3.e2.w3", 1)
    battle.ship_dmg("bg3.e2.w3.2", 2)
    battle.reassign_escort("bg3.e2", "bg2")
    battle.reassign_escort("bg3.e1", "")
    battle.reassign_escort("bg4.e1", "bg2")
    battle.area_dmg("bg2", 4)
    battle.set_attribute("bg3.lockon", "1")
    battle.set_attribute("alpha.e3.greywash", "+1")
    d1 = battle.__dict__
    battle.save_to("save/temp")
    battle.load_from("save/temp")
    assert d1 == battle.__dict__
    print(battle.get_gm_rapport())
    print(battle.get_player_rapport())
    #print(acm_long_embed("Message", "Author"))

if __name__ == "__main__":
    tests()