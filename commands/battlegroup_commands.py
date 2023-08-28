import asyncio
import discord.ext as dext

from battlegroup.battlegroup_impl import *
from battlegroup.output import *
from battlegroup.parser.parser import Parser
from battlegroup.console import bg_cmd, ArgumentList
from message_processing import client, data, get_dm_channel

#D = data["bg_data"]  # TODO
current_battle = BGBattle()
parser = Parser()

async def process_command(ctx, path: list[str], cmd: str, args: list) -> None:
    global current_battle
    if not current_battle.opened and cmd not in ["open", "load", "connect"]:
        print(acm("Out of combat right now"))
        return
    if current_battle.opened and cmd not in ["show"] and ctx.author.name != current_battle.gm_id:
        await ctx.send(acm_embed(f"authotisation denied") + f"({current_battle.gm_id} IS GM, NOT {ctx.author.name})")
        return
    try:
        bg_cmd(path, current_battle, cmd.lower(), ArgumentList(args), ctx.author.name)
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


@client.command(name="BG")
async def bg_general(ctx):
    """ New syntax. Only valid command now """
    inp = ctx.message.content[3:]
    
    try:
        path, inp, args = parser.parse_command(inp)
        if not parser.has_error():
            await process_command(ctx, path, inp, args)
        while parser.has_error():
            print(parser.get_error())
    except Exception as e:
        await ctx.send(f"Uncaught python exception in battlegroup_cmds: {e}")

