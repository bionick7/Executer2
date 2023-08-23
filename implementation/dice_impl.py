import re
import typing
import numpy as np
import numpy.typing as nptyp
from random import Random


from enum import Enum
from typing import List, Dict

EvalResult = typing.Union[nptyp.NDArray[np.int32], nptyp.NDArray[np.float32]]

last_dice_rolls = {}
roll_random = Random()  # Seperate one for testing

HELP_TEXT = """
Syntax:
    a x b: does [b] [a] times, returns array
    a & b: concantenates [b] to [a]
    a +-*/ b: operations on [a] and [b], [a], [b] can be array
    NdM: rolls N M-sided dicea and adds the results
    M(...): maximum between all values
    m(...): minimum between [a] and [b]
    
Order of operations:
    () > */ > +- > x > &

Examples:
    Rolls 1d20, adds the greater one of 2d6, then 4
        1d20 + M(2x1d6) + 4
    Takes the minimum between 2d20 minus a doubled d8 and 5. Does this 5 times
        5xm(2d20 - 1d8*2 & 5)
    Rolls 1d6 1d6 times
        1d6x1d6
    Should return (3, 3, 0, -1)
        2x3 & 0*-2 & 1 + 2*(3-5)/2
"""

class TokenType(Enum):
    BRACKET_OPEN = 0,
    BRACKET_CLOSE = 1,
    WHITESPACE = 2,
    INTEGER = 3,
    IDENTIFIER = 4,
    DICE = 5,
    ADD_OPERATOR = 6,
    SUBTRACT_OPERATOR = 7,
    MULTIPLY_OPERATOR = 8,
    DIVIDE_FLOOR_OPERATOR = 9,
    AND_OPERATOR = 10,
    TIMES_OPERATOR = 11,
    SEPARATOR = 12,
    COMPOSITE = 13,

SINGLE_CHAR_TOKENS = {
    "(": TokenType.BRACKET_OPEN,
    ")": TokenType.BRACKET_CLOSE,
    "+": TokenType.ADD_OPERATOR,
    "-": TokenType.SUBTRACT_OPERATOR,
    "*": TokenType.MULTIPLY_OPERATOR,
    "/": TokenType.DIVIDE_FLOOR_OPERATOR,
    "&": TokenType.AND_OPERATOR,
    "x": TokenType.TIMES_OPERATOR,
    ",": TokenType.SEPARATOR,
    **(dict(zip(map(chr, range(33)), [TokenType.WHITESPACE]*33)))
    # marks all the characters up to 0x20 ([space]) as whitespace
}

OPERATOR_TOKENS = (
    TokenType.ADD_OPERATOR, 
    TokenType.SUBTRACT_OPERATOR, 
    TokenType.MULTIPLY_OPERATOR, 
    TokenType.DIVIDE_FLOOR_OPERATOR, 
    TokenType.AND_OPERATOR, 
    TokenType.TIMES_OPERATOR
)

def get_dice_permutations(p: int, q: int, x: int) -> int:
    """ possibilities that pdq = x"""
    if not (p <= x <= p*q):
        return 0
    if p == 1:
        return 1
    res = 0
    for i in range(1, min(q, x - p + 1)+1):
        res += get_dice_permutations(p-1, q, x-i)
    return res

class Token:
    def __init__(self, p_type: TokenType, *args, **kwargs):
        self.token_type = p_type
        self.result = np.zeros(0, np.int32)
        self.has_result = False
        if p_type == TokenType.INTEGER:
            self.value: int = args[0]
        elif p_type == TokenType.DICE:
            self.number: int = args[0]
            self.sides: int = args[1]
        elif p_type == TokenType.IDENTIFIER:
            self.id_value: str = args[0]

    def _show_recursive(self, indent: str = "") -> str:
        if self.token_type == TokenType.INTEGER:
            return indent + f"{self.value}"
        if self.token_type == TokenType.DICE:
            return indent + f"{self.number}d{self.sides}"
        if self.token_type == TokenType.IDENTIFIER:
            return indent + f"'{self.id_value}'"
        if self.token_type == TokenType.WHITESPACE:
            return "[ ]"
        if self.token_type in SINGLE_CHAR_TOKENS.values():
            return f"[{list(SINGLE_CHAR_TOKENS.keys())[list(SINGLE_CHAR_TOKENS.values()).index(self.token_type)]}]"
        return indent + f"{self.token_type}"

    def _set_result(self, res: EvalResult) -> EvalResult:
        self.result = res
        self.has_result = True
        return res
    
    def __repr__(self):
        return self._show_recursive()
        
    def is_evaluable(self) -> bool:
        return self.token_type in (TokenType.INTEGER, TokenType.DICE, TokenType.COMPOSITE)

    def evaluate(self, modus_op: str="num", times: int=1) -> EvalResult:
        base_arr = np.ones(1, np.int32)
        if self.token_type == TokenType.INTEGER:
            return base_arr * self.value
        if self.token_type == TokenType.DICE:
            if modus_op == "num":
                if not self.has_result:  # Don't re-roll
                    self._set_result(np.random.randint(1, self.sides, self.number, np.int32))
                return base_arr * np.sum(self.result)
            elif modus_op == "min":
                return base_arr * self.number
            elif modus_op == "max":
                return base_arr * self.sides * self.number
        return np.zeros(0, np.int32)

    def string_evaluate(self, modus_op: str="num", times: int=1, index: int=0, indent: str="") -> str:
        if self.token_type == TokenType.INTEGER:
            return str(self.value)
        elif self.token_type == TokenType.DICE:
            if not self.has_result:
                return "Uncalc"
            if len(self.result) == 0:
                return "None"
            elif len(self.result) == 1:
                return f"{self.result[0]}|{self.sides}"
            return f"({' + '.join([str(r) + '|' + str(self.sides) for r in self.result])} = {sum(self.result)})"
        else:
            return ""

    def custom_copy(self):
        args = []
        if self.token_type == TokenType.INTEGER:
            args = [self.value]
        elif self.token_type == TokenType.DICE:
            args = (self.number, self.sides)
        return Token(self.token_type, *args)

    #@classmethod
    #def accumulate(cls, token_list: List):
    #    if len(token_list) == 1:
    #        return token_list[0]
    #    return cls(TokenType.TOKEN_SET, token_list)

class OperatorToken(Token):
    def __init__(self, p_operator: str, *args, **kwargs):
        super().__init__(TokenType.COMPOSITE, *args, **kwargs)
        self.operator = p_operator
        self.lhs: Token = args[0]
        self.rhs: Token = args[1]
        self.rhs_copies = []

    def _show_recursive(self, indent: str = ""):
        return indent +  f"{self.operator}\n" + (
                self.lhs._show_recursive(indent + "  ") + "\n" + 
                self.rhs._show_recursive(indent + "  ")
        )

    def evaluate(self, modus_op: str="num", times: int=1) -> EvalResult:
        if self.has_result:
            return self.result
        
        if self.operator == "x":
            times_n = int(np.sum(self.lhs.evaluate(modus_op, times)))
            self.rhs_copies = [self.rhs.custom_copy() for _ in range(times_n)]
            return self._set_result(np.concatenate([
                c.evaluate(modus_op, times) for c in self.rhs_copies
            ]))
        a, b = self.lhs.evaluate(modus_op, times), self.rhs.evaluate(modus_op, times)
        if self.operator == "+":
            return self._set_result(a + b)
        if self.operator == "-":
            return self._set_result(a - b)
        if self.operator == "*":
            return self._set_result(a * b)
        if self.operator == "/":
            return self._set_result(a // b)
        if self.operator == "&":
            return np.concatenate((a, b))
        raise Exception(f"Invalid operator: {self.operator}")
    
    def string_evaluate(self, modus_op: str="num", times: int=1, index: int=0, indent: str="") -> str:
        res = self.evaluate(modus_op, times)  # Needs to set internal state
        if self.operator == "x":
            return (
                    f"(" + f"".join(["\n" + indent + "  " + c.string_evaluate(modus_op, times, index, indent + "  ") for c in self.rhs_copies])
                    + f"\n{indent})"
            )
        if self.operator == "&":
            return (
                f"({self.lhs.string_evaluate(modus_op, times, index, indent + '  ')}"
                f"\n{indent}&\n{indent}{self.rhs.string_evaluate(modus_op, times, index, indent + '  ')}"
                f"\n{indent})"
            )
        res_str = str(res[0]) if len(res) == 1 else str(res)
        return f"({self.lhs.string_evaluate(modus_op, times, index, indent)} {self.operator} {self.rhs.string_evaluate(modus_op, times, index, indent)} = {res_str})"
    
    def custom_copy(self):
        return OperatorToken(self.operator, self.lhs.custom_copy(), self.rhs.custom_copy())
    
    @classmethod
    def from_tokens(cls, lhs: Token, operand: Token, rhs: Token):
        operator = {
            TokenType.ADD_OPERATOR: "+",
            TokenType.SUBTRACT_OPERATOR: "-",
            TokenType.MULTIPLY_OPERATOR: "*",
            TokenType.DIVIDE_FLOOR_OPERATOR: "/",
            TokenType.AND_OPERATOR: "&",
            TokenType.TIMES_OPERATOR: "x",
        }.get(operand.token_type, "")
        return cls(operator, lhs, rhs)
    
class SingleOperatorToken(Token):
    def __init__(self, p_operator: str, *args, **kwargs):
        super().__init__(TokenType.COMPOSITE, *args, **kwargs)
        self.operator = p_operator
        self.lhs: Token = args[0]
        
    def _show_recursive(self, indent: str = ""):
        return indent + f"{self.operator}\n" + (
                self.lhs._show_recursive(indent + "  ")
        )

    def evaluate(self, modus_op: str="num", times: int=1) -> EvalResult:
        a = self.lhs.evaluate(modus_op, times)
        if self.operator == "+":
            return a
        if self.operator == "-":
            return -a
        if self.operator == "min":
            return min(a)
        if self.operator == "max":
            return max(a)
        raise Exception(f"Invalid operator: {self.operator}")
    
    def string_evaluate(self, modus_op: str="num", times: int=1, index: int=0, indent: str="") -> str:
        res = self.evaluate(modus_op, times)
        return f"({self.operator}{self.lhs.string_evaluate(modus_op, times, index, indent)} = {res})"
    
    def custom_copy(self):
        return SingleOperatorToken(self.operator, self.lhs.custom_copy())
    
    @classmethod
    def from_tokens(cls, operand: Token, leaf: Token) -> Token:
        if operand.token_type == TokenType.ADD_OPERATOR:
            return cls("+", leaf)
        if operand.token_type == TokenType.SUBTRACT_OPERATOR:
            return cls("-", leaf)
        if operand.token_type == TokenType.IDENTIFIER:
            if operand.id_value == "m":
                return cls("min", leaf)
            if operand.id_value == "M":
                return cls("max", leaf)
        raise ValueError("Invalid Operand")
    
    @classmethod
    def valid_tokens(cls, operand: Token, leaf: Token) -> bool:
        if not leaf.is_evaluable(): return False
        if operand.token_type in (TokenType.ADD_OPERATOR, TokenType.SUBTRACT_OPERATOR):
            return True
        if operand.token_type == TokenType.IDENTIFIER:
            return operand.id_value in ["M", "m"]
        return False

def interprete_roll(inp: str, author_id: int=-1) -> str:
    try:
        root = parse_roll(tokenise(inp))
    except ValueError as e:
        return str(e)
    return root.string_evaluate()

def tokenise(inp: str) -> list[Token]:
    current_token = ""
    tokens = []
    # Initial tokenisation
    for c in inp + "\x00":  # Null terminate to trigger token evaluator at the end (could be any whitespace)
        if c in SINGLE_CHAR_TOKENS:
            # dice atom
            match = re.search(r"^(\d+)d(\d+)$", current_token)
            if match is not None:
                number, sides = map(int, match.group(1, 2))
                tokens.append(Token(TokenType.DICE, number, sides))
            # integer atom
            elif current_token.isdigit():
                tokens.append(Token(TokenType.INTEGER, int(current_token)))
            elif current_token != "":
                tokens.append(Token(TokenType.IDENTIFIER, current_token))
            current_token = ""
            tokens.append(Token(SINGLE_CHAR_TOKENS[c]))
        else:
            current_token += c
    tokens = list(filter(lambda x: x.token_type != TokenType.WHITESPACE, tokens))
    return tokens

def parser_pass(tokens: List[Token], filter: list[TokenType]) -> None:
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.token_type in filter:
            if i <= 0:
                raise Exception(f"Unexpected start of input")
            if not tokens[i-1].is_evaluable():
                raise Exception(f"Invalid token encountered: {tokens[i-1]}")
            if i >= len(tokens) - 1:
                raise Exception(f"Unexpected end of input")
            prep_next_token(tokens, i+1)
            tokens[i-1: i+2] = [OperatorToken.from_tokens(*tokens[i-1: i+2])]
            i -= 2
        i += 1

def prep_next_token(tokens: list[Token], i: int) -> None:
    if tokens[i].is_evaluable():
        return
    if SingleOperatorToken.valid_tokens(tokens[i], tokens[i+1]):
        prep_next_token(tokens, i+1)
        tokens[i: i+2] = [SingleOperatorToken.from_tokens(tokens[i], tokens[i+1])]
        return

def parse_roll(tokens: list[Token]) -> Token:
    i = 0
    last_bracket_stack = []
    while i < len(tokens):
        t = tokens[i]
        if t.token_type == TokenType.BRACKET_OPEN:
            last_bracket_stack.append(i)
        elif t.token_type == TokenType.BRACKET_CLOSE:
            if len(last_bracket_stack) == 0:
                raise ValueError("Parenteses mismatch")
            last = last_bracket_stack.pop()
            tokens[last: i + 1] = [parse_roll(tokens[last + 1: i])]
            i = last
        i += 1

    if len(last_bracket_stack) != 0:
        raise ValueError("Parenteses mismatch")

    prep_next_token(tokens, 0)
    parser_pass(tokens, [TokenType.MULTIPLY_OPERATOR, TokenType.DIVIDE_FLOOR_OPERATOR])
    parser_pass(tokens, [TokenType.ADD_OPERATOR, TokenType.SUBTRACT_OPERATOR])
    parser_pass(tokens, [TokenType.TIMES_OPERATOR])
    parser_pass(tokens, [TokenType.AND_OPERATOR])

    assert len(tokens) == 1
    return tokens[0]

def test_equivalent(*args) -> None:
    np.random.seed(0)
    root0 = parse_roll(tokenise(args[0]))
    res0 = root0.evaluate()
    for arg in args[1:]:
        np.random.seed(0)
        root = parse_roll(tokenise(arg))
        res = root.evaluate()
        assert res.shape == res0.shape
        assert (res == res0).all()

def test_fail(query) -> None:
    try:
        root = parse_roll(tokenise(query))
        res = root.evaluate()
    except Exception:
        return
    else:
        raise Exception("Did not fail")

def tests():
    test_equivalent("1d100", "1d100")
    test_equivalent("(5x 1) + 2", "5x 1 + 2")
    test_equivalent("5x (3x1)", "(3x5) x1")
    test_equivalent("15x1", "(3x5) x1")
    test_equivalent("1*-2", "0-2", "-2")
    test_fail("*2")
    test_fail("1 + ((1 + 2))) * 3 + (4 + 4")
    print("All tests passed")

if __name__ == '__main__':
    print(tokenise("BREAKWATER ::: (LOYAL_GUARDIAN, DEN_MOTHER, BROTHERS_IN_ARMS, ALBEDO_CAVALIER)"))
    print(tokenise("1d20 + M(2x1d6)"))
    print(interprete_roll("3x(1d20 + M(2x1d6) + 4)", -1), "\n==========================")
    print(interprete_roll("2x3 & 0*-2 & 1 + 2*(3-5)/2", -1), "\n==========================")
    print(interprete_roll("m(1d6x1d6)", -1), "\n==========================")
    tests()

    #print(interprete_roll("5x (3x1d6)"))
    #print(interprete_roll("(10d10 - 10) x (1d5 * (1d2 + 3) / 2d8)", -1), "\n==========================")
    #print(interprete_roll("(3x5) x1d6"), "\n==========================")

    #print(parse_roll(tokenise("(2d6 - 5) / 2")))
    #print(parse_roll(tokenise("1x3 & 5+3x(4 && 3)")))
    #print(parse_roll(tokenise("(10d10 - 10) x (1d5 * (1d2 + 3) / 2d8)")))
    #print(parse_roll(tokenise("1+2+3+4*5*6*7+8+9+10")))
    #print(parse_roll(tokenise("1 + ((1 + 2) * 3 + (4)) + 4")))
    #print(parse_roll(tokenise("1 + ((1 + 2))) * 3 + (4 + 4")))
