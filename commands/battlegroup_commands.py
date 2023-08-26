import asyncio
import discord.ext as dext

from battlegroup.battlegroup_impl import *
from battlegroup.output import *
from battlegroup.console import bg_cmd
from message_processing import client, data, get_dm_channel

#D = data["bg_data"]  # TODO
current_battle = BGBattle()

async def bg_discord(cmd: str, ctx, *args, **kwargs):
    global current_battle
    if kwargs.get("require_open", True) and not current_battle.opened:
        await ctx.send(acm_embed("Out of combat right now"))
        return
    if kwargs.get("gm_only", True) and ctx.author != current_battle.gm:
        await ctx.send(acm_embed("authotisation denied"))
        return

    try:
        bg_cmd(current_battle, cmd.lower(), *args, **kwargs, author=ctx.author)
    except Exception as e:
        await ctx.send(str(e))
    
    is_error = len(current_battle.error_queue) > 0
    while len(current_battle.error_queue) > 0:
        error = current_battle.error_queue.pop(0)
        await ctx.send(acm_embed(error))
    if is_error:
        return
    while len(current_battle.message_queue) > 0:
        msg = current_battle.message_queue.pop(0)
        if msg.startswith("$WAIT:"):
            delay = float(msg[6:])
            await asyncio.sleep(delay)
        elif msg.startswith("$LONG"):
            await ctx.send(acm_long_embed(msg[5:]))
        else:
            await ctx.send(acm_embed(msg))


@client.command(name="BGopen")
async def bg_open_battle(ctx):
    """ Opens a new battle. Author of the message is considered the GM """
    await bg_discord("open", ctx, require_open=False, gm_only=False)

@client.command(name="BGclose")
async def bg_close_battle(ctx):
    """ Closes a battle. prevents any more changes """
    await bg_discord("close", ctx)

@client.command(name="BGadd")
async def bg_add_NPC_bg(ctx, bg_code: str, name: str=""):
    """ Adds a battlegroup, uder the syntax \"Flagship:::(Escort1, Escort2, ...)\" """
    await bg_discord("add", ctx, bg_code, name)

@client.command(name="BGshow")
async def bg_show(ctx):
    """ Show a version of the battlefield with all information players should know """
    await bg_discord("show", ctx, gm_only=False)

@client.command(name="BGgm")
async def bg_gm_show(ctx):
    """ Shows a detailed version of the bettlefield, including all of the information for the gm """
    await bg_discord("gm", ctx)

@client.command(name="BGset")
async def bg_set(ctx, path: str, value: str):
    """
    Sets an arbitrary counter at an arbitrary path to a value. Default counters include lockon (0 or 1) and greywash
    
    :param path: The path to the ship(s) + name of the counter. EG: "bg1.e3.2.greywash"
    :param value: The value to set the counter to. An integer sets the counter to the integer.
    Prefacing the integer with '+' or '-' increases or decreases the counter.
    Charge counters get reset by 'r'. When resetting the charge counter, refer to the index of the counter by ship, instead of the name
    """
    await bg_discord("set", ctx, path, value)

@client.command(name="BGarea_dmg")
async def bg_area_dmg(ctx, fleet_name: str, dmg: int):
    """
    Equivalent to BGset [fleet_name].**.hp -[dmg]
    
    fleet_name: name of the attacked fleet
    dmg: integer dammage
    """
    await bg_discord("area_dmg", ctx, fleet_name, dmg)

@client.command(name="BGdmg")
async def bg_ship_dmg(ctx, path: str, dmg: int):
    """
    Equivalent to BGset [path].hp -[dmg]
    
    :param path: name of the attacked battlegroup
    :param dmg: integer dammage
    """
    await bg_discord("dmg", ctx, path, dmg)

@client.command(name="BGrm")
async def bg_rm(ctx, path: str):
    """
    Removes escort or battlegroup
    
    :param path: name of the attacked battlegroup or path to escort
    """
    await bg_discord("rm", ctx, path)

@client.command(name="BGreassign")
async def bg_reassign(ctx, path: str, to: str):
    """
    Reassign escort
    
    :param path: path to escort
    :to: name of new battlegroup
    """
    await bg_discord("reassign", ctx, path, to)

@client.command(name="BGsave")
async def bg_save(ctx, path: str = "save/temp"):
    """
    Saves current battle as file
    
    :param path: relative filepath. Defaults to "save/temp"
    """
    await bg_discord("save", ctx, path)

@client.command(name="BGload")
async def bg_load(ctx, path: str = "save/temp"):
    """
    Opens and loads battle from file
    
    :param path: relative filepath. Defaults to "save/temp"
    """
    await bg_discord("load", ctx, path, require_open=False, gm_only=False)

@client.command(name="BGturn")
async def bg_turn(ctx):
    """ Finishes turn """
    await bg_discord("turn", ctx)