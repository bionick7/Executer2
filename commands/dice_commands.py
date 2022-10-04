import discord

from data_backend import get_dm_channel
from implementation.dice_impl import interprete_roll, HELP_TEXT, last_dice_rolls, analyse_roll
from message_processing import client


@client.command(name="Dhelp", help="Gives more information about the dice rolling implementation")
async def dice_help(ctx):
    await ctx.send(HELP_TEXT)


@client.command(name="Droll", aliases=["r"], help="Rolls a dice")
async def dice_roll(ctx, *args):
    if len(args) == 0:
        await ctx.send("```0```")
    else:
        await ctx.send("```" + interprete_roll(" ".join(args), ctx.author.id) + "```")


@client.command(name="Danalyse", help="Gives insight into probabilities of a roll")
async def dice_analyse(ctx, *args):
    await ctx.send("```" + analyse_roll(" ".join(args)) + "```")


@client.command(name="Dinitiative", help="Shows a collection of lase d20 rolls")
async def dice_gather_initiative(ctx):
    def get_user_name(i):
        user = ctx.guild.get_member(i)
        if user is None:
            return "NULL"
        else:
            return user.display_name

    ids_sorted = sorted(last_dice_rolls.items(), key=lambda x: x[1], reverse=True)
    users_sorted = [(get_user_name(t[0]), t[1]) for t in ids_sorted]

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
