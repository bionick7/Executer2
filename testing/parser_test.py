import unittest
import numpy as np

from battlegroup.parser.parser import Parser

class TestParser(unittest.TestCase):
    def  __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.parser = Parser()

    def _test_pass(self, query: str) -> None:
        self.parser.parse_command(query)
        self.assertFalse(self.parser.has_error(), self.parser.get_error())
        
    def _test_ast(self, query: str, test_path: list[str], test_res: str, test_args: list) -> None:
        act_path, act_res, act_args = self.parser.parse_command(query)
        self.assertFalse(self.parser.has_error(), self.parser.get_error())
        self.assertEqual(test_path, act_path)
        self.assertEqual(test_res, act_res)
        self.assertEqual(test_args, act_args)

    def _test_dice_equivalent(self, *args) -> None:
        np.random.seed(0)
        root0 = self.parser.parse_dice(args[0])
        self.assertFalse(self.parser.has_error(), self.parser.get_error())
        self.assertIsNotNone(root0, f"Not a valid dice {args[0]}")
        if root0 is None: return
        res0 = root0.evaluate()
        for arg in args[1:]:
            np.random.seed(0)
            root = self.parser.parse_dice(arg)
            self.assertFalse(self.parser.has_error(), self.parser.get_error())
            self.assertIsNotNone(root, f"Not a valid dice {arg}")
            if root is None: return
            res = root.evaluate()
            assert res.shape == res0.shape
            assert (res == res0).all()

    def _test_dice_fail(self, query: str) -> None:
        # TODO: disable logging
        root = self.parser.parse_dice(query)
        self.assertTrue(self.parser.has_error(), f"Expression \"{query}\" is valid, but should fail")
        while self.parser.has_error():
            self.parser.get_error()  # To ensure future tests work

    def test_parser(self) -> None:
        self.assertEqual(len(self.parser.tokenise("BREAKWATER :: LOYAL-GUARDIAN :: DEN-MOTHER :: BROTHERS-IN-ARMS :: ALBEDO-CAVALIER")), 9)
        self.assertEqual(len(self.parser.tokenise("1d20 + M(2#1d6)")), 8)
        self.assertEqual(len(self.parser.tokenise("1d20 + M(2#1d6) // a comment ... ** => 1d20 + M(2#1d6) :: a.b.c.d :: 5d80 & 3#5")), 8)

        self._test_pass('open()')
        self._test_pass('//load("abc/def")')
        self._test_pass('** ?? 1d20')
        self._test_pass('??(1d20 :: bg1.e2)')
        self._test_pass('bg1 ??')
        self._test_pass('bg1 := BREAKWATER :: LOYAL_GUARDIAN :: DEN_MOTHER :: BROTHERS_IN_ARMS :: ALBEDO_CAVALIER')
        self._test_pass('bg1.e2.w1.hp -= 1')
        self._test_pass('bg1.**.hp -= (-2d6 + 5)')
        self._test_pass('bg1.*.hp -= 5#(-2d6 + 5) & 3')
        self._test_pass('p1.e2.w1.hp = R')
        self._test_pass('bg1.e2 => bg2')
        self._test_pass('bg1.** ?? 0::5')
        self._test_pass('** => 1d20 + M(2#1d6) :: a.b.c.d :: 5d80 & 3#5')
        self._test_ast('1.2.3 => ', ["1", "2", "3"], "=>", [])


    def test_dicerolls(self) -> None:
        self._test_dice_equivalent("1d100", "1d100")
        self._test_dice_equivalent("(5# 1) + 2", "5# 1 + 2")
        self._test_dice_equivalent("5# (3#1)", "(3#5) #1")
        self._test_dice_equivalent("15#1", "(3#5) #1")
        self._test_dice_equivalent("1*-2", "0-2", "-2")
        self._test_dice_fail("*2")
        self._test_dice_fail("1 + ((1 + 2))) * 3 + (4 + 4")
