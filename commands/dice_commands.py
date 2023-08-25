import discord
import discord.ext.commands.context

from data_backend import get_dm_channel
from implementation.battlegroup_parser import Parser, tokenise
from message_processing import client


HELP_TEXT = """
```
Syntax:
    a # b: does [b] [a] times, returns array
    a & b: concantenates [b] to [a]
    a +-*/ b: operations on [a] and [b], [a], [b] can be array
    NdM: rolls N M-sided dicea and adds the results
    M(...): maximum between all values
    m(...): minimum between [a] and [b]
    
Order of operations:
    () > */ > +- > # > &

Examples:
    Rolls 1d20, adds the greater one of 2d6, then 4
        1d20 + M(2#1d6) + 4
    Takes the minimum between 2d20 minus a doubled d8 and 5. Does this 5 times
        5#m(2d20 - 1d8*2 & 5)
    Rolls 1d6 1d6 times
        1d6#1d6
    Should return (3, 3, 0, -1)
        2#3 & 0*-2 & 1 + 2*(3-5)/2
```
"""

last_dice_rolls = {}

@client.command(name="Dhelp", help="Gives more information about the dice rolling implementation")
async def dice_help(ctx):
    await ctx.send(HELP_TEXT)


@client.command(name="Droll", aliases=["r"], help="Rolls a dice")
async def dice_roll(ctx:discord.ext.commands.Context, *args):
    if len(args) == 0:
        await ctx.send("```0```")
    
    query = " ".join(args)
    parser = Parser(tokenise(query))
    root = parser.parse_roll()
    if not parser.has_error():
        res = root.evaluate()
        last_dice_rolls[ctx.author.id] = res[0]
        await ctx.send(root.string_evaluate())
    while parser.has_error():
        await ctx.send(parser.get_error())

def get_user_name(ctx:discord.ext.commands.Context, i: int):
    guild = ctx.guild
    if guild is None:
        return "NULL"
    user = guild.get_member(i)
    if user is None:
        return "NULL"
    else:
        return user.display_name

@client.command(name="Dinitiative", help="Shows a collection of lase d20 rolls")
async def dice_gather_initiative(ctx: discord.ext.commands.Context):
    ids_sorted = sorted(last_dice_rolls.items(), key=lambda x: x[1], reverse=True)
    users_sorted = [(get_user_name(ctx, t[0]), t[1]) for t in ids_sorted]

    em = discord.Embed(title="Initiative", colour=0xf0f000)
    if len(users_sorted) > 0:
        res_string = "\n".join([f"{t[1]}\t{t[0]}" for t in users_sorted])
        for t in users_sorted:
            em.add_field(name=t[0], value=t[1], inline=False)
        dm_channel = await get_dm_channel(ctx.author)
        await dm_channel.send("Copyable text: \n```" + res_string + "```")
    else:
        em.description = "No one rolled yet"
    await ctx.send("", embed=em)
