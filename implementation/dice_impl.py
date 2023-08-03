from random import randint
import re

from enum import Enum
from typing import List, Dict

last_dice_rolls = {}

HELP_TEXT = """
New roll Syntax:
a x b & (c x d)
where a b c d are all:
x + y * (z - w)
where x y z w are  all:
nds or a constant
example (1d5 * 2 + 3) x 4 would be 4 critical hits with 4 dammage modifiers
"""


class TokenType(Enum):
    BRACKET_OPEN = 0,
    BRACKET_CLOSE = 1,
    WHITESPACE = 2,
    INTEGER = 3,
    DICE = 4,
    ADD_OPERATOR = 5,
    SUBTRACT_OPERATOR = 6,
    MULTIPLY_OPERATOR = 7,
    DIVIDE_FLOOR_OPERATOR = 8,
    AND_OPERATOR = 9,
    TIMES_OPERATOR = 10,
    TOKEN_SET = 11,


SINGLE_CHAR_TOKENS = {
    "(": TokenType.BRACKET_OPEN,
    ")": TokenType.BRACKET_CLOSE,
    "+": TokenType.ADD_OPERATOR,
    "-": TokenType.SUBTRACT_OPERATOR,
    "*": TokenType.MULTIPLY_OPERATOR,
    "/": TokenType.DIVIDE_FLOOR_OPERATOR,
    "&": TokenType.AND_OPERATOR,
    "x": TokenType.TIMES_OPERATOR,
    **(dict(zip(map(chr, range(33)), [TokenType.WHITESPACE]*33)))
    # marks all the characters up to 0x20 ([space]) as whitespace
}


def get_dice_permutations(p, q, x: int) -> int:
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
        if p_type == TokenType.INTEGER:
            self.value = args[0]
        elif p_type == TokenType.DICE:
            self.number, self.sides = args[0:2]
            self._results = list()
        elif p_type == TokenType.TOKEN_SET:
            self.token_list = args[0]

    def __repr__(self):
        if self.token_type == TokenType.TOKEN_SET:
            return "SET" + self.token_list.__repr__()
        return self.token_type.name

    def can_be_evaluated(self) -> bool:
        return self.token_type in (TokenType.INTEGER, TokenType.DICE)

    def can_be_evaluated_indirect(self) -> bool:
        return self.token_type in (TokenType.INTEGER, TokenType.DICE, TokenType.TOKEN_SET)

    def evaluate(self, modus_op="num") -> int:
        if self.token_type == TokenType.INTEGER:
            if modus_op == "var":
                return 0
            if modus_op == "exp2":
                return self.value*self.value
            else:
                return self.value
        if self.token_type == TokenType.DICE:
            if modus_op == "num":
                if not self._results:  # Don't re-roll
                    self._results = [randint(1, self.sides) for _ in range(self.number)]
                return sum(self._results)
            elif modus_op == "min":
                return self.number
            elif modus_op == "max":
                return self.sides * self.number
            elif modus_op == "exp":
                return self.number * (0.5 + self.sides / 2)
            elif modus_op == "exp2":
                return self.number * sum([x * x for x in range(1, self.sides + 1)]) / self.sides
            elif modus_op == "var":
                return self.evaluate("exp2") - self.evaluate("exp")**2 / self.number
        return 0

    def string_evaluate(self) -> str:
        if self.token_type == TokenType.INTEGER:
            return str(self.value)
        elif self.token_type == TokenType.DICE:
            if not self._results:
                self._results = [randint(1, self.sides) for _ in range(self.number)]
            if len(self._results) == 0:
                return "None"
            elif len(self._results) == 1:
                return f"{self._results[0]}|{self.sides}"
            return f"({' + '.join([str(r) + '|' + str(self.sides) for r in self._results])} = {sum(self._results)})"
        else:
            return ""

    def custom_copy(self):
        args = []
        if self.token_type == TokenType.INTEGER:
            args = [self.value]
        elif self.token_type == TokenType.DICE:
            args = (self.number, self.sides)
        elif self.token_type == TokenType.TOKEN_SET:
            args = [[t.custom_copy() for t in self.token_list]]
        return Token(self.token_type, *args)

    @classmethod
    def comulate(cls, token_list: List):
        if len(token_list) == 1:
            return token_list[0]
        return cls(TokenType.TOKEN_SET, token_list)


def interprete_roll(inp: str, author_id: int) -> str:
    tokens = tokenise(inp)
    res = ""
    roll_list = []
    for enumerator_token, t in tokens.items():
        res += "rolling: " + string_evaluate(enumerator_token, 0) + " times \n"
        for _ in range(evaluate(enumerator_token, "num")):
            roll_list.append(t.custom_copy())
    for roll in roll_list:
        if author_id >= 0:
            # print(f"Author is {author_id}")
            last_dice_rolls[author_id] = evaluate(roll)
        res += string_evaluate(roll, 0) + "\n"
    return res


def analyse_roll(inp: str) -> str:
    tokens = tokenise(inp)
    res = ""
    for enumerator_token, t in tokens.items():
        if enumerator_token.token_type != TokenType.INTEGER:
            res += f"Enumerator : [{evaluate(enumerator_token, 'min')}, {evaluate(enumerator_token, 'max')}]" \
                   f"E = {evaluate(enumerator_token, 'exp')} --- STD = {evaluate(enumerator_token, 'var') ** 0.5}"
        res += f"Roll : [{evaluate(t, 'min')}, {evaluate(t, 'max')}] E = {evaluate(t, 'exp')} --- STD = {evaluate(t, 'var') ** 0.5}"
    return res


def string_evaluate(token: Token, recursion_level: int) -> str:
    evaluated = evaluate(token)
    if token.can_be_evaluated():
        return token.string_evaluate()
    if token.token_type == TokenType.TOKEN_SET:
        calculation = string_evaluate(token.token_list[0], recursion_level+1)
        for t in token.token_list[1:]:
            if t.token_type == TokenType.ADD_OPERATOR:
                calculation += ' + '
            elif t.token_type == TokenType.SUBTRACT_OPERATOR:
                calculation += ' - '
            elif t.token_type == TokenType.MULTIPLY_OPERATOR:
                calculation += ' * '
            elif t.token_type == TokenType.DIVIDE_FLOOR_OPERATOR:
                calculation += ' / '
            elif t.can_be_evaluated() or t.token_type == TokenType.TOKEN_SET:
                calculation += string_evaluate(t, recursion_level+1)
        return f"{calculation} = {evaluated}" if recursion_level == 0 else f"({calculation} = {evaluated})"
    return ""


def evaluate(token: Token, modus_op="num"):
    if token.can_be_evaluated():
        return token.evaluate(modus_op)
    if token.token_type == TokenType.TOKEN_SET:
        res = evaluate(token.token_list[0], modus_op)
        t2 = token.token_list[0]
        current_operation = ''
        for t in token.token_list[1:]:
            if t.token_type == TokenType.ADD_OPERATOR:
                current_operation = '+'
            elif t.token_type == TokenType.SUBTRACT_OPERATOR:
                current_operation = '-'
            elif t.token_type == TokenType.MULTIPLY_OPERATOR:
                current_operation = '*'
            elif t.token_type == TokenType.DIVIDE_FLOOR_OPERATOR:
                current_operation = '/'
            elif t.can_be_evaluated() or t.token_type == TokenType.TOKEN_SET:
                if modus_op == "var":
                    if current_operation == '*' and t2 is not None:
                        res = evaluate(t, "var") * evaluate(t2, "exp2") + evaluate(t2, "var") * evaluate(t, "exp2")
                    if current_operation == '/' and t.token_type == TokenType.INTEGER:
                        res /= evaluate(t, "exp2")
                else:
                    if current_operation == '+':
                        res += evaluate(t, modus_op)
                    elif current_operation == '-':
                        res -= evaluate(t, modus_op)
                    elif current_operation == '*':
                        res *= evaluate(t, modus_op)
                    elif current_operation == '/':
                        res //= evaluate(t, modus_op)
                t2 = t
            else:
                current_operation = ''
        return res
    return 0


def tokenise(inp: str) -> Dict[Token, Token]:
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
            if current_token.isdigit():
                tokens.append(Token(TokenType.INTEGER, int(current_token)))
            current_token = ""
            tokens.append(Token(SINGLE_CHAR_TOKENS[c]))
        else:
            current_token += c
    tokens = list(filter(lambda x: x.token_type != TokenType.WHITESPACE, tokens))
    # print(tokens)
    i = 0

    # Grouping
    last_bracket_queue = []
    while i < len(tokens):
        t = tokens[i]
        if t.token_type == TokenType.BRACKET_OPEN:
            last_bracket_queue.append(i)
        elif t.token_type == TokenType.BRACKET_CLOSE:
            last = last_bracket_queue.pop()
            tokens[last:i + 1] = [Token.comulate(tokens[last + 1: i])]
            i = last
        i += 1

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.token_type in (TokenType.MULTIPLY_OPERATOR, TokenType.DIVIDE_FLOOR_OPERATOR):
            tokens[i-1: i+2] = [Token.comulate(tokens[i-1: i+2])]
            i -= 2
        i += 1
    # print(tokens)

    i = 0
    last = 0
    times, rolls, add_times = [], [], True
    res = {}
    # print(tokens)
    for i, t in enumerate(tokens + [Token(TokenType.AND_OPERATOR)]):
        if t.token_type == TokenType.AND_OPERATOR:
            if not rolls:
                rolls, times = times, [Token(TokenType.INTEGER, 1)]
            if rolls:
                res[Token.comulate(times)] = Token.comulate(rolls)
            times, rolls, add_times = [], [], True
        elif t.token_type == TokenType.TIMES_OPERATOR:
            add_times = False
        else:
            if add_times:
                times.append(t)
            else:
                rolls.append(t)

    return res

if __name__ == '__main__':
    # print(interprete_roll("(10d10 - 10) x (1d5 * (1d2 + 3) / 2d8)"))
    # print(interprete_roll("1x3 & 5+3x4 && 3", -1))
    #print(analyse_roll("1d12"))
    #print(analyse_roll("2d6"))
    #print(analyse_roll("3d4"))
    #print(analyse_roll("4d3"))
    #print(analyse_roll("6d2"))
    print(analyse_roll("2d6 - 5"))
    print(analyse_roll("(2d6 - 5) / 2"))
    print(tokenise("(2d6 - 5) / 2"))
