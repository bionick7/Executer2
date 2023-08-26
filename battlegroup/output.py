from datetime import datetime
import typing

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
    res = f"[W]{len(w['.'])}x {w['_name'].upper()}"
    if gm:
        res += f" [{w['_range']}] " + "|".join(str(x['hp']) for x in w['.'])
    if all(x['hp'] <= 0 for x in w['.']):
        res = corrupted(res)
    return res + "\n"

def format_charge_counter(charge_object: dict[str, typing.Any], indent: str="") -> str:
    name = charge_object["_name"].upper()
    value = charge_object["."]["current"]
    if value == 0:
        return indent + f"!!! {name}: READY !!!\n"
    return indent + f"({name}: {value})\n"

def format_counter(name: str, value: int, indent: str="") -> str:
    if name[0] not in "._+0&" and name not in ["lockon", "hp", "max_hp"] and value != 0:
        return indent + f"({name.upper()}: {value})\n"
    return ""

def format_bg(bg, gm: bool) -> str:
    res = f"{bg.name.upper()} :: "
    capital = bg.content
    capital_wings = [v for k, v in bg.content.items() if k.startswith(".w")]
    capital_charges = [v for k, v in bg.content.items() if k.startswith(".c")]
    cap_txt = f"{capital['_name'].upper()}"
    if gm:
        cap_txt += f" Def: {capital['_defense']} " + "".join([f"+{x}" for x in capital.get('+defense', [])])
        cap_txt += f"I: {capital['_interdiction']}" + "".join([f"+{x}" for x in capital.get('+interdiction', [])])
        cap_txt += f" - {capital['.']['hp']}/{capital['.']['max_hp']}"
    for _ in range(capital['.']['lockon']):
        cap_txt = f">{cap_txt}<"
    if capital['.']['hp'] <= 0:
        cap_txt = corrupted(cap_txt)
    res += cap_txt + "\n"
    if gm:
        indent = "     |  "
        for name, value in *capital.items(), *capital["."].items():
            res += format_counter(name, value, indent)
        for charge_index, charge_object in enumerate(capital_charges):
            border = f"c{charge_index+1:2<}   "
            res += border + format_charge_counter(charge_object, "|  ")
    for wing_index, wing_object in enumerate(capital_wings):
        border = f"w{wing_index+1:2<}   |" if gm else ""
        res += border + "    " + format_wing(wing_object, gm)
    for escort_index, escort in enumerate(bg.escorts):
        escort_wings = [v for k, v in escort.items() if k.startswith(".w")]
        escort_charges = [v for k, v in escort.items() if k.startswith(".c")]
        escort_txt = f"e{escort_index+1:2<}   |" if gm else ""
        if escort['_is_template']:
            escort_txt += f"    {escort['_name'].upper()}"
        else:
            escort_txt += f"    {len(escort['.'])}x {escort['_name'].upper()}"
            if gm:
                escort_txt += f" Def:{escort['_defense']}"
                escort_txt += " - "
                escort_txt += "|".join(str(x['hp']) for x in escort['.'])
        escort_txt += "\n"
        if gm and escort.get(".", []) != []:
            indent = "     |      "
            for charge_index, charge_object in enumerate(escort_charges):
                border = f"e{escort_index+1:1}.c{charge_index+1:1}"
                escort_txt += border + format_charge_counter(charge_object, "|      ")
            for i, ship in enumerate(escort['.']):
                for name, value in ship.items():
                    escort_txt += format_counter(name, value, indent + f"({i})")
        for _ in range(sum(x['lockon'] for x in escort['.'])):
            escort_txt = f">{escort_txt}<"
        for wing_index, wing_object in enumerate(escort_wings):
            border = f"e{escort_index+1:1}.w{wing_index+1:1}|" if gm else ""
            escort_txt += border + " "*8 + format_wing(wing_object, gm)
        if all(x['hp'] <= 0 for x in escort['.']) and not escort['_is_template']:
            escort_txt = corrupted(escort_txt)
        res += escort_txt
    return res

if __name__ == "__main__":
    import battlegroup_impl
    battle = battlegroup_impl.BGBattle()
    battle.load_from("temp")
    print(battle.get_player_rapport())
    print(battle.get_gm_rapport())