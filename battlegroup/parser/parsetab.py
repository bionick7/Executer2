
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'AND ARROWLEFT ASSIGN BG_SEPERATOR DICE DIVIDE DOT DOUBLE_STAR IDENTIFIER INITIALIZE INTEGER LPAREN MINUS MINUSEQUAL MULTIPLY PLUS PLUSEQUAL QUESTION RPAREN STRLITERAL TIMEScommand       : path operator arglist\n                         | IDENTIFIER operator arglist\n                         | path operator\n                         | IDENTIFIER operator\n                         | operator\n                         | IDENTIFIER\n        command       : IDENTIFIER LPAREN arglist RPAREN\n                         | IDENTIFIER LPAREN RPAREN\n                         | operator LPAREN arglist RPAREN\n                         | operator LPAREN RPAREN\n        arglist       : arglist BG_SEPERATOR expression\n                         | expression\n        pathelem      : MULTIPLY\n                         | DOUBLE_STAR\n                         | IDENTIFIER\n                         | INTEGER\n                         expression    : d_expression\n                         | path\n                         | IDENTIFIER\n                         | STRLITERAL\n        path          : path DOT pathelem\n                         | IDENTIFIER DOT pathelem\n                         | INTEGER DOT pathelem\n                         | DOUBLE_STAR\n                         | MULTIPLY\n        d_expression  : d_expression AND d_term2\n           d_term2       : d_term2 TIMES d_term1\n           d_term1       : d_term1 PLUS d_term0\n                         | d_term1 MINUS d_term0\n           d_term0       : d_term0 MULTIPLY d_factor\n                         | d_term0 DIVIDE d_factord_factor : PLUS d_factor\n                    | MINUS d_factord_expression : d_term2\n           d_term2      : d_term1\n           d_term1      : d_term0\n           d_term0      : d_factor\n           d_factor     : INTEGER\n                        | DICEd_factor     : LPAREN d_expression RPAREN\n        operator    : ASSIGN\n                       | INITIALIZE\n                       | PLUSEQUAL\n                       | MINUSEQUAL\n                       | ARROWLEFT\n                       | QUESTION\n        d_factor     : IDENTIFIER LPAREN d_expression RPAREN\n        '
    
_lr_action_items = {'IDENTIFIER':([0,8,9,10,11,12,13,14,15,16,17,18,19,20,30,32,35,48,49,50,51,52,53,57,58,],[4,-41,-42,-43,-44,-45,-46,25,39,25,25,25,39,39,56,56,56,25,56,56,56,56,56,56,56,]),'INTEGER':([0,8,9,10,11,12,13,14,15,16,17,18,19,20,30,32,35,48,49,50,51,52,53,57,58,],[5,-41,-42,-43,-44,-45,-46,28,40,28,28,28,40,40,55,55,55,28,55,55,55,55,55,55,55,]),'DOUBLE_STAR':([0,8,9,10,11,12,13,14,15,16,17,18,19,20,48,],[6,-41,-42,-43,-44,-45,-46,6,38,6,6,6,38,38,6,]),'MULTIPLY':([0,8,9,10,11,12,13,14,15,16,17,18,19,20,28,31,33,34,48,54,55,59,67,68,69,70,71,72,],[7,-41,-42,-43,-44,-45,-46,7,37,7,7,7,37,37,-38,57,-37,-39,7,-32,-38,-33,57,57,-30,-31,-40,-47,]),'ASSIGN':([0,2,4,6,7,36,37,38,39,40,46,47,],[8,8,8,-24,-25,-21,-13,-14,-15,-16,-22,-23,]),'INITIALIZE':([0,2,4,6,7,36,37,38,39,40,46,47,],[9,9,9,-24,-25,-21,-13,-14,-15,-16,-22,-23,]),'PLUSEQUAL':([0,2,4,6,7,36,37,38,39,40,46,47,],[10,10,10,-24,-25,-21,-13,-14,-15,-16,-22,-23,]),'MINUSEQUAL':([0,2,4,6,7,36,37,38,39,40,46,47,],[11,11,11,-24,-25,-21,-13,-14,-15,-16,-22,-23,]),'ARROWLEFT':([0,2,4,6,7,36,37,38,39,40,46,47,],[12,12,12,-24,-25,-21,-13,-14,-15,-16,-22,-23,]),'QUESTION':([0,2,4,6,7,36,37,38,39,40,46,47,],[13,13,13,-24,-25,-21,-13,-14,-15,-16,-22,-23,]),'$end':([1,3,4,6,7,8,9,10,11,12,13,14,17,21,22,23,24,25,26,27,28,29,31,33,34,36,37,38,39,40,42,43,45,46,47,54,55,59,61,62,63,64,66,67,68,69,70,71,72,],[0,-5,-6,-24,-25,-41,-42,-43,-44,-45,-46,-3,-4,-18,-1,-12,-17,-19,-20,-34,-38,-35,-36,-37,-39,-21,-13,-14,-15,-16,-10,-2,-8,-22,-23,-32,-38,-33,-9,-7,-11,-26,-27,-28,-29,-30,-31,-40,-47,]),'DOT':([2,4,5,6,7,21,25,28,36,37,38,39,40,46,47,],[15,19,20,-24,-25,15,19,20,-21,-13,-14,-15,-16,-22,-23,]),'LPAREN':([3,4,8,9,10,11,12,13,14,16,17,18,25,30,32,35,48,49,50,51,52,53,56,57,58,],[16,18,-41,-42,-43,-44,-45,-46,35,35,35,35,50,35,35,35,35,35,35,35,35,35,50,35,35,]),'BG_SEPERATOR':([6,7,21,22,23,24,25,26,27,28,29,31,33,34,36,37,38,39,40,41,43,44,46,47,54,55,59,63,64,66,67,68,69,70,71,72,],[-24,-25,-18,48,-12,-17,-19,-20,-34,-38,-35,-36,-37,-39,-21,-13,-14,-15,-16,48,48,48,-22,-23,-32,-38,-33,-11,-26,-27,-28,-29,-30,-31,-40,-47,]),'RPAREN':([6,7,16,18,21,23,24,25,26,27,28,29,31,33,34,36,37,38,39,40,41,44,46,47,54,55,59,60,63,64,65,66,67,68,69,70,71,72,],[-24,-25,42,45,-18,-12,-17,-19,-20,-34,-38,-35,-36,-37,-39,-21,-13,-14,-15,-16,61,62,-22,-23,-32,-38,-33,71,-11,-26,72,-27,-28,-29,-30,-31,-40,-47,]),'STRLITERAL':([8,9,10,11,12,13,14,16,17,18,48,],[-41,-42,-43,-44,-45,-46,26,26,26,26,26,]),'PLUS':([8,9,10,11,12,13,14,16,17,18,28,29,30,31,32,33,34,35,48,49,50,51,52,53,54,55,57,58,59,66,67,68,69,70,71,72,],[-41,-42,-43,-44,-45,-46,30,30,30,30,-38,52,30,-36,30,-37,-39,30,30,30,30,30,30,30,-32,-38,30,30,-33,52,-28,-29,-30,-31,-40,-47,]),'MINUS':([8,9,10,11,12,13,14,16,17,18,28,29,30,31,32,33,34,35,48,49,50,51,52,53,54,55,57,58,59,66,67,68,69,70,71,72,],[-41,-42,-43,-44,-45,-46,32,32,32,32,-38,53,32,-36,32,-37,-39,32,32,32,32,32,32,32,-32,-38,32,32,-33,53,-28,-29,-30,-31,-40,-47,]),'DICE':([8,9,10,11,12,13,14,16,17,18,30,32,35,48,49,50,51,52,53,57,58,],[-41,-42,-43,-44,-45,-46,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,]),'AND':([24,27,28,29,31,33,34,54,55,59,60,64,65,66,67,68,69,70,71,72,],[49,-34,-38,-35,-36,-37,-39,-32,-38,-33,49,-26,49,-27,-28,-29,-30,-31,-40,-47,]),'TIMES':([27,28,29,31,33,34,54,55,59,64,66,67,68,69,70,71,72,],[51,-38,-35,-36,-37,-39,-32,-38,-33,51,-27,-28,-29,-30,-31,-40,-47,]),'DIVIDE':([28,31,33,34,54,55,59,67,68,69,70,71,72,],[-38,58,-37,-39,-32,-38,-33,58,58,-30,-31,-40,-47,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'command':([0,],[1,]),'path':([0,14,16,17,18,48,],[2,21,21,21,21,21,]),'operator':([0,2,4,],[3,14,17,]),'arglist':([14,16,17,18,],[22,41,43,44,]),'expression':([14,16,17,18,48,],[23,23,23,23,63,]),'d_expression':([14,16,17,18,35,48,50,],[24,24,24,24,60,24,65,]),'d_term2':([14,16,17,18,35,48,49,50,],[27,27,27,27,27,27,64,27,]),'d_term1':([14,16,17,18,35,48,49,50,51,],[29,29,29,29,29,29,29,29,66,]),'d_term0':([14,16,17,18,35,48,49,50,51,52,53,],[31,31,31,31,31,31,31,31,31,67,68,]),'d_factor':([14,16,17,18,30,32,35,48,49,50,51,52,53,57,58,],[33,33,33,33,54,59,33,33,33,33,33,33,33,69,70,]),'pathelem':([15,19,20,],[36,46,47,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> command","S'",1,None,None,None),
  ('command -> path operator arglist','command',3,'p_command','parser.py',89),
  ('command -> IDENTIFIER operator arglist','command',3,'p_command','parser.py',90),
  ('command -> path operator','command',2,'p_command','parser.py',91),
  ('command -> IDENTIFIER operator','command',2,'p_command','parser.py',92),
  ('command -> operator','command',1,'p_command','parser.py',93),
  ('command -> IDENTIFIER','command',1,'p_command','parser.py',94),
  ('command -> IDENTIFIER LPAREN arglist RPAREN','command',4,'p_funccommand','parser.py',105),
  ('command -> IDENTIFIER LPAREN RPAREN','command',3,'p_funccommand','parser.py',106),
  ('command -> operator LPAREN arglist RPAREN','command',4,'p_funccommand','parser.py',107),
  ('command -> operator LPAREN RPAREN','command',3,'p_funccommand','parser.py',108),
  ('arglist -> arglist BG_SEPERATOR expression','arglist',3,'p_arglist','parser.py',117),
  ('arglist -> expression','arglist',1,'p_arglist','parser.py',118),
  ('pathelem -> MULTIPLY','pathelem',1,'p_pathelem','parser.py',126),
  ('pathelem -> DOUBLE_STAR','pathelem',1,'p_pathelem','parser.py',127),
  ('pathelem -> IDENTIFIER','pathelem',1,'p_pathelem','parser.py',128),
  ('pathelem -> INTEGER','pathelem',1,'p_pathelem','parser.py',129),
  ('expression -> d_expression','expression',1,'p_expression','parser.py',137),
  ('expression -> path','expression',1,'p_expression','parser.py',138),
  ('expression -> IDENTIFIER','expression',1,'p_expression','parser.py',139),
  ('expression -> STRLITERAL','expression',1,'p_expression','parser.py',140),
  ('path -> path DOT pathelem','path',3,'p_path','parser.py',145),
  ('path -> IDENTIFIER DOT pathelem','path',3,'p_path','parser.py',146),
  ('path -> INTEGER DOT pathelem','path',3,'p_path','parser.py',147),
  ('path -> DOUBLE_STAR','path',1,'p_path','parser.py',148),
  ('path -> MULTIPLY','path',1,'p_path','parser.py',149),
  ('d_expression -> d_expression AND d_term2','d_expression',3,'p_binary_operators_dice','parser.py',162),
  ('d_term2 -> d_term2 TIMES d_term1','d_term2',3,'p_binary_operators_dice','parser.py',163),
  ('d_term1 -> d_term1 PLUS d_term0','d_term1',3,'p_binary_operators_dice','parser.py',164),
  ('d_term1 -> d_term1 MINUS d_term0','d_term1',3,'p_binary_operators_dice','parser.py',165),
  ('d_term0 -> d_term0 MULTIPLY d_factor','d_term0',3,'p_binary_operators_dice','parser.py',166),
  ('d_term0 -> d_term0 DIVIDE d_factor','d_term0',3,'p_binary_operators_dice','parser.py',167),
  ('d_factor -> PLUS d_factor','d_factor',2,'p_unary_operators_dice','parser.py',171),
  ('d_factor -> MINUS d_factor','d_factor',2,'p_unary_operators_dice','parser.py',172),
  ('d_expression -> d_term2','d_expression',1,'p_fallthroughs','parser.py',176),
  ('d_term2 -> d_term1','d_term2',1,'p_fallthroughs','parser.py',177),
  ('d_term1 -> d_term0','d_term1',1,'p_fallthroughs','parser.py',178),
  ('d_term0 -> d_factor','d_term0',1,'p_fallthroughs','parser.py',179),
  ('d_factor -> INTEGER','d_factor',1,'p_fallthroughs','parser.py',180),
  ('d_factor -> DICE','d_factor',1,'p_fallthroughs','parser.py',181),
  ('d_factor -> LPAREN d_expression RPAREN','d_factor',3,'p_parens','parser.py',185),
  ('operator -> ASSIGN','operator',1,'p_operator','parser.py',190),
  ('operator -> INITIALIZE','operator',1,'p_operator','parser.py',191),
  ('operator -> PLUSEQUAL','operator',1,'p_operator','parser.py',192),
  ('operator -> MINUSEQUAL','operator',1,'p_operator','parser.py',193),
  ('operator -> ARROWLEFT','operator',1,'p_operator','parser.py',194),
  ('operator -> QUESTION','operator',1,'p_operator','parser.py',195),
  ('d_factor -> IDENTIFIER LPAREN d_expression RPAREN','d_factor',4,'p_func','parser.py',200),
]
