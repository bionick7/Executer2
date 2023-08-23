import numpy as np
from battlegroup_parser import Parser, tokenise

last_dice_rolls = {}

def interprete_roll(inp: str, author_id: int=-1) -> str:
    try:
        root = Parser(tokenise(inp)).parse_roll()
    except ValueError as e:
        return str(e)
    return root.string_evaluate()


def test_equivalent(*args) -> None:
    np.random.seed(0)
    root0 = Parser(tokenise(args[0])).parse_roll()
    res0 = root0.evaluate()
    for arg in args[1:]:
        np.random.seed(0)
        root = Parser(tokenise(arg)).parse_roll()
        res = root.evaluate()
        assert res.shape == res0.shape
        assert (res == res0).all()

def test_fail(query) -> None:
    try:
        root = Parser(tokenise(query)).parse_roll()
        res = root.evaluate()
    except Exception:
        return
    else:
        raise Exception("Did not fail")

def tests():
    test_equivalent("1d100", "1d100")
    test_equivalent("(5# 1) + 2", "5# 1 + 2")
    test_equivalent("5# (3#1)", "(3#5) #1")
    test_equivalent("15#1", "(3#5) #1")
    test_equivalent("1*-2", "0-2", "-2")
    test_fail("*2")
    test_fail("1 + ((1 + 2))) * 3 + (4 + 4")
    print("All tests passed")

if __name__ == '__main__':
    print(tokenise("BREAKWATER ::: (LOYAL_GUARDIAN, DEN_MOTHER, BROTHERS_IN_ARMS, ALBEDO_CAVALIER)"))
    print(tokenise("1d20 + M(2#1d6)"))
    print(interprete_roll("3#(1d20 + M(2#1d6) + 4)", -1), "\n==========================")
    print(interprete_roll("2#3 & 0*-2 & 1 + 2*(3-5)/2", -1), "\n==========================")
    print(interprete_roll("m(1d6#1d6)", -1), "\n==========================")
    tests()
