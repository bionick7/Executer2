import typing
import ply.lex as lex
import ply.yacc as yacc

from battlegroup.parser.syntaxnodes import *

class Parser:
    def __init__(self,**kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        self.parser: yacc.LRParser = yacc.yacc(module=self, **kwargs)
        self.error_queue = []

    # Needs to hase specific name
    tokens = (
        "IDENTIFIER",
        "STRLITERAL",
        "INTEGER",
        "DICE",
        "LPAREN",
        "RPAREN",
        "PLUS",
        "MINUS",
        "MULTIPLY",
        "DIVIDE",
        "AND",
        "TIMES",
        "DOT",
        "DOUBLE_STAR",
        "BG_SEPERATOR",
        "ASSIGN",
        "INITIALIZE",
        "PLUSEQUAL",
        "MINUSEQUAL",
        "ARROWLEFT",
        "QUESTION"
    )
    
    # Regular expression rules for simple tokens
    t_LPAREN        = r'\('
    t_RPAREN        = r'\)'
    t_PLUS          = r'\+'
    t_MINUS         = r'-'
    t_MULTIPLY      = r'\*'
    t_DIVIDE        = r'/'
    t_AND           = r'&'
    t_TIMES         = r'\#'
    t_DOT           = r'\.'
    t_DOUBLE_STAR   = r'\*{2}'
    t_IDENTIFIER    = r'[a-zA-Z_][a-zA-Z0-9_\-]*'
    t_BG_SEPERATOR  = r'::'
    t_ASSIGN        = r'='
    t_INITIALIZE    = r':='
    t_PLUSEQUAL     = r'\+='
    t_MINUSEQUAL    = r'-='
    t_ARROWLEFT     = r'=>'
    t_QUESTION      = r'\?{2}'
    
    # ORDER DOES MATTER! Dice before Integer
    def t_DICE(self, t):
        r'\d+d\d+'
        num, sides = map(int, t.value.split("d"))
        t.value = DiceNode(num, sides)
        return t

    def t_INTEGER(self, t):
        r'\d+'
        t.value = IntegerNode(int(t.value))
        return t
        
    def t_STRLITERAL(self, t):
        r'"([^"\\]|(\["\\tnr]))*"'
        t.value = t.value[1:-1] \
            .replace("\\n", "\n") \
            .replace("\\t", "\t") \
            .replace("\\\\", "\\") \
            .replace("\\\"", "\"")
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        
    def t_COMMENT(self, t):
        r'(//.*(\n|$))'

    t_ignore  = ' \t'

    def p_command(self, p):
        """command       : path operator arglist
                         | IDENTIFIER operator arglist
                         | path operator
                         | IDENTIFIER operator
                         | operator
                         | IDENTIFIER
        """
        if len(p) == 2:
            p[0] = {"path": ["**"], "cmd": p[1], "args": []}
            return
        args = p[3] if len(p) == 4 else []
        p[0] = {"path": p[1], "cmd": p[2], "args": args}
        if isinstance(p[0]["path"], str):
            p[0]["path"] = [p[0]["path"]]

    def p_funccommand(self, p):
        """command       : IDENTIFIER LPAREN arglist RPAREN
                         | IDENTIFIER LPAREN RPAREN
                         | operator LPAREN arglist RPAREN
                         | operator LPAREN RPAREN
        """
        if len(p) == 5:
            p[0] = {"path": ["**"], "cmd": p[1], "args": p[3]}
        else:
            p[0] = {"path": ["**"], "cmd": p[1], "args": []}


    def p_arglist(self, p):
        """arglist       : arglist BG_SEPERATOR expression
                         | expression
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_pathelem(self, p):
        """pathelem      : MULTIPLY
                         | DOUBLE_STAR
                         | IDENTIFIER
                         | INTEGER
                         """
        lhs = p[1]
        if isinstance(lhs, IntegerNode):
            lhs = str(lhs.value)
        p[0] = lhs
        
    def p_expression(self, p):
        """expression    : d_expression
                         | path
                         | IDENTIFIER
                         | STRLITERAL
        """
        p[0] = p[1]

    def p_path(self, p):
        """path          : path DOT pathelem
                         | IDENTIFIER DOT pathelem
                         | INTEGER DOT pathelem
                         | DOUBLE_STAR
                         | MULTIPLY
        """
        lhs = p[1]
        if isinstance(lhs, IntegerNode):
            lhs = str(lhs.value)
        if not isinstance(lhs, list):
            lhs = [lhs]
        if len(p) == 2:
            p[0] = lhs
            return
        p[0] = lhs + [p[3]]
    
    def p_binary_operators_dice(self, p):
        '''d_expression  : d_expression AND d_term2
           d_term2       : d_term2 TIMES d_term1
           d_term1       : d_term1 PLUS d_term0
                         | d_term1 MINUS d_term0
           d_term0       : d_term0 MULTIPLY d_factor
                         | d_term0 DIVIDE d_factor'''
        p[0] = DiceOperatorNode(p[2], p[1], p[3])
        
    def p_unary_operators_dice(self, p):
        '''d_factor : PLUS d_factor
                    | MINUS d_factor'''
        p[0] = DiceUnitaryNode(p[1], p[2])

    def p_fallthroughs(self, p):
        '''d_expression : d_term2
           d_term2      : d_term1
           d_term1      : d_term0
           d_term0      : d_factor
           d_factor     : INTEGER
                        | DICE'''
        p[0] = p[1]

    def p_parens(self, p):
        '''d_factor     : LPAREN d_expression RPAREN
        '''
        p[0] = p[2]

    def p_operator(self, p):
        '''operator    : ASSIGN
                       | INITIALIZE
                       | PLUSEQUAL
                       | MINUSEQUAL
                       | ARROWLEFT
                       | QUESTION
        '''
        p[0] = p[1]
        
    def p_func(self, p):
        '''d_factor     : IDENTIFIER LPAREN d_expression RPAREN
        '''
        if p[1] in ("m", "min"):
            p[0] = DiceUnitaryNode("min", p[3])
        elif p[1] in ("M", "max"):
            p[0] = DiceUnitaryNode("max", p[3])
        else:
            assert False

    def t_error(self,t):
        self.error_queue.append("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def p_error(self, p):
        if p:
            self.error_queue.append(f"Syntax error at '{p.value}' @ ({p.lineno}, {p.lexpos})")
        else:
            self.error_queue.append("Syntax error at EOF")
        
    def has_error(self) -> bool:
        return len(self.error_queue) > 0

    def get_error(self) -> str:
        if len(self.error_queue) == 0:
            return ""
        return self.error_queue.pop(0)

    def tokenise(self, line) -> list[lex.LexToken]:
        self.lexer.input(line)
        res = []
        while True:
            tok = self.lexer.token()
            if not tok: 
                return res      # No more input
            res.append(tok)
    
    def parse_command(self, inp: str) -> typing.Any:
        if len(self.tokenise(inp)) == 0: 
            return ["**"], "_", []
        res = self.parser.parse(inp)
        if res is None:
            return ["**"], "_", []
        return res["path"], res["cmd"], res["args"]

    def parse_dice(self, inp: str) -> typing.Optional[DiceNode]:
        res = self.parser.parse("** ?? " + inp)
        if res is None:
            return None
        if "??" not in res["cmd"] or len(res["args"]) != 1 or not isinstance(res["args"][0], SyntaxNode):
            return None
        return res["args"][0]
