import time
import sys
import numpy as np

from typing import Callable, Any

from battlegroup.battlegroup_impl import *
from battlegroup.output import *
from battlegroup.parser.parser import Parser, SyntaxNode, EvalResult
from message_processing import client, data, get_dm_channel

UNREACHABLE: int = -2**32

TESTING_INPUT = """
        open()
        bg1 := BREAKWATER :: LOYAL-GUARDIAN :: DEN-MOTHER :: BROTHERS-IN-ARMS
        bg2 := STARKILLER
        bg1.e2.w1.hp -= 1
        bg1.**.hp -= (-2d6 + 5)
        bg1.*.hp -= 5#(-2d6 + 5) & 3
        p1.e2.w1.hp = R
        bg1.e2 => bg2
        bg1.** ?? 0::5
        turn()
""".split("\n")[1:-1]

#D = data["bg_data"]  # TODO
current_battle = BGBattle()

parser = Parser()


class ArgumentList:
    def __init__(self, p_args: list) -> None:
        self.args = p_args
        self._i = 0

    def __repr__(self) -> str:
        return ", ".join(map(str, self.args)) + f"[{self._i}]"

    def back(self) -> None:
        self._i = max(self._i - 1, 0)
        
    def reset(self) -> None:
        self._i = 0

    def can_fetch(self) -> bool:
        return self._i < len(self.args)

    def fetch_raw(self) -> str:
        self._i += 1
        return self.args[self._i - 1]

    @staticmethod
    def _get_as_int(x, default: int) -> int:
        if isinstance(x, np.ndarray) and len(x) > 0:
            return int(x[0])
        if isinstance(x, (int, float)):
            return int(x)
        return default

    def fetch_int(self, default: int=0) -> int:
        if not self.can_fetch(): return default
        x = self.fetch_raw()
        if isinstance(x, (SyntaxNode)):
            return self._get_as_int(x.evaluate(), default)
        return self._get_as_int(x, default)

    @staticmethod
    def _get_as_arr(x, count: int, default: list[int]) -> list[int]:
        if isinstance(x, np.ndarray):
            if len(x) > count: return list(map(int, x[:count]))
            if len(x) < count: return list(map(int, x)) + [0] * (count - len(x))
            return list(map(int, x))
        if isinstance(x, (int, float)):
            return [int(x)] * count
        return default

    def fetch_array(self, count: int, default: list[int]=[]) -> list[int]:
        if not self.can_fetch(): return default
        x = self.fetch_raw()
        if isinstance(x, (SyntaxNode)):
            return self._get_as_arr(x.evaluate(), count, default)
        return self._get_as_arr(x, count, default)

    def fetch_path(self, default: list[str]=[]) -> list[str]:
        if not self.can_fetch(): return default
        x = self.fetch_raw()
        if isinstance(x, list):
            return list(map(str, x))
        return default

    def fetch_id(self, default: str="") -> str:
        if not self.can_fetch(): return default
        x = self.fetch_raw()
        if isinstance(x, str):
            return x
        return default

def bg_cmd(path: list[str], battle: BGBattle, cmd: str, args: ArgumentList, author: str) -> None:
    if cmd == "open":
        battle.open(author, "")
    elif cmd == "close":
        battle.close()
    elif cmd == "load":
        if not battle.opened:
            battle.open(author, "")
        battle.datamanager.load_from(args.fetch_id("save/temp"))  # TODO: this might get a problem
        battle.sync()
    elif cmd == "save":
        battle.datamanager.save_to(args.fetch_id("save/temp"))
    elif cmd == "turn":
        battle.logistics_phase()
    elif cmd == "show":
        battle.get_player_rapport()
    elif cmd == "gm":
        fleet_name = args.fetch_id("")
        if fleet_name != "":
            battle.get_gm_detail(fleet_name)
        else:
            battle.get_gm_rapport()
    
    elif cmd == ":=":
        flagship = args.fetch_id()
        escorts = []
        while args.can_fetch(): escorts.append(args.fetch_id())
        battle.add_npc(flagship, escorts, path[0])
    elif cmd == "=":
        rhs = args.fetch_raw()
        if isinstance(rhs, SyntaxNode):
            battle.set_attribute(path, args._get_as_int(rhs, battle.get_attribute(path)))
        elif isinstance(rhs, list) and all([isinstance(x, str) for x in rhs]):
            battle.set_attribute(path, battle.get_attribute(rhs))
        elif rhs == "R" or rhs == "r":
            battle.reset_counter(path)
    elif cmd == "+=":
        battle.inc_attribute(path, args.fetch_int())
    elif cmd == "-=":
        battle.inc_attribute(path, -args.fetch_int())
    elif cmd == "=>":
        battle.reassign_escort(path, args.fetch_id())
    elif cmd == "??":
        fleet_name = path[0]
        if fleet_name == "**":
            if args.can_fetch() and isinstance((x := args.fetch_raw()), SyntaxNode):
                print(x.string_evaluate())
            else:
                battle.get_gm_rapport()
        else:
            battle.get_gm_detail(fleet_name)

def bg_console(path: list[str], cmd: str, args: list[str]):
    global current_battle
    if not current_battle.opened and cmd not in ["open", "load"]:
        print(acm("Out of combat right now"))
        return

    bg_cmd(path, current_battle, cmd, ArgumentList(args), "USR")

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

def get_input():
    while True:
        inp = input(">//[$USR]:: ")
        if inp == "exit":
            break
        elif inp == "help":
            print("Not Implemented")
        yield inp

def sim_input(input_list: list[str]):
    for inp in input_list:
        print(">//[$USR]:: " + inp)
        if inp == "exit":
            break
        elif inp == "help":
            print("Not Implemented")
        yield inp

def console_application(input_gen):
    for i, inp in enumerate(input_gen):
        try:
            path, cmd, args = parser.parse_command(inp)
            if not parser.has_error():
                bg_console(path, cmd, args)
        except Exception as e:
            print(f"Uncaught python exception: {e}")
        while parser.has_error():
            print(parser.get_error())


if __name__ == "__main__":
    tst1 = [
        'open',
        'bg1 := Starkiller :: Brothers-in-arms',
        'turn',
        'turn',
        'bg1.e1.c1 = R',
        'bg1.c1.current = bg1.c1.total',
        '??',
        'turn',
        '** = R',
        '??',
    ]
    tst2 = [
        'open',
        'bg1 := Starkiller :: Brothers-in-arms',
        'bg1 ?? 0 :: 5'
    ]
    #console_application(get_input())
    console_application(sim_input(tst2))
