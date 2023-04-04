import re
import discord

from implementation.cah_impl import *
from message_processing import client, data, get_dm_channel

D = data["cah_config"]
CAH_IMAGE_URL = D["image url"]
BLACK = D["black"]
WHITE = D["white"]
current_cah_game = CahGame()


@client.command(name="Chost", help="Starts the joining part of a game")
async def cah_host(ctx, *args):
    global current_cah_game
    current_cah_game.open(rando=("rando" in args))

    if "full" in args:
        meta_data = current_cah_game.add_libs(D["full"])
    else:
        meta_data = current_cah_game.add_libs([str(a) for a in args[1:]])

    if len(current_cah_game.whites_tot) < 1:
        current_cah_game.close()
        await ctx.send("No white cards")
        return

    if len(current_cah_game.blacks_tot) < 1:
        current_cah_game.close()
        await ctx.send("No black cards")
        return

    current_cah_game.join(ctx.author)

    em = discord.Embed(title="New c-a-h game",  colour=0x000000)
    em.description = ctx.author.display_name + "just created a new \"Cards against Humanity\" game\n\n__Libraries:__"
    for meta_instance in meta_data:
        em.add_field(name=meta_instance["filename"], value=meta_instance["outcome"])
        if meta_instance["outcome"] != "success":
            await ctx.send(
                meta_instance["outcome"] + ":\n" + 
                "\n".join([str(x) for x in meta_instance["errors"]]) + "\nin file " + 
                meta_instance["filename"])
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    await ctx.send("", embed=em)


@client.command(name="Cplay", help="Plays a card")
async def cah_play(ctx, args):
    global current_cah_game
    if any([re.match(r"^\w*\d$", x) is None for x in args]):
        await ctx.send("All arguments must be positive integers between 0 and 9")
        return

    if current_cah_game.game_stat != 1:
        await ctx.send("You cannot play now")
        return

    if len(args) != current_cah_game.cards_needed:
        await ctx.send(f"You have to play exactly {current_cah_game.cards_needed} cards")
        return

    if current_cah_game.tsar.discord_implement == ctx.author:
        await ctx.send(f"The tsar cannot play")
        return

    await ctx.send(current_cah_game.lay_card(ctx.author.display_name, [int(x) for x in args]))

    if current_cah_game.all_played:
        em = discord.Embed(title="The Cards are laid out", colour=BLACK)
        em.description = current_cah_game.show()
        em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
        await ctx.send("", embed=em)

    cards_em = discord.Embed(title="White Cards", colour=WHITE)
    cards_em.description = current_cah_game.get_player(ctx.author.display_name).get_cards()
    cards_em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    dm_channel = await get_dm_channel(ctx.author)
    await dm_channel.send("", embed=cards_em)


@client.command(name="Cchoose", help="Chooses a winner")
async def cah_choose(ctx, choice):
    global current_cah_game        
    if current_cah_game.tsar.discord_implement != ctx.author:
        await ctx.send("Only the tsar can choose")
        return

    if current_cah_game.game_stat != 2:
        await ctx.send("You cannot choose right now")
        return

    try:
        player_chosen = int(choice)
    except ValueError:
        await ctx.send(f"{ctx.author.mention()}, choice must be an integer")
        return
    if player_chosen >= current_cah_game.player_num - 1:
        await ctx.send(f"{ctx.author.mention()}, choice must be a number between 0 and {current_cah_game.player_num - 2}")
        return
    await ctx.send(current_cah_game.choose(player_chosen))


@client.command(name="Cstart", help="Starts the actual game. No players will be allowed to join after")
async def cah_close_host(ctx):
    global current_cah_game
    if current_cah_game.game_stat != 0:
        await ctx.send("Host already closed")
        return

    if current_cah_game.tsar.discord_implement != ctx.author:
        await ctx.send("You cannot close the host")
        return

    await ctx.send(current_cah_game.close_joining())

    em = discord.Embed(title="Game Start", colour=BLACK)
    em.description = "Nobody can join now anymore"
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    # Close the joining
    for player in current_cah_game.player_list:
        if not player.isrando:
            cards_em = discord.Embed(title="White Cards", colour=WHITE)
            cards_em.description = player.get_cards()
            cards_em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
            dm_channel = await get_dm_channel(player.discord_implement)
            await dm_channel.send("", embed=cards_em)

    await ctx.send("", embed=em)


@client.command(name="Cscore", help="Shows the score of each player")
async def cah_stats(ctx):
    global current_cah_game
    em = discord.Embed(title="Game statistics",  colour=BLACK)
    for author, points in current_cah_game.stats():
        em.add_field(name=author, value=points, inline=False)
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    await ctx.send("", embed=em)


@client.command(name="Cjoin", help="Join a game")
async def cah_join(ctx):
    # Join a game
    global current_cah_game
    if current_cah_game.game_stat != 0:
        await ctx.send("You cannot join now")
        return

    current_cah_game.join(ctx.author)

    em = discord.Embed(title="User Joined", colour=0x20ff1d)
    em.set_thumbnail(url=ctx.author.avatar.url)
    em.description = ctx.author.display_name + " just joined ..."
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    await ctx.send("", embed=em)


@client.command(name="Cleave", help="Leaves without disrupting the game")
async def cah_leave(ctx):
    global current_cah_game
    current_cah_game.leave(ctx.author)

    em = discord.Embed(title="User Left", colour=0xa305d5)
    em.set_thumbnail(url=ctx.author.avatar.url)
    em.description = ctx.author.mention() + " just left ..."
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    await ctx.send("", embed=em)


@client.command(name="Cend", help="Closes the game for good")
async def cah_end(ctx):
    global current_cah_game
    await cah_stats(ctx)

    current_cah_game = None
    em = discord.Embed(title="Game Finished", colour=0xff1c1d)
    em.description = "The game has just been finished"
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    # Finish the game
    await ctx.send("", embed=em)


@client.command(name="Crandom", help="Plays a random card combination")
async def cah_random(ctx):
    global current_cah_game
    if current_cah_game.closed:
        current_cah_game.open()
        current_cah_game.add_libs(["cah_lib"])
    await ctx.send(current_cah_game.random())
