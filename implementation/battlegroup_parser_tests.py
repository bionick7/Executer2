import numpy as np
from implementation.battlegroup_parser import Parser, tokenise



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
    parser = Parser(tokenise(query))
    root = parser.parse_roll()
    res = root.evaluate()
    assert parser.has_error()

def tests():
    assert len(tokenise("BREAKWATER ::: (LOYAL_GUARDIAN, DEN_MOTHER, BROTHERS_IN_ARMS, ALBEDO_CAVALIER)")) == 11
    assert len(tokenise("1d20 + M(2#1d6)")) == 8

    test_equivalent("1d100", "1d100")
    test_equivalent("(5# 1) + 2", "5# 1 + 2")
    test_equivalent("5# (3#1)", "(3#5) #1")
    test_equivalent("15#1", "(3#5) #1")
    test_equivalent("1*-2", "0-2", "-2")
    test_fail("*2")
    test_fail("1 + ((1 + 2))) * 3 + (4 + 4")

    parser = Parser(tokenise("1d20 + M(2#1d6) a.b.c.d 5d80 & 3#5"))
    parser.parse_roll()
    parser.parse_path()
    parser.parse_roll()
    assert not parser.has_error(), parser.get_error()

    print("All tests passed")

if __name__ == '__main__':
    tests()
