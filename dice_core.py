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

    def evaluate(self) -> int:
        if self.token_type == TokenType.INTEGER:
            return self.value
        elif self.token_type == TokenType.DICE:
            if not self._results:  # Don't re-roll
                self._results = [randint(1, self.sides) for _ in range(self.number)]
            return sum(self._results)
        else:
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
        for _ in range(evaluate(enumerator_token)):
            roll_list.append(t.custom_copy())
    for roll in roll_list:
        if author_id >= 0:
            # print(f"Author is {author_id}")
            last_dice_rolls[author_id] = evaluate(roll)
        res += string_evaluate(roll, 0) + "\n"
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


def evaluate(token: Token) -> int:
    if token.can_be_evaluated():
        return token.evaluate()
    if token.token_type == TokenType.TOKEN_SET:
        res = evaluate(token.token_list[0])
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
                if current_operation == '+':
                    res += evaluate(t)
                elif current_operation == '-':
                    res -= evaluate(t)
                elif current_operation == '*':
                    res *= evaluate(t)
                elif current_operation == '/':
                    res //= evaluate(t)
            else:
                current_operation = ''
        return res
    return 0


def tokenise(inp: str) -> Dict[Token, Token]:
    current_token = ""
    tokens = []
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
    while i < len(tokens):
        t = tokens[i]
        if t.token_type in (TokenType.MULTIPLY_OPERATOR, TokenType.DIVIDE_FLOOR_OPERATOR):
            tokens[i-1: i+2] = [Token.comulate(tokens[i-1: i+2])]
            i -= 2
        i += 1
    i = 0
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
    last = 0
    """
    while i < len(tokens):
        if tokens[i].token_type in (TokenType.AND_OPERATOR, TokenType.TIMES_OPERATOR):
            print(i, tokens[i], tokens)
            if i - last > 2:
                print(last, i)
                tokens[last+1: i] = [Token(TokenType.TOKEN_SET, tokens[last+1: i])]
            last = i
        i += 1"""
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


def legacy(args: List[str], author_id: int) -> str:
    global last_dice_rolls

    number, dice_faces = args[1].split("d")
    is_sum = "/s" in args
    mult = 2 if "/crit" in args else 1

    dice_list = []
    dice_int = int(dice_faces)

    for i in range(int(number)):
        dice_list.append(randint(1, dice_int))

    bonus = 0
    for arg in args[2:]:
        if arg.startswith("+"):
            if "d" in arg:
                number, dice_int = arg[1:].split("d")
                dice_int = int(dice_int)
                for i in range(int(number)):
                    dice_list.append(randint(1, dice_int))
            else:
                try:
                    bonus += int(arg[1:])
                except ValueError:
                    pass
        if arg.startswith("-"):
            if "d" in arg:
                number, dice_int = arg[1:].split("d")
                dice_int = int(dice_int)
                for i in range(int(number)):
                    dice_list.append(-randint(1, dice_int))
            else:
                try:
                    bonus -= int(arg[1:])
                except ValueError:
                    pass

    if is_sum:
        collective_bonus = bonus
        individual_bonus = 0
    else:
        collective_bonus = 0
        individual_bonus = bonus

    conclude_individual = not (individual_bonus == 0 and mult == 1)

    results_list = [d * mult + individual_bonus for d in dice_list]
    formated_string_list = []
    for i in range(len(dice_list)):
        formated_string = str(dice_list[i])
        if mult != 1:
            formated_string += " * 2 "
        if individual_bonus != 0:
            formated_string += (" + " if individual_bonus > 0 else " - ") + str(abs(individual_bonus))
        if conclude_individual:
            formated_string += " = " + str(results_list[i])
        formated_string_list.append(formated_string)

    return_string = ("\n + " if is_sum else "\n").join(formated_string_list) +\
                    ("\n+" + str(collective_bonus) if collective_bonus != 0 else "")

    if is_sum:
        end_result = sum([x * mult + individual_bonus for x in dice_list]) + collective_bonus
        end_result += f" = {end_result}"
        last_dice_rolls[author_id] = end_result
    else:
        last_dice_rolls[author_id] = results_list[-1]

    return return_string


if __name__ == '__main__':
    # print(interprete_roll("(10d10 - 10) x (1d5 * (1d2 + 3) / 2d8)"))
    print(interprete_roll("1x3 & 5+3x4 && 3", -1))
