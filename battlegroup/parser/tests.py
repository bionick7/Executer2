import numpy as np
from battlegroup.parser.parser import Parser

TESTING_INPUT = """
        open()
        bg1 := BREAKWATER :: LOYAL_GUARDIAN :: DEN_MOTHER :: BROTHERS_IN_ARMS :: ALBEDO_CAVALIER
        bg1.e2.w1.hp -= 1
        bg1.**.hp -= (-2d6 + 5)
        bg1.*.hp -= 5#(-2d6 + 5) & 3
        p1.e2.w1.hp = R
        bg1.e2 => bg2
        bg1.** ?? 0::5
""".split("\n")[1:-1]

def test_pass(parser: Parser, query: str) -> None:
    parser.parse_command(query)
    assert not parser.has_error(), parser.get_error()

def test_dice_equivalent(parser: Parser, *args) -> None:
    np.random.seed(0)
    root0 = parser.parse_dice(args[0])
    assert not parser.has_error(), parser.get_error()
    assert root0 is not None, f"Not a valid dice {args[0]}"
    res0 = root0.evaluate()
    for arg in args[1:]:
        np.random.seed(0)
        root = parser.parse_dice(arg)
        assert not parser.has_error(), parser.get_error()
        assert root is not None, f"Not a valid dice {arg}"
        res = root.evaluate()
        assert res.shape == res0.shape
        assert (res == res0).all()

def test_dice_fail(parser: Parser, query: str) -> None:
    # TODO: disable logging
    root = parser.parse_dice(query)
    assert parser.has_error(), f"Expression \"{query}\" is valid, but should fail"
    while parser.has_error():
        parser.get_error()  # To ensure future tests work

def tests():
    parser = Parser()

    assert len(parser.tokenise("BREAKWATER :: LOYAL-GUARDIAN :: DEN-MOTHER :: BROTHERS-IN-ARMS :: ALBEDO-CAVALIER")) == 9
    assert len(parser.tokenise("1d20 + M(2#1d6)")) == 8

    for q in TESTING_INPUT:
        test_pass(parser, q)

    test_pass(parser, "** => 1d20 + M(2#1d6) :: a.b.c.d :: 5d80 & 3#5")

    test_dice_equivalent(parser, "1d100", "1d100")
    test_dice_equivalent(parser, "(5# 1) + 2", "5# 1 + 2")
    test_dice_equivalent(parser, "5# (3#1)", "(3#5) #1")
    test_dice_equivalent(parser, "15#1", "(3#5) #1")
    test_dice_equivalent(parser, "1*-2", "0-2", "-2")
    test_dice_fail(parser, "*2")
    test_dice_fail(parser, "1 + ((1 + 2))) * 3 + (4 + 4")

    print("All tests passed")

if __name__ == '__main__':
    tests()
