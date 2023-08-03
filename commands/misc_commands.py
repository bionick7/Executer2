import discord
import random
import numpy as np

from message_processing import client

NUMBER_EMOJIS = {
    0: ":zero:",
    1: ":one:",
    2: ":two:",
    3: ":three:",
    4: ":four:",
    5: ":five:",
    6: ":six:",
    7: ":seven:",
    8: ":eight:",
}

POSSIBLE_NEIGHBOURS = [
    (-1, -1),
    (-1,  0),
    (-1,  1),
    ( 0, -1),
    ( 0,  1),
    ( 1, -1),
    ( 1,  0),
    ( 1,  1)
]


@client.command(help="Gives you a round of minesweeper")
async def minesweeper(ctx, width: int = 10, height: int = 10, mines: int = 4):
    field_string = f"There are {mines} mines\n"

    mine_matrix = np.zeros((height, width), np.bool)
    for i in range(mines):
        location = (random.randint(0, height - 1), random.randint(0, width - 1))
        while mine_matrix[location[0], location[1]]:
            location = (random.randint(0, height - 1), random.randint(0, width - 1))
        mine_matrix[location[0], location[1]] = True

    for y, row in enumerate(mine_matrix):
        for x, cell in enumerate(row):
            character = ":bomb:"
            if not cell:
                neighbour_bombs = 0
                for n in POSSIBLE_NEIGHBOURS:
                    if 0 <= x + n[0] < width and 0 <= y + n[1] < height:
                        if mine_matrix[y + n[1], x + n[0]]:
                            neighbour_bombs += 1

                character = NUMBER_EMOJIS[neighbour_bombs]
            field_string += "||" + character + "|| "
        field_string += "\n"

    if len(field_string) > 2000:
        field_string = "board contains to much Text. Try a smaller board"

    await ctx.send(field_string)


@client.command(help="If you just want to say something, but you want it to be fancy")
async def msg(ctx, *args):
    # TODO: battlegroup_theme
    message_text = "Content: {} \n".format(" ".join(args))
    length = max(len(message_text), 18) - 1

    em = discord.Embed(title="+++Incoming Transmission+++\n" + "+" * length + "\n", colour=ctx.author.color)
    em.description = message_text
    url = ctx.author.avatar.url
    if url == "":
        url = ctx.author.avatar.url
    em.set_author(name="-Signed, " + ctx.author.display_name, icon_url=url)
    em.set_footer(text="+++Transmission ends+++")
    await ctx.send("", embed=em)


@client.command(help="Considers the ongoing discussion and gives a commentary to your last argument using coding and "
                     "algorhythms")
async def approves(ctx):
    em = discord.Embed(title="Executor approval Rating", color=0x51ff00,
                       description=f"{client.user.name} approves :white_check_mark:")
    em.set_author(name=client.user.name, icon_url=client.user.avatar.url)
    em.set_footer(text="determined after long consideration")
    await ctx.send("", embed=em)


@client.command(help="If the bot gets to annoying")
async def shutup(ctx):
    await ctx.send(":pensive:")


@client.command(name="test")
async def test_message(ctx, *args):
    await ctx.send("Test1: " + ", ".join(args))
