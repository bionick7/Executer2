import time
import sys

from typing import Callable, Any

from implementation.battlegroup_impl import *
from implementation.battlegroup_output import *
from implementation.dice_impl import tokenise
from message_processing import client, data, get_dm_channel

#D = data["bg_data"]  # TODO
current_battle = BGBattle()

def fetch(args, default: Any) -> Any:
    if len(args) == 0:
        return default
    return args.pop(0)

def bg_cmd(battle: BGBattle, cmd: str, *args, **kwargs) -> None:
    args = list(args)
    if cmd == "open":
        battle.open(kwargs.get("author", None), "")
    elif cmd == "close":
        battle.close()
    elif cmd == "add":
        battle.add_npc(fetch(args, ""), fetch(args, ""))
    elif cmd == "rm":
        battle.reassign_escort(fetch(args, ""))
    elif cmd == "reassign":
        battle.reassign_escort(fetch(args, ""), fetch(args, ""))
    elif cmd == "set":
        path = fetch(args, "")
        battle.check_path_valid(path, True)
        battle.set_attribute(path, fetch(args, "1"))
    elif cmd == "dmg":
        path = fetch(args, "")
        dmg = int(fetch(args, "0"))
        battle.check_path_valid(path)
        battle.ship_dmg(path, dmg)
    elif cmd == "area_dmg":
        fleet_name = fetch(args, "")
        dmg = int(fetch(args, "0"))
        battle.area_dmg(fleet_name, dmg)
    elif cmd == "load":
        if not battle.opened:
            battle.open(kwargs.get("author", None), "")
        battle.load_from(fetch(args, "save/temp"))
    elif cmd == "save":
        battle.save_to(fetch(args, "save/temp"))
    elif cmd == "turn":
        battle.logistics_phase()
    elif cmd == "show":
        battle.get_player_rapport()
    elif cmd == "gm":
        fleet_name = fetch(args, "")
        if fleet_name != "":
            battle.get_gm_detail(fleet_name)
        else:
            battle.get_gm_rapport()

def bg_console(cmd: str, *args, **kwargs):
    global current_battle
    if not current_battle.opened and cmd not in ["open", "load"]:
        print(acm("Out of combat right now"))
        return

    bg_cmd(current_battle, cmd.lower(), *args, **kwargs)

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

def console_application():
    cmds = """
    set bg1.e2.w1 hp -1
    set bg1.** hp (-2d6 + 5)
    set bg1.* hp 5x(-2d6 + 5) & 3
    set p1.e2.w1 hp -10
    what bg1.** 0-5
    """.split("\n")[1:-1]
    while True:
        #inp = input(">//[$USR]:: ")
        inp = cmds.pop(0)
        print(tokenise(inp))
        args = inp.split(" ")
        if args[0].lower() == "exit":
            return
        try:
            bg_console(*args)
        except Exception as e:
            print(e, file=sys.stderr)


if __name__ == "__main__":
    console_application()
