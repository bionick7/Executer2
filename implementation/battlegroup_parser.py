import re
import typing
import numpy as np
import numpy.typing as nptyp
from random import Random
from enum import Enum, auto

EvalResult = typing.Union[nptyp.NDArray[np.int32], nptyp.NDArray[np.float32]]


class TokenType(Enum):
    IDENTIFIER = auto(),
    BRACKET_OPEN = auto(),
    BRACKET_CLOSE = auto(),
    DOT = auto(),
    ADD_OPERATOR = auto(),
    SUBTRACT_OPERATOR = auto(),
    MULTIPLY_OPERATOR = auto(),
    DIVIDE_FLOOR_OPERATOR = auto(),
    AND_OPERATOR = auto(),
    TIMES_OPERATOR = auto(),
    SEPARATOR = auto(),
    DOUBLE_STAR = auto(),

SINGLE_CHAR_TOKENS = {
    "(": TokenType.BRACKET_OPEN,
    ")": TokenType.BRACKET_CLOSE,
    "+": TokenType.ADD_OPERATOR,
    "-": TokenType.SUBTRACT_OPERATOR,
    "*": TokenType.MULTIPLY_OPERATOR,
    "/": TokenType.DIVIDE_FLOOR_OPERATOR,
    "&": TokenType.AND_OPERATOR,
    "#": TokenType.TIMES_OPERATOR,
    ",": TokenType.SEPARATOR,
    ".": TokenType.DOT,
}


class Token:
    def __init__(self, p_type: TokenType, p_value: str):
        self.token_type = p_type
        self.value = p_value

    def __repr__(self):
        return f"[{self.value}]({self.token_type})"


def make_long_token(token_str: str) -> Token:
    return Token(TokenType.IDENTIFIER, token_str)


def tokenise(inp: str) -> list[Token]:
    current_token = ""
    tokens = []
    # Terminator to trigger token evaluator at the end and don't have to worry about checking end of string (could be any whitespace)
    inp += "\x00"
    i = 0
    while i < len(inp):
        c = inp[i]
        if c == "*":
            if current_token != "": tokens.append(make_long_token(current_token))
            current_token = ""
            if inp[i+1] == "*":
                tokens.append(Token(TokenType.DOUBLE_STAR, "**"))
                i += 2
            else:
                tokens.append(Token(TokenType.MULTIPLY_OPERATOR, "*"))
                i += 1
        elif ord(c) <= 32:
            if current_token != "": tokens.append(make_long_token(current_token))
            current_token = ""
            i += 1
        elif c in SINGLE_CHAR_TOKENS:
            if current_token != "": tokens.append(make_long_token(current_token))
            current_token = ""
            tokens.append(Token(SINGLE_CHAR_TOKENS[c], c))
            i += 1
        else:
            current_token += c
            i += 1
    return tokens


class DiceSyntaxNode:
    def __init__(self, p_id: str):
        self.id = p_id
        self.result = np.zeros(0, np.int32)
        self.has_result = False
        assert self.id != ""

    def _show_recursive(self, indent: str = "") -> str:
        return indent + f"{self.id}"

    def _set_result(self, res: EvalResult) -> EvalResult:
        self.result = res
        self.has_result = True
        return res
    
    def __repr__(self):
        return self._show_recursive()
        
    def is_evaluable(self) -> bool:
        return self.id != "pending"

    def evaluate_as_num(self, modus_op: str="num") -> int:
        return 0

    def evaluate(self, modus_op: str="num") -> EvalResult:
        return np.ones(1, np.int32) * self.evaluate_as_num(modus_op)

    def string_evaluate(self, modus_op: str="num", indent: str="") -> str:
        return ""

    def custom_copy(self):
        return DiceSyntaxNode(self.id)
    
    @classmethod
    def from_token(cls, token: Token):
        if token.token_type == TokenType.IDENTIFIER:
            # dice atom
            match = re.search(r"^(\d+)d(\d+)$", token.value)
            if match is not None:
                number, sides = map(int, match.group(1, 2))
                return DiceNode(number, sides)
            # integer atom
            if token.value.isdigit():
                return DiceIntegerNode(int(token.value))
        return DicePendingOpNode(token)


class DicePendingOpNode(DiceSyntaxNode):
    def __init__(self, p_token: Token):
        super().__init__("pending")
        self.token = p_token
        assert self.token.value in "+-*/&#()" or self.token.token_type == TokenType.IDENTIFIER
    
    def _show_recursive(self, indent: str = "") -> str:
        return indent + f"PENDING: {self.token}"


class DiceIntegerNode(DiceSyntaxNode):
    def __init__(self, p_val: int):
        super().__init__("int")
        self.value = p_val

    def _show_recursive(self, indent: str = "") -> str:
        return indent + f"{self.value}"

    def evaluate_as_num(self, modus_op: str="num") -> int:
        return self.value

    def string_evaluate(self, modus_op: str="num", indent: str="") -> str:
        return str(self.value)

    def custom_copy(self):
        return DiceIntegerNode(self.value)


class DiceNode(DiceSyntaxNode):
    def __init__(self, p_number: int, p_sides: int):
        super().__init__("dice")
        self.number = p_number
        self.sides = p_sides

    def _show_recursive(self, indent: str = "") -> str:
        return indent + f"{self.number}d{self.sides}"

    def evaluate_as_num(self, modus_op: str="num") -> int:
        if modus_op == "num":
            if not self.has_result:  # Don't re-roll
                self._set_result(np.random.randint(1, self.sides, self.number, np.int32))
            return int(np.sum(self.result))
        elif modus_op == "min":
            return self.number
        elif modus_op == "max":
            return self.sides * self.number
        return 0

    def string_evaluate(self, modus_op: str="num", indent: str="") -> str:
        if not self.has_result:
            return "Uncalc"
        if len(self.result) == 0:
            return "None"
        elif len(self.result) == 1:
            return f"{self.result[0]}|{self.sides}"
        return f"({' + '.join([str(r) + '|' + str(self.sides) for r in self.result])} = {sum(self.result)})"

    def custom_copy(self):
        return DiceNode(self.number, self.sides)
    

class DiceOperatorNode(DiceSyntaxNode):
    def __init__(self, p_operator: str, p_lhs: DiceSyntaxNode, p_rhs: DiceSyntaxNode):
        super().__init__("op2")
        self.operator = p_operator
        self.lhs = p_lhs
        self.rhs = p_rhs
        self.rhs_copies = []

    def _show_recursive(self, indent: str = ""):
        return indent +  f"{self.operator}\n" + (
                self.lhs._show_recursive(indent + "  ") + "\n" + 
                self.rhs._show_recursive(indent + "  ")
        )

    def evaluate(self, modus_op: str="num") -> EvalResult:
        if self.has_result:
            return self.result
        
        if self.operator == "#":
            times_n = int(np.sum(self.lhs.evaluate(modus_op)))
            self.rhs_copies = [self.rhs.custom_copy() for _ in range(times_n)]
            return self._set_result(np.concatenate([
                c.evaluate(modus_op) for c in self.rhs_copies
            ]))
        a, b = self.lhs.evaluate(modus_op), self.rhs.evaluate(modus_op)
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
        res = self.evaluate(modus_op)  # Needs to set internal state
        if self.operator == "#":
            return (
                    f"(" + f"".join(["\n" + indent + "  " + c.string_evaluate(modus_op, indent + "  ") for c in self.rhs_copies])
                    + f"\n{indent})"
            )
        if self.operator == "&":
            return (
                    f"({self.lhs.string_evaluate(modus_op, indent + '  ')}"
                    f"\n{indent}&\n{indent}{self.rhs.string_evaluate(modus_op, indent + '  ')}"
                    f"\n{indent})"
            )
        res_str = str(res[0]) if len(res) == 1 else str(res)
        return f"({self.lhs.string_evaluate(modus_op, indent)} {self.operator} {self.rhs.string_evaluate(modus_op, indent)} = {res_str})"
    
    def custom_copy(self):
        return DiceOperatorNode(self.operator, self.lhs.custom_copy(), self.rhs.custom_copy())
    
    @classmethod
    def from_tokens(cls, lhs: DiceSyntaxNode, operand: DicePendingOpNode, rhs: DiceSyntaxNode):
        return cls(operand.token.value, lhs, rhs)


class DiceUnitaryNode(DiceSyntaxNode):
    def __init__(self, p_operator: str, p_lhs: DiceSyntaxNode):
        super().__init__("op1")
        self.operator = p_operator
        self.lhs = p_lhs
        
    def _show_recursive(self, indent: str = ""):
        return indent + f"{self.operator}\n" + self.lhs._show_recursive(indent + "  ")

    def evaluate(self, modus_op: str="num") -> EvalResult:
        a = self.lhs.evaluate(modus_op)
        if self.operator == "+":
            return a
        if self.operator == "-":
            return -a
        if self.operator == "min":
            return min(a)
        if self.operator == "max":
            return max(a)
        raise Exception(f"Invalid operator: {self.operator}")
    
    def string_evaluate(self, modus_op: str="num", indent: str="") -> str:
        res = self.evaluate(modus_op)
        return f"({self.operator}{self.lhs.string_evaluate(modus_op, indent)} = {res})"
    
    def custom_copy(self):
        return DiceUnitaryNode(self.operator, self.lhs.custom_copy())
    
    @classmethod
    def from_tokens(cls, operand: DicePendingOpNode, leaf: DiceSyntaxNode) -> DiceSyntaxNode:
        if operand.token.token_type == TokenType.ADD_OPERATOR:
            return cls("+", leaf)
        if operand.token.token_type == TokenType.SUBTRACT_OPERATOR:
            return cls("-", leaf)
        if operand.token.token_type == TokenType.IDENTIFIER:
            if operand.token.value == "m":
                return cls("min", leaf)
            if operand.token.value == "M":
                return cls("max", leaf)
        raise ValueError("Invalid Operand")
    
    @classmethod
    def valid_tokens(cls, operand: DicePendingOpNode, leaf: DiceSyntaxNode) -> bool:
        if not leaf.is_evaluable(): return False
        return operand.token.value in "+-Mm"


class Parser():
    def __init__(self, p_tokens: list[Token]) -> None:
        self.consumed_tokens = 0
        self.tokens = p_tokens[:]

    def _roll_parser_pass(self, nodes: list[DiceSyntaxNode], filter: list[str]) -> None:
        i = 0
        while i < len(nodes):
            t = nodes[i]
            if isinstance(t, DicePendingOpNode) and t.token.value in filter:
                if i <= 0:
                    raise Exception(f"Unexpected start of input")
                if not nodes[i-1].is_evaluable():
                    raise Exception(f"Invalid token encountered: {nodes[i-1]}")
                if i >= len(nodes) - 1:
                    raise Exception(f"Unexpected end of input")
                op_node = DiceOperatorNode.from_tokens(
                    self._roll_prep_next_token(nodes, i-1), t,
                    self._roll_prep_next_token(nodes, i+1)
                )
                nodes[i-1: i+2] = [op_node]
                self.consumed_tokens += 2
                i -= 2
            i += 1

    def _roll_prep_next_token(self, nodes: list[DiceSyntaxNode], i: int) -> DiceSyntaxNode:
        if nodes[i].is_evaluable():
            return nodes[i]
        n = nodes[i]
        if isinstance(n, DicePendingOpNode) and DiceUnitaryNode.valid_tokens(n, nodes[i+1]):
            self._roll_prep_next_token(nodes, i+1)
            unitary = DiceUnitaryNode.from_tokens(n, nodes[i+1])
            nodes[i: i+2] = [unitary]
            self.consumed_tokens += 1
            return unitary
        return DiceSyntaxNode("")

    def _parse_roll(self, nodes: list[DiceSyntaxNode]) -> DiceSyntaxNode:
        consumed_tokens = 0
        i = 0
        last_bracket_stack = []
        while i < len(nodes):
            n = nodes[i]
            if isinstance(n, DicePendingOpNode) and n.token.token_type == TokenType.BRACKET_OPEN:
                last_bracket_stack.append(i)
            elif isinstance(n, DicePendingOpNode) and n.token.token_type == TokenType.BRACKET_CLOSE:
                if len(last_bracket_stack) == 0:
                    raise ValueError("Parenteses mismatch")
                last = last_bracket_stack.pop()
                consumed_tokens += 2
                nodes[last: i + 1] = [self._parse_roll(nodes[last + 1: i])]
                i = last
            i += 1

        if len(last_bracket_stack) != 0:
            raise ValueError("Parenteses mismatch")

        self._roll_prep_next_token(nodes, 0)
        self._roll_parser_pass(nodes, ["*", "/"])
        self._roll_parser_pass(nodes, ["+", "-"])
        self._roll_parser_pass(nodes, ["#"])
        self._roll_parser_pass(nodes, ["&"])

        consumed_tokens += 1
        return nodes.pop(0)

    def parse_roll(self) -> DiceSyntaxNode:
        return self._parse_roll(list(map(DiceSyntaxNode.from_token, self.tokens)))
