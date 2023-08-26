from battlegroup.battlegroup_impl import BGBattle
import unittest

class TestImplementation(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.battle = BGBattle()

    def test_implementation(self):
        self.battle.open("Threading the needle", "LOCAL")
        self.battle.add_npc("BREAKWATER", ["LOYAL-GUARDIAN", "DEN-MOTHER", "BROTHERS-IN-ARMS"], "alpha")
        self.battle.add_npc("PALADIN", ["ROUGHNECKS"], "bg2")
        self.battle.add_npc("HIGHLINE", ["BROTHERS-IN-ARMS", "STARFIELD-FURIES"], "bg3")
        self.battle.add_npc("CORSAIR", ["ROUGHNECKS"], "bg4")
        self.battle.save_to("temp")

        self.assertEqual(len(self.battle.error_queue), 0, "Initializetion error")
        self.assertTrue(self.battle.check_path_valid("bg2".split(".")))
        self.assertTrue(self.battle.check_path_valid("bg3.e2.w3".split(".")))
        self.assertTrue(self.battle.check_path_valid("bg4.e1.2".split(".")))
        self.assertTrue(self.battle.check_path_valid("alpha.e1.1".split(".")))
        self.assertFalse(self.battle.check_path_valid("alpha.e1.2".split(".")))
        self.assertFalse(self.battle.check_path_valid("alpha.e1.-1".split(".")))
        self.assertFalse(self.battle.check_path_valid("bg1.e1.2".split(".")))

        self.battle.set_attribute("bg3.e2.w3.dmg".split("."), 1)
        self.battle.set_attribute("bg3.e2.w3.2.dmg".split("."), 2)
        self.battle.inc_attribute("bg3.e2.w3.dmg".split("."), 1)
        self.battle.inc_attribute("bg3.e2.w3.2.dmg".split("."), 2)
        self.battle.reassign_escort("bg3.e2".split("."), "bg2")
        self.battle.reassign_escort("bg3.e1".split("."), "")
        self.battle.reassign_escort("bg4.e1".split("."), "bg2")
        
        self.assertEqual(len(list(self.battle.npcs["bg2"].escorts)), 3)
        self.assertEqual(len(list(self.battle.npcs["bg3"].escorts)), 0)

        d1 = self.battle.__dict__
        self.battle.save_to("temp")
        self.battle.load_from("temp")
        self.assertEqual(d1, self.battle.__dict__)