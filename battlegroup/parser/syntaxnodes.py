import typing
import numpy as np
import numpy.typing as nptyp

EvalResult = nptyp.NDArray[np.int32]

class SyntaxNode:
    def __init__(self, p_id: str):
        self.id = p_id
        self.result = np.zeros(0, np.int32)
        self.has_result = False
        #assert self.id != ""

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

    def evaluate_as_numeric(self, modus_op: str="num") -> int:
        return 0

    def evaluate(self, modus_op: str="num") -> EvalResult:
        return np.ones(1, np.int32) * self.evaluate_as_numeric(modus_op)

    def string_evaluate(self, modus_op: str="num", indent: str="") -> str:
        return ""

    def custom_copy(self):
        return SyntaxNode(self.id)


class IntegerNode(SyntaxNode):
    def __init__(self, p_val: int):
        super().__init__("int")
        self.value = p_val

    def _show_recursive(self, indent: str = "") -> str:
        return indent + f"{self.value}"

    def evaluate_as_numeric(self, modus_op: str="num") -> int:
        return self.value

    def string_evaluate(self, modus_op: str="num", indent: str="") -> str:
        return str(self.value)

    def custom_copy(self):
        return IntegerNode(self.value)


class DiceNode(SyntaxNode):
    def __init__(self, p_number: int, p_sides: int):
        super().__init__("dice")
        self.number = p_number
        self.sides = p_sides

    def _show_recursive(self, indent: str="") -> str:
        return indent + f"{self.number}d{self.sides}"

    def evaluate_as_numeric(self, modus_op: str="num") -> int:
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
    

class DiceOperatorNode(SyntaxNode):
    def __init__(self, p_operator: str, p_lhs: SyntaxNode, p_rhs: SyntaxNode):
        super().__init__("op2")
        assert p_lhs is not None
        assert p_rhs is not None
        self.operator = p_operator
        self.lhs = p_lhs
        self.rhs = p_rhs
        self.rhs_copies = []


    def _show_recursive(self, indent: str=""):
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


class DiceUnitaryNode(SyntaxNode):
    def __init__(self, p_operator: str, p_lhs: SyntaxNode):
        super().__init__("op1")
        self.operator = p_operator
        self.lhs = p_lhs
        
    def _show_recursive(self, indent: str=""):
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

