"""       
{
    ".": {A},
    ".w1": {
    ".": [ {B}, {C} ]
    },
    ".e1": {
    ".": [ {D} ],
    ".w1": {
        ".": [ {E} ]
    },
    "_meta": 1
    },
}
   -> A
w1 -> [B, C]
w1.* -> [B, C]
w1.1 -> B
w1.2 -> C
w1.* -> [B, C]
e1.* -> D
e1.w1.1 -> E
e1.** -> [D, E]
** -> [A, B, C, D, E]
"""

KEY_PREFIX = "."

import typing
Obj = dict[str, typing.Any]

class NPCBattleGroup:
    def __init__(self, p_name: str, p_stats: dict):
        self.name = p_name
        self.content = p_stats

    @property
    def escorts(self):
        for key, value in self.content.items():
            if key.startswith(KEY_PREFIX + "e"):
                yield value
                
    @property
    def counters(self):
        for k, v in self.content.items():
            if k.startswith(KEY_PREFIX + "c"):
                yield v
        for e in self.escorts:
            for k, v in e.items():
                if k.startswith(KEY_PREFIX + "c"):
                    yield v
    
    def recalc_boni(self):
        content = self.content
        content['+defense'] = []
        content['+interdiction'] = []
        content['hp'] = content['_hp0']
        content['max_hp'] = content['_hp0']
        for escort in self.escorts:
            if any(x['hp'] > 0 for x in escort[KEY_PREFIX]):
                if escort['+defense'] > 0:
                    content['+defense'].append(escort['+defense'])
                if escort['+interdiction'] != "":
                    content['+interdiction'].append(escort['+interdiction'])
                if escort['+hp'] > 0:
                    content['hp'] += escort['+hp']
                    content['max_hp'] += escort['+hp']
    
    def add_escort(self, p_escort_dict: dict):
        if not p_escort_dict.get("_init", False):
            escort_dict = {
                **p_escort_dict,
                "_init": True
            }
        else:
            escort_dict = p_escort_dict
        if not escort_dict["_valid"]:
            return  # TODO: error msg
        
        is_unique = escort_dict['_is_unique'] or escort_dict['_is_template']
        if any(x["_name"] == escort_dict["_name"] for x in self.escorts) and is_unique:
            return  # TODO: error msg
        else:
            escort_num = len(list(self.escorts)) + 1
            self.content[f"{KEY_PREFIX}e{escort_num}"] = escort_dict
        self.recalc_boni()

    def remove(self, path: list[str]) -> Obj:
        cursor = self.content
        for p in path[:-1]:
            cursor = self.content[KEY_PREFIX + p]
        res = cursor[KEY_PREFIX + path[-1]]
        del cursor[KEY_PREFIX + path[-1]]
        self.recalc_boni()
        return res
    
    def is_path_valid(self, path: list[str], include_meta: bool=False) -> str:
        return self.__is_path_valid(path, self.content, include_meta)

    def decode_path(self, path: list[str], include_meta: bool=False) -> list[Obj]:
        return self.__decode_path(path, self.content, include_meta)

    def __is_path_valid(self, path: list[str], content: Obj, include_meta: bool) -> str:
        if len(path) == 0:
            if KEY_PREFIX in content or include_meta: return ""
            else: return "'{KEY_PREFIX}' expected"
        index = path[0]
        if index in ["*", "**"]:
            if include_meta:
                return "No wildcards supproted if include_meta is set"
            for key in content:
                if key.startswith(KEY_PREFIX) and key != KEY_PREFIX:
                    err = self.__is_path_valid(path[1:] if index == "*" else ["**"], content[key], False)
                    if err != "":
                        return err
            return ""
        elif index.isdigit():
            if int(index) - 1 >= len(self.__ensure_list(content.get(KEY_PREFIX, []))):
                return f"{index} Out of bounds {KEY_PREFIX}"
            return ""
        if KEY_PREFIX + index not in content:
            return f"no such key: '{KEY_PREFIX}{index}'"
        return self.__is_path_valid(path[1:], content[KEY_PREFIX+index], include_meta)
    
    @staticmethod
    def __ensure_list(inp) -> list:
        if isinstance(inp, list):
            return inp[:]
        return [inp]

    def __decode_path(self, path: list[str], content: Obj, include_meta: bool) -> list[Obj]:
        if len(path) == 0:
            return [content] if include_meta else self.__ensure_list(content[KEY_PREFIX])
        index = path[0]
        if index == "*":
            return self.__decode_layer(content, path[1:])
        if index == "**":
            return self.__decode_layer(content, ["**"])
        elif index.isdigit():
            return [self.__ensure_list(content[KEY_PREFIX])[int(index) - 1]]
        return self.__decode_path(path[1:], content[KEY_PREFIX+index], include_meta)
    
    def __decode_layer(self, content: Obj, next: list[str]) -> list:
        res = self.__ensure_list(content.get(KEY_PREFIX, []))
        for key in content:
            if key == KEY_PREFIX or not key.startswith(KEY_PREFIX):
                pass
            else:
                res += self.__decode_path(next, content[key], False)
        return res
            
    def inc_attribute(self, path: list[str], value: int) -> None:
        attribute_name = path[-1]
        assert not attribute_name.startswith("_")
        for obj in self.decode_path(path[:-1]):
            if attribute_name in obj:
                obj[attribute_name] += value
            
    def set_attribute(self, path: list[str], value: int) -> None:
        attribute_name = path[-1]
        assert not attribute_name.startswith("_")
        for obj in self.decode_path(path[:-1]):
            if attribute_name in obj:
                obj[attribute_name] = value

    def get_attribute(self, path: list[str]) -> int:
        attribute_name = path[-1]
        for obj in self.decode_path(path[:-1]):
            if attribute_name in obj:
                return obj[attribute_name]
        return -1

    def reset_counter(self, path: list[str]) -> None:
        cws = self.decode_path(path)
        for cw in cws:
            if "current" in cw and "total" in cw:
                cw["current"] = cw["total"]

    def logistics_phase(self) -> list[tuple[str, str]]:
        res = []
        for cw in self.counters:
            if cw[KEY_PREFIX]["current"] > 0:
                cw[KEY_PREFIX]["current"] -= 1
            if cw[KEY_PREFIX]["current"] == 0:
                res.append((self.name, cw["_name"]))
        return res

    def save(self) -> dict:
        return {
            "name": self.name,
            "content": self.content
        }

    @classmethod
    def load(cls, save_dict: dict):
        res = cls(save_dict["name"], {})
        res.content = save_dict["content"]
        return res
   