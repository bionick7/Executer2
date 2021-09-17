import re

board = [{
        "towin": 1,
        "x_size": 1,
        "y_size": 1,
        "limit": 0,
        "running": False
    }]

purgable = None


def can_play():
    return board[0]["running"]


def print_board() -> str:
    global board
    meta = board[0]
    res = ""
    if len(board) == 1:
        literal_board = [["".join(['.' for x in range(meta["x_size"])]) for y in range(meta["y_size"])]]
    else:
        literal_board = reversed(board[1:])
    for l, layer in enumerate(literal_board):
        res += "L={0:<2d} ".format(len(board) - 1 - l) + " ".join(map(lambda x: chr(x+65), range(meta["x_size"]))) + "\n"
        for r, row in enumerate(layer):
            res += "{0:<2d} > ".format(r+1)
            for c, field in enumerate(row):
                res += field + " "
            res += "\n"
        res += "\n\n"
    return res


def ai_move():
    global board
    meta = board[0]


def interprete_inarow(cmd):
    global board
    meta = board[0]
    if not re.match(r"[A-Za-z]\d", cmd):
        return -1
    x, y = ord(cmd.upper()[0]) - 65, int(cmd[1]) - 1
    i = 0
    while board[i+1][y][x] != ".":
        i += 1
    line = board[i+1][y]
    line = line[:x] + "X" + line[x+1:]
    board[i+1][y] = line
    if i + 2 >= len(board):
        board.append(["".join(['.' for x in range(meta["x_size"])]) for y in range(meta["y_size"])])

    ai_move()

    return print_board()


def win_condotion():
    # 0 -> noone
    # 1 -> player
    # 2 -> ai
    return 0


def begin_inarow(*args, **kwargs):
    global board
    symbols = kwargs.get("symbol", "XO")[:2]
    size = args[1].split("x") if len(args) > 1 else ("4", "4")
    if len(size) not in [2, 3] or any([not d.isdigit() for d in size]):
        size = (4, 4)
    else:
        size = [int(d) for d in size]
    n = int(args[0]) if len(args) > 1 and args[0].isdigit() else 4
    limit = size[3] if len(size) == 3 else -1
    board = [{
        "towin": n,
        "x_size": size[0],
        "y_size": size[1],
        "limit": limit,
        "running": True
    }, ["".join(['.' for x in range(size[0])]) for y in range(size[1])]
    ]

    return print_board()


def end_inarow():
    global board
    board = [{
        "towin": 1,
        "x_size": 1,
        "y_size": 1,
        "limit": 0,
        "running": False
    }]


if __name__ == "__main__":
    print(begin_inarow(symbol="XO"))
    while True:
        print(interprete_inarow(input(">>> ")))
    print(end_inarrow())
