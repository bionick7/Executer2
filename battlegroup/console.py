import time
import sys
import numpy as np

from typing import Callable, Any

from battlegroup.battlegroup_impl import *
from battlegroup.output import *
from battlegroup.parser.parser import Parser, SyntaxNode, EvalResult
from battlegroup.parser.tests import TESTING_INPUT
from message_processing import client, data, get_dm_channel

#D = data["bg_data"]  # TODO
current_battle = BGBattle()

parser = Parser()

def bg_cmd(path: list[str], battle: BGBattle, cmd: str, args: list, author: str) -> None:
    args = list(args)
    if cmd == "open":
        battle.open(author, "")
    elif cmd == "close":
        battle.close()
    elif cmd == "add":
        capital = fetch_id(args, "")
        escorts = []
        while len(args) > 0:
            escorts.append(fetch_id(args))
        battle.add_npc(capital, escorts)
    elif cmd == "rm":
        battle.reassign_escort(fetch_id(args))
    elif cmd == "reassign":
        battle.reassign_escort(fetch_id(args), fetch_id(args))
    elif cmd == "set":
        battle.set_attribute(path, fetch_int(args))
        battle.get_gm_detail(path[0])
    elif cmd == "dmg":
        battle.inc_attribute([*path, "dmg"], -fetch_int(args))
        battle.get_gm_detail(path[0])
    elif cmd == "area_dmg":
        bg = fetch_id(args)
        battle.inc_attribute([bg, "**", "dmg"], -fetch_int(args))
        battle.get_gm_detail(bg)
    elif cmd == "load":
        if not battle.opened:
            battle.open(author, "")
        battle.load_from(fetch_id(args, "save/temp"))  # TODO: this might get a problem
    elif cmd == "save":
        battle.save_to(fetch_id(args, "save/temp"))
    elif cmd == "turn":
        battle.logistics_phase()
    elif cmd == "show":
        battle.get_player_rapport()
    elif cmd == "gm":
        fleet_name = fetch_id(args, "")
        if fleet_name != "":
            battle.get_gm_detail(fleet_name)
        else:
            battle.get_gm_rapport()

def bg_console(path: list[str], cmd: str, args):
    global current_battle
    if not current_battle.opened and cmd not in ["open", "load"]:
        print(acm("Out of combat right now"))
        return

    bg_cmd(path, current_battle, cmd, args, "USR")

    is_error = len(current_battle.error_queue) > 0
    while len(current_battle.error_queue) > 0:
        error = current_battle.error_queue.pop(0)
        print(acm(error, "$ERR"))
    if is_error:
        return
    while len(current_battle.message_queue) > 0:
        msg = current_battle.message_queue.pop(0)
        if msg.startswith("$WAIT:"):
            t = float(msg[6:])
            time.sleep(t)
        elif msg.startswith("$LONG"):
            print(acm_long_embed(msg[5:]))
        else:
            print(acm(msg))

def fetch_int(args: list, default: int=0) -> int:
    # Modifies list
    if len(args) == 0: return default
    x = args.pop(0)
    if isinstance(x, np.ndarray) and len(x) > 0:
        return int(x[0])
    if isinstance(x, (int, float)):
        return int(x)
    if isinstance(x, (SyntaxNode)):
        fetch_int([x.evaluate()], default)
    return default

def fetch_array(args: list, count: int, default: list[int]=[]) -> list[int]:
    # Modifies list
    if len(args) == 0: return default
    x = args.pop(0)
    if isinstance(x, np.ndarray):
        if len(x) > count: return list(map(int, x[:count]))
        if len(x) < count: return list(map(int, x)) + [0] * (count - len(x))
        return list(map(int, x))
    if isinstance(x, (int, float)):
        return [int(x)] * count
    if isinstance(x, (SyntaxNode)):
        fetch_array([x.evaluate()], count, default)
    return default

def fetch_path(args: list, default: list[str]=[]) -> list[str]:
    # Modifies list
    if len(args) == 0: return default
    x = args.pop(0)
    if isinstance(x, list):
        return list(map(str, x))
    return default

def fetch_id(args: list, default: str="") -> str:
    # Modifies list
    if len(args) == 0: return default
    x = args.pop(0)
    if isinstance(x, str):
        return x
    return default

def get_input():
    while True:
        inp = input(">//[$USR]:: ")
        if inp == "exit":
            break
        yield inp

def console_application(input_gen):
    for inp in input_gen:
        path, cmd, args = parser.parse_command(inp)
        if not parser.has_error():
            bg_console(path, cmd, args)
        while parser.has_error():
            print(parser.get_error())


if __name__ == "__main__":
    #console_application(get_input())
    console_application(TESTING_INPUT)
