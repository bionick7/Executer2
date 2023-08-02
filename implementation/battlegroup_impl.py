import re
import json
import random
from datetime import datetime

from data_backend import load, can_load

DEFAULT_COUNTERS = {"lockon": 0, "greywash": 0}

def corrupted(text: str) -> str:
    return ''.join([chr(ord(c) % 16 + 0x2590) if c.isalpha() else c for c in text])

def acm(msg: str, author: str = "$LGN") -> str:
    return f">//[{author}]:: {msg.upper()}"

def acm_embed(msg: str, author: str = "$LGN") -> str:
    return f"```>//[{author}]:: {msg.upper()}```"

def acm_long_embed(msg: str, author: str = "$LGN") -> str:
    fictional_date: datetime = datetime.now() - datetime(2023, 6, 7, 00, 00) + datetime(5016, 3, 30, 00, 00)
    date = fictional_date.strftime("%j.%Y %H:%M CrST")
    header = f"""
TIMESTAMP:           ({date})
CODE+++PURPOSE:      SHOW BATTLE STATUS
DISTRIBUTION:        VOID SPEER TASK FORCE -- CLEARANCE: CAPTAIN
MESSAGE TO FOLLOW:::
"""
    return "```" + header + msg + "```"

def format_wing(w: dict, gm: bool) -> str:
    res = f"[W]{len(w['hp'])}x {w['name'].upper()}"
    if gm:
        res += f" [{w['range']}] " + "|".join(str(x) for x in w['hp'])
    if all(x <= 0 for x in w['hp']):
        res = corrupted(res)
    return res + "\n"

def format_bg(bg, gm: bool) -> str:
    res = f"{bg.name.upper()} :: "
    cap = f"{bg.capitalship['name'].upper()}"
    if gm:
        cap += f" Def: {bg.capitalship['defense']} " + "".join([f"+{x}" for x in bg.capitalship['+defense']])
        cap += f"I: {bg.capitalship['interdiction']}" + "".join([f"+{x}" for x in bg.capitalship['+interdiction']])
        cap += f" - {bg.capitalship['hp']}/{bg.capitalship['max_hp']}"
    for lo in range(bg.capitalship['counters']['lockon']):
        cap = f">{cap}<"
    if bg.capitalship['hp'] <= 0:
        cap = corrupted(cap)
    res += cap + "\n"
    if gm:
        for name, value in bg.capitalship['charges'].items():
            res += f"  ({name.upper()}: {value})\n"
        for name, value in bg.capitalship['counters'].items():
            if name != "lockon" and value != 0:
                res += f"  ({name.upper()}: {value})\n"
    for w in bg.capitalship['wings']:
        res += "    " + format_wing(w, gm)
    for escort in bg.escorts.values():
        escort_txt = ""
        if escort['is_template']:
            escort_txt += f"    {escort['name'].upper()}"
        else:
            escort_txt += f"    {len(escort['hp'])}x {escort['name'].upper()}"
            if gm:
                escort_txt += f" Def:{escort['defense']}"
                escort_txt += " - "
                escort_txt += "|".join(str(x) for x in escort['hp'])
        escort_txt += "\n"
        if gm:
            for name, value in escort['charges'].items():
                escort_txt += f"      ({name.upper()}: {value})\n"
            for name, value in escort['counters'].items():
                if name != "lockon" and value != 0:
                    escort_txt += f"      ({name.upper()}: {value})\n"
        for w in escort['wings']:
            escort_txt += "        " + format_wing(w, gm)
        if all(x <= 0 for x in escort['hp']) and not escort['is_template']:
            escort_txt = corrupted(escort_txt)
        res += escort_txt
    return res

class NPCBattleGroup:
    def __init__(self, p_name: str, p_stats: dict):
        self.name = p_name
        self.capitalship = {
            **p_stats,
            "hp": p_stats.get("hp", p_stats["hp0"]),
            "max_hp": p_stats.get("max_hp", p_stats["hp0"]),
            "+interdiction": p_stats.get("+interdiction", []),
            "+defense": p_stats.get("+defense", [])
        }
        self.escorts = {}
    
    def add_escort(self, p_escort_dict: dict):
        if not p_escort_dict.get("_init", False):
            escort_dict = {
                **p_escort_dict,
                "hp": p_escort_dict["hp0"],
                "max_hp": p_escort_dict["hp0"],
                "_init": True
            }
        else:
            escort_dict = p_escort_dict
        if not escort_dict["_valid"]:
            return
        if escort_dict['name'] in self.escorts:
            if escort_dict['is_unique'] or escort_dict['is_template']:
                return
            else:
                self.escorts[escort_dict['name']]['hp'] += escort_dict["hp"]
        else:
            self.escorts[escort_dict['name']] = escort_dict

    def recalc_boni(self):
        self.capitalship['+defense'] = []
        self.capitalship['+interdiction'] = []
        self.capitalship['hp'] = self.capitalship['hp0']
        self.capitalship['max_hp'] = self.capitalship['hp0']
        for escort in self.escorts:
            if escort['+defense'] > 0:
                self.capitalship['+defense'].append(escort['+defense'])
            if escort['+interdiction'] != "":
                self.capitalship['+interdiction'].append(escort['+interdiction'])
            if escort['+hp'] > 0:
                self.capitalship['hp'] += escort['+hp']
                self.capitalship['max_hp'] += escort['+hp']

    @staticmethod
    def _get_wing_unit(path: list[str]) -> tuple[int, int]:
        wing_index = int(path[0][1:]) - 1
        if len(path) > 1 and path[1].isdigit():
            unit_index = int(path[1]) - 1
        else:
            unit_index = 0
        return wing_index, unit_index

    def is_path_valid(self, path: list[str]) -> str:
        if len(path) == 0:
            return ""
        elif re.match(r"w\d+", path[0]):
            if len(path) > 1 and not path[1].isdigit():
                return "Invalid syntax"
            wing_index, unit_index = self._get_wing_unit(path)
            if len(self.capitalship["wings"]) <= wing_index:
                return f"{self.capitalship['name']} has only {len(self.capitalship['wings'])} wings"
            if wing_index < 0: return "Index must be greater than 0"
            wing = self.capitalship["wings"][wing_index]
            if len(wing["hp"]) <= unit_index:
                return f"{wing['name']} has only {len(wing['hp'])} units"
            if unit_index < 0: return "Index must be greater than 0"
            return ""
        elif re.match(r"e\d+", path[0]):
            escort_index = int(path[0][1:]) - 1
            if len(self.escorts) <= escort_index:
                return f"{self.name} has only {len(self.escorts)} escorts"    
            if escort_index < 0: return "Index must be greater than 0"
            escort = list(self.escorts.values())[escort_index]
            if escort["is_template"]:
                return f"{escort['name']} is a template"
            if len(path) == 1:
                return ""
            elif path[1].isdigit():
                unit_index = int(path[1]) - 1
                if len(escort["hp"]) <= unit_index:
                    return f"{escort['name']} has only {len(escort['hp'])} units"
                if unit_index < 0: return "Index must be greater than 0"
                return ""
            elif re.match(r"w\d+", path[1]):
                if len(path) > 2 and not path[2].isdigit():
                    return "Invalid syntax"
                wing_index, unit_index = self._get_wing_unit(path[1:])
                if len(escort["wings"]) <= wing_index:
                    return f"{escort['name']} has only {len(escort['wings'])} wings"
                if wing_index < 0: return "Index must be greater than 0"
                wing = escort["wings"][wing_index]
                if len(wing["hp"]) <= unit_index:
                    return f"{wing.name} has only {len(wing['hp'])} units"
                if unit_index < 0: return "Index must be greater than 0"
                return ""
            return "Invalid syntax"
        return "Invalid syntax"

    def decode_path(self, path: list[str]):
        """
        [] => capital ship
        [wX] => capital ship wing X, unit 0
        [wX.uY] => capital ship wing X, unit Y
        [eX] => capital ship escort 0, unit 0
        [eX.uY] => capital ship escort X, unit Y
        [eX.wY] => capital ship escort X, wing Y, unit 0
        [eX.wY.uZ] => capital ship escort X, wing Y, unit Z
        """
        if len(path) == 0:
            return self.capitalship, -1
        elif re.match(r"w\d+", path[0]):
            wing_index, unit_index = self._get_wing_unit(path)
            return self.capitalship["wings"][wing_index], unit_index
        elif re.match(r"e\d+", path[0]):
            escort_index = int(path[0][1:]) - 1
            escort = list(self.escorts.values())[escort_index]
            if len(path) == 1:
                return escort, 0
            elif path[1].isdigit():
                unit_index = int(path[1]) - 1
                return escort, unit_index
            else:
                wing_index, unit_index = self._get_wing_unit(path[1:])
                return escort["wings"][wing_index], unit_index
        return {}, -1
    
    def take_area_dmg(self, dmg: int) -> None:
        self.capitalship["hp"] -= dmg
        for w in self.capitalship["wings"]:
            for i in range(len(w["hp"])):
                w["hp"][i] -= dmg
        for e in self.escorts.values():
            for i in range(len(e["hp"])):
                e["hp"][i] -= dmg
            for w in e["wings"]:
                for i in range(len(w["hp"])):
                    w["hp"][i] -= dmg

    def take_dmg(self, path: list[str], dmg: int) -> None:
        obj, unit_index = self.decode_path(path)
        if unit_index >= 0:
            obj["hp"][unit_index] -= dmg
        else:
            obj["hp"] -= dmg
            
    def inc_counter(self, path: list[str], value: int) -> None:
        counter_name = path[-1]
        obj, _ = self.decode_path(path[:-1])
        if "counters" in obj:
            obj["counters"][counter_name] += value
            
    def set_counter(self, path: list[str], value: int) -> None:
        counter_name = path[-1]
        obj, _ = self.decode_path(path[:-1])
        if "counters" in obj:
            obj["counters"][counter_name] = value

    def remove_escort(self, escort_index: int) -> dict:
        res_key = list(self.escorts.keys())[escort_index]
        res = self.escorts[res_key]
        del self.escorts[res_key]
        return res

    def logistics_phase(self):
        pass

    def save(self) -> dict:
        return {
            "name": self.name,
            "capitalship": self.capitalship,
            "escorts": self.escorts
        }

    @classmethod
    def load(cls, save_dict: dict):
        res = cls(save_dict["name"], save_dict["capitalship"])
        res.escorts = save_dict["escorts"]
        return res
    

class BGBattle:
    def __init__(self):
        self.modifiers = []
        self.npcs = {}
        self.payloads = []
        self.error_queue = []

        self.capitalship_compendium = {}
        self.escorts_compendium = {}

        self.opened = False
        self._load_compendium("core")

        self.gm = None

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

    def open(self, p_gm, *p_modifiers: str):
        self.modifiers = p_modifiers
        self.opened = True
        self.gm = p_gm

    def close(self):
        self.gm = None
        self.opened = False
        self.modifiers = []
        self.npcs = {}
        self.payloads = []

    def get_stats_capitalship(self, name: str) -> dict:
        comp = self.capitalship_compendium.get(name.lower(), {})
        wings = comp.get("wings", [])
        if isinstance(wings, dict):
            wings = [wings]
        counters = {**comp.get("counters", {}), "lockon": 0, "greywash": 0}
        return {
            "name": name.lower(),
            "hp0": comp.get("hp", 1),
            "defense": comp.get("defense", 5),
            "interdiction": comp.get("interdiction", "1d6"),
            "wings": wings,
            "charges": comp.get("charges", {}),
            "counters": {**comp.get("counters", {}), **DEFAULT_COUNTERS},
            "_valid": name.lower() in self.capitalship_compendium,
        }
    
    def get_stats_escort(self, name: str) -> dict:
        comp = self.escorts_compendium.get(name.lower(), {})
        wings = comp.get("wings", [])
        if isinstance(wings, dict):
            wings = [wings]
        tags = [x.lower() for x in comp.get("tags", [])]
        return {
            "name": name.lower(),
            "hp0": comp.get("hp", []),
            "defense": comp.get("defense", 5),
            "+defense": comp.get("+defense", 0),
            "+interdiction": comp.get("+interdiction", ""),
            "+hp": comp.get("+hp", 0),
            "is_template": "template" in tags,
            "is_unique": "unique" in tags,
            "wings": wings,
            "charges": comp.get("charges", {}),
            "counters": {**comp.get("counters", {}), **DEFAULT_COUNTERS},
            "_valid": name.lower() in self.escorts_compendium
        }

    @staticmethod
    def is_valid_npc(npc_code: str) -> str:
        if re.match(r"^\w+(\s*::\s*\(\s*\w+(\s*,\s*\w+)*\s*\))?$", npc_code) is None:
            return "Invalid syntax"
        # TODO: Additional checks
        return ""
        

    def add_npc(self, npc_code: str, name: str="") -> NPCBattleGroup:
        """
        code template: 
        "FLAGSHIP ::: (ESCORT_1, ESCORT_2, ...) "
        """
        flagship_name, escorts_names = "", []
        if ":::" in npc_code:
            flagship_name, escorts_names = npc_code.strip().split(":::")
            escorts_names = [x.strip() for x in escorts_names.strip()[1:-1].split(",")]
        else:
            flagship_name, escorts_names == npc_code, []
        flagship_name = flagship_name.strip()
        flagship_stats = self.get_stats_capitalship(flagship_name)
        if name == "":
            name = f"bg{len(self.npcs) + 1}"
        name = name.lower()
        npc_bg = NPCBattleGroup(name, flagship_stats)
        for escort_name in escorts_names:
            escort_stats = self.get_stats_escort(escort_name)
            npc_bg.add_escort(escort_stats)

        self.npcs[name] = npc_bg
        return npc_bg

    def check_path_valid(self, path: str, include_property: bool=False) -> bool:
        steps = path.split(".")
        if include_property:
            steps = steps[:-1]
        if len(steps) == 0:
            return False
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
        bg.take_area_dmg(dmg)
        
    def ship_dmg(self, path: str, dmg: int) -> None:
        steps = path.split(".")
        bg = self.npcs[steps[0]]
        bg.take_dmg(steps[1:], dmg)
                
    def reassign_escort(self, path1: str, bg2_name: str = "") -> bool:
        bg_name, escort_index = path1.split(".")
        if bg_name not in self.npcs:
            self.error_queue.append(f"no such battlegroup: {bg_name}")
            return False
        if bg2_name not in self.npcs and bg2_name != "":
            self.error_queue.append(f"no such battlegroup: {bg2_name}")
            return False
        if bg_name == bg2_name:
            return True
        bg1: NPCBattleGroup = self.npcs[bg_name]
        path_error = bg1.is_path_valid([escort_index])
        if path_error != "":
            self.error_queue.append(path_error)
            return False
        if re.match(r"^e\d+$", escort_index) is None:
            self.error_queue.append(f"not valid path to escort: {path1}")
            return False
        escort_index = int(escort_index[1:]) - 1
        escort = bg1.remove_escort(escort_index)
        if bg2_name != "":
            self.npcs[bg2_name].add_escort(escort)
        return True
    
    def kill(self, path: str) -> bool:
        self.error_queue.append("Not implemented")
        return False

    def set_counter(self, path: str, value: str) -> None:
        steps = path.split(".")
        bg = self.npcs[steps[0]]
        if re.match(r"[+-]\d+", value) is not None:
            bg.inc_counter(steps[1:], int(value[1:]))
        elif value.isdigit():
            bg.set_counter(steps[1:], int(value))

    def get_player_rapport(self) -> str:
        res = ""
        for npc in self.npcs.values():
            res += format_bg(npc, False)
        return res

    def get_gm_rapport(self) -> str:
        res = ""
        for npc in self.npcs.values():
            res += format_bg(npc, True)
        return res
        
    def save_to(self, path: str) -> None:
        with open(path + ".json", "w") as f:
            save_dict = {
                "npcs": [x.save() for x in self.npcs.values()],
                "modifiers": self.modifiers,
                "opened": self.opened
            }
            json.dump(save_dict, f, indent="  ")

    def load_from(self, path: str):
        with open(path + ".json", "r") as f:
            save_dict = json.load(f)
            self.npcs = dict((x["name"], NPCBattleGroup.load(x)) for x in save_dict["npcs"])
            self.modifiers = save_dict["modifiers"]
            self.opened = save_dict["opened"]

def test():
    battle = BGBattle()
    battle.open("Threading the needle")
    battle.add_npc("BREAKWATER ::: (LOYAL_GUARDIAN, DEN_MOTHER, BROTHERS_IN_ARMS, ALBEDO_CAVALIER)", "Alpha")
    battle.add_npc("PALADIN ::: (ROUGHNECKS)")
    battle.add_npc("HIGHLINE ::: (BROTHERS_IN_ARMS, STARFIELD_FURIES)")
    battle.add_npc("CORSAIR ::: (ROUGHNECKS)")
    assert battle.check_path_valid("bg2")
    assert battle.check_path_valid("bg3.e2.w3")
    assert battle.check_path_valid("bg4.e1.2")
    battle.ship_dmg("bg3.e2.w3", 1)
    battle.ship_dmg("bg3.e2.w3.2", 2)
    battle.reassign_escort("bg3.e2", "bg2")
    battle.reassign_escort("bg3.e1", "")
    battle.reassign_escort("bg4.e1", "bg2")
    battle.area_dmg("bg2", 4)
    battle.set_counter("bg3.lockon", "1")
    battle.set_counter("alpha.e3.greywash", "+1")
    d1 = battle.__dict__
    battle.save_to("save/temp")
    battle.load_from("save/temp")
    assert d1 == battle.__dict__
    print(battle.get_gm_rapport())
    print(battle.get_player_rapport())
    #print(acm_long_embed("Message", "Author"))

if __name__ == "__main__":
    test()