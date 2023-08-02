import discord
import time

from implementation.battlegroup_impl import *
from message_processing import client, data, get_dm_channel

#D = data["bg_data"]  # TODO
current_battle = BGBattle()

no_battle_text = acm_embed("Out of combat right now")

async def bg_cmd(cmd, ctx, *args, **kwargs):
    global current_battle
    if not current_battle.opened:
        await ctx.send(no_battle_text)
        return
    if kwargs.get("gm_only", True) and ctx.author != current_battle.gm:
        await ctx.send(acm_embed("authotisation denied"))
        return
    if cmd == "open":
        current_battle.open(ctx.author, "")
        await ctx.send(acm_embed("Entering combat mode ..."))
        time.sleep(0.5)
        await ctx.send(acm_embed("Constructing Legion ..."))
        time.sleep(0.5)
        await ctx.send(acm_embed("All ready"))
    elif cmd == "close":
        current_battle.close()
        await ctx.send(acm_embed("disengaged"))
    elif cmd == "add":
        bg_code, name = args
        current_battle.add_npc(bg_code, name)
    elif cmd == "rm":
        path = args[0]
        current_battle.kill(path)
    elif cmd == "reassign":
        path, to = args
        current_battle.reassign_escort(path, to)
    elif cmd == "set":
        path, value = args
        current_battle.check_path_valid(path, True)
        current_battle.set_counter(path, value)
    elif cmd == "dmg":
        current_battle.check_path_valid(path)
        current_battle.ship_dmg(path, dmg)
    elif cmd == "area_dmg":
        fleet_name, dmg = args
        current_battle.area_dmg(fleet_name, dmg)
    elif cmd == "load":
        path = args[0]
        current_battle.load_from(path)
    elif cmd == "save":
        path = args[0]
        current_battle.save_to(path)
    elif cmd == "show":
        await ctx.send(acm_long_embed(current_battle.get_player_rapport()))
    elif cmd == "gm":
        await ctx.send(acm_long_embed(current_battle.get_gm_rapport()))
    no_error = current_battle.error_queue == []
    while len(current_battle.error_queue) > 0:
        error = current_battle.error_queue.pop(0)
        ctx.send(acm_embed(error))


@client.command(name="BGopen", help="")
async def bg_open_battle(ctx):
    await bg_cmd("open", ctx)

@client.command(name="BGclose", help="")
async def bg_close_battle(ctx):
    await bg_cmd("close", ctx)

@client.command(name="BGadd", help="")
async def bg_add_NPC_bg(ctx, bg_code: str, name: str=""):
    await bg_cmd("add", ctx, bg_code, name)

@client.command(name="BGshow", help="")
async def bg_show(ctx):
    await bg_cmd("show", ctx, gm_only=False)

@client.command(name="BGgm", help="")
async def bg_gm_show(ctx):
    await bg_cmd("gm", ctx)

@client.command(name="BGset", help="")
async def bg_status(ctx, path: str, value: str):
    await bg_cmd("set", ctx, path, value)

@client.command(name="BGarea_dmg", help="")
async def bg_area_dmg(ctx, dmg: int, fleet_name: str):
    await bg_cmd("area_dmg", ctx, dmg, fleet_name)

@client.command(name="BGdmg", help="")
async def bg_ship_dmg(ctx, path: str, dmg: int):
    await bg_cmd("dmg", ctx, path, dmg)

@client.command(name="BGrm", help="")
async def bg_rm(ctx, path: str):
    await bg_cmd("rm", ctx, path)

@client.command(name="BGreassign", help="")
async def bg_reassign(ctx, path: str, to: str):
    await bg_cmd("reassign", ctx, path, to)

@client.command(name="BGsave", help="")
async def bg_save(ctx, path: str = "save/temp"):
    await bg_cmd("save", path)

@client.command(name="BGload", help="")
async def bg_load(ctx, path: str = "save/temp"):
    await bg_cmd("load", path)
