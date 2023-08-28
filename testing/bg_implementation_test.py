import unittest

import dictdiffer
from battlegroup.battlegroup_impl import BGBattle
from battlegroup.console import bg_cmd, ArgumentList

class TestImplementation(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.battle = BGBattle()

    def compare_dict(self, d1: dict, d2: dict):
        diff = list(dictdiffer.diff(d1, d2))
        self.assertEqual(diff, [])

    def cmd(self, cmd: str, path: str = "**", args: list = []):
        bg_cmd(path.split("."), self.battle, cmd, ArgumentList(args), "tester")
        
    def _assert_attribute(self, path: str, compare: int):
        self.assertEqual(self.battle.get_attribute(path.split(".")), compare)

    def test_implementation(self):
        self.battle.open("Threading the needle", "LOCAL")
        self.battle.add_npc("BREAKWATER", ["LOYAL-GUARDIAN", "DEN-MOTHER", "BROTHERS-IN-ARMS"], "alpha")
        self.battle.add_npc("PALADIN", ["ROUGHNECKS"], "bg2")
        self.battle.add_npc("HIGHLINE", ["BROTHERS-IN-ARMS", "STARFIELD-FURIES"], "bg3")
        self.battle.add_npc("CORSAIR", ["ROUGHNECKS"], "bg4")
        self.battle.datamanager.save_to("temp")

        self.assertEqual(len(self.battle.error_queue), 0, "Initializetion error")
        self.assertTrue(self.battle.check_path_valid("bg2".split(".")))
        self.assertTrue(self.battle.check_path_valid("bg3.e2.w3".split(".")))
        self.assertTrue(self.battle.check_path_valid("bg4.e1.2".split(".")))
        self.assertTrue(self.battle.check_path_valid("alpha.e1.1".split(".")))
        self.assertFalse(self.battle.check_path_valid("alpha.e1.2".split(".")))
        self.assertFalse(self.battle.check_path_valid("alpha.e1.-1".split(".")))
        self.assertFalse(self.battle.check_path_valid("bg1.e1.2".split(".")))

        self.battle.set_attribute("bg3.e2.w3.hp".split("."), 1)
        self.battle.set_attribute("bg3.e2.w3.2.hp".split("."), 2)
        self.assertEqual(self.battle.get_attribute("bg3.e2.w3.hp".split(".")), 1)
        self.assertEqual(self.battle.get_attribute("bg3.e2.w3.2.hp".split(".")), 2)
        self.battle.inc_attribute("bg3.e2.w3.hp".split("."), 1)
        self.battle.inc_attribute("bg3.e2.w3.2.hp".split("."), 1)
        self.assertEqual(self.battle.get_attribute("bg3.e2.w3.1.hp".split(".")), 2)
        self.assertEqual(self.battle.get_attribute("bg3.e2.w3.2.hp".split(".")), 4)
        self.battle.reassign_escort("bg3.e2".split("."), "bg2")
        self.battle.reassign_escort("bg3.e1".split("."), "")
        self.battle.reassign_escort("bg4.e1".split("."), "bg2")
        
        self.assertEqual(len(list(self.battle.npcs["bg2"].escorts)), 3)
        self.assertEqual(len(list(self.battle.npcs["bg3"].escorts)), 0)

        d1 = dictdiffer.deepcopy(self.battle.get_data().copy())
        self.battle.datamanager.save_to("temp")
        self.battle.datamanager.load_from("temp")
        self.battle.sync()
        self.compare_dict(d1, self.battle.get_data())

    def test_history(self):
        self.battle.datamanager.reset_history()
        self.battle.open("Threading the needle", "LOCAL")
        self.battle.add_npc("BREAKWATER", ["LOYAL-GUARDIAN", "DEN-MOTHER", "BROTHERS-IN-ARMS"], "alpha")
        self.battle.add_npc("PALADIN", ["ROUGHNECKS"], "bg2")
        self.battle.add_npc("HIGHLINE", ["BROTHERS-IN-ARMS", "STARFIELD-FURIES"], "bg3")
        self.battle.add_npc("CORSAIR", ["ROUGHNECKS"], "bg4")

        d1 = dictdiffer.deepcopy(self.battle.get_data())
        
        self.battle.inc_attribute("bg3.e2.w3.hp".split("."), -1)
        self.battle.inc_attribute("bg3.e2.w3.2.hp".split("."), -2)

        d2 = dictdiffer.deepcopy(self.battle.get_data())

        self.battle.datamanager.undo()
        self.battle.datamanager.undo()
        self.battle.sync()

        self.compare_dict(self.battle.get_data(), d1)
        
        self.battle.datamanager.redo()
        self.battle.datamanager.redo()
        self.battle.sync()

        self.compare_dict(self.battle.get_data(), d2)

    def test_charges(self):
        self.cmd("open")
        self.cmd(":=", "alpha", ["Starkiller", "Brothers-in-arms"])
        self.cmd("turn")
        self.cmd("turn")
        self._assert_attribute("alpha.c1.current", 0)
        self._assert_attribute("alpha.e1.c1.current", 0)
        self.cmd("=", "alpha.c1", ["R"])
        self.cmd("=", "alpha.e1.c1.current", ["alpha.e1.c1.total".split(".")])
        self._assert_attribute("alpha.c1.current", 2)
        self._assert_attribute("alpha.e1.c1.current", 2)
        
    def test_sync(self):
        battle2 = BGBattle()
        self.cmd("open")
        self.cmd(":=", "alpha", ["Starkiller", "Battlethreads"])
        self.cmd("connect", "**", ["test_watch"])

        d1 = dictdiffer.deepcopy(self.battle.get_data())
        
        bg_cmd(["**"], battle2, "connect", ArgumentList(["test_watch"]), "tester")
        battle2.datamanager.watch()
        battle2.sync()
        self.compare_dict(d1, battle2.get_data())

    def _assert_available_guns(self, fleetname: str, max_range: int, min_range: int, compare: int) -> None:
        resdict = [bg.get_abilities(max_range, min_range) for bg in self.battle._get_npcs(fleetname)]
        available_guns = 0
        for bg in resdict:
            for abilities in bg.values():
                for ability in abilities:
                    if ability["type"] == "gun":
                        available_guns += 1
        self.assertEqual(available_guns, compare)

    def test_ranges(self):
        self.cmd("open")
        self.cmd(":=", "alpha", ["Starkiller", "Brothers-in-arms"]) # 5-3 & 4-1
        self.cmd("??", "alpha", )
        self._assert_available_guns("alpha", 5, 0, 2)
        self._assert_available_guns("alpha", 3, 0, 2)
        self._assert_available_guns("alpha", 2, 0, 1)
        self._assert_available_guns("alpha", 7, 6, 0)
        self._assert_available_guns("alpha", 5, 5, 1)
        self._assert_available_guns("alpha", 4, 4, 2)

if __name__ == "__main__":
    unittest.main()