import discord
import re

from backend import ResponseOutput as Out, FunctionMaintenanceState
from program_base import get_globals, set_globals, push_message, register_response_function as register
from cah_core import *

current_cah_game = None

CAH_IMAGE_URL, BLACK, WHITE = get_globals("cah config|image url", "cah config|black", "cah config|white")

"""
def cards_against_humanity(inp):
    global current_cah_game
    cah_data = get_globals("cah config")
    args = inp.args[1:]
    author_ment = inp.author.mention
    #if re.match(r"^%?cah (play \d{1,3}|choose \d|host (rando)?|join|close host|finish|stats|random)\s*$", inp.text_content) is None:
    #    pass
    if args[0] not in ("host", "random") and current_cah_game is None:
        return Out("No game initialized", inp.channel)
    if len(args) >= 2:
        command = args[0]
        if command == "play":
            if any([re.match(r"^\w*\d$", x) is None for x in args[1:]]):
                return Out("All arguments must be positive integers between 0 and 9", inp.channel)

            if current_cah_game.game_stat != 1:
                return Out("You cannot play now", inp.channel)

            if len(args) - 1 != current_cah_game.cards_needed:
                return Out("You have to play exactly {} cards".format(current_cah_game.cards_needed), inp.channel)

            if current_cah_game.tsar.discord_implement == inp.author:
                return Out("The tsar cannot play", inp.channel)

            output_queue.push(Out(current_cah_game.lay_card(inp.author.display_name, [int(x) for x in args[1:]]), inp.channel))
            if current_cah_game.all_played:
                em = discord.Embed(title="The Cards are laid out", colour=0x000000)
                em.description = current_cah_game.show()
                em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
                output_queue.push(Out(em, inp.channel))

            cards_em = discord.Embed(title="White Cards", colour=0x000000)
            cards_em.description = current_cah_game.get_player(inp.author.display_name).get_cards()
            cards_em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
            return Out(cards_em, inp.author)
        if command == "choose":
            if current_cah_game.tsar.discord_implement != inp.author:
                return Out("Only the tsar can choose", inp.channel)

            if current_cah_game.game_stat != 2:
                return Out("You cannot choose now", inp.channel)

            try:
                player_chosen = int(args[1])
            except ValueError:
                return Out(author_ment + "player must be an integer", inp.channel)
            if player_chosen >= current_cah_game.player_num - 1:
                return Out(author_ment + "player must be a number between 0 and {}"
                                     .format(current_cah_game.player_num - 2), inp.channel)
            return Out(current_cah_game.choose(player_chosen), inp.channel)
            # Choose a player
        if command == "host":
            # Create a new game
            if "full" in args:
                current_cah_game = Game(cah_data["full"], rando=("rando" in args))
            else:
                current_cah_game = Game(args[1:], rando=("rando" in args))

            if len(current_cah_game._whites_tot) < 1:
                current_cah_game = None
                return Out("No white cards", inp.channel)

            if len(current_cah_game._blacks_tot) < 1:
                current_cah_game = None
                return Out("No black cards", inp.channel)

            current_cah_game.join(inp.author)

            em = discord.Embed(title="New c-a-h game",  colour=0x000000)
            em.description = "{0} just created a new \"Cards against Humanity\" game\n\n__Libraries:__\n{1}".format(inp.author.display_name,
                                                                                        ";\n".join(current_cah_game.packs))
            em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
            return Out(em, inp.channel)
    elif len(args) == 1:
        command = args[0]
        if command == "join":
            if current_cah_game.game_stat != 0:
                return Out("You cannot join now", inp.channel)

            current_cah_game.join(inp.author)

            em = discord.Embed(title="User Joined", colour=0x20ff1d)
            em.description = author_ment + " just joined ..."
            em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
            # Join a game
            return Out(em, inp.channel)
        elif command == "leave":
            current_cah_game.leave(inp.author)

            em = discord.Embed(title="User Left", colour=0xa305d5)
            em.description = author_ment + " just left ..."
            em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
            return Out(em, inp.channel)
        elif command == "close_host":
            if current_cah_game.game_stat != 0:
                return Out("Host already closed", inp.channel)

            if current_cah_game.tsar.discord_implement != inp.author:
                return Out("You cannot close the host", inp.channel)

            output_queue.push(Out(current_cah_game.close_joining(), inp.channel))

            em = discord.Embed(title="Game Start", colour=0x000000)
            em.description = "Nobody can join now anymore"
            em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
            # Close the joining
            for player in current_cah_game.player_list:
                cards_em = discord.Embed(title="White Cards", colour=0x000000)
                cards_em.description = player.get_cards()
                cards_em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
                output_queue.push(Out(cards_em, player.discord_implement))

            return Out(em, inp.channel)
        elif command == "finish":
            current_cah_game = None
            em = discord.Embed(title="Game Finished", colour=0xff1c1d)
            em.description = "The game has just been finished"
            em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
            # Finish the game
            return Out(em, inp.channel)
        elif command == "stats":
            return Out("Outdated, use Cstats instead")
        elif command == "random":
            if current_cah_game is None:
                current_cah_game = Game(["cah_lib"])
            return Out(current_cah_game.random(), inp.channel)
    else:
        return Out("There are no 0-argument functions yet", inp.channel)
"""


def cah_host(inp):
    global current_cah_game
    current_cah_game = Game(rando=("rando" in inp.args))

    if "full" in inp.args:
        meta_data = current_cah_game.add_libs(get_globals("cah config|full"))
    else:
        meta_data = current_cah_game.add_libs(inp.args[1:])

    if len(current_cah_game._whites_tot) < 1:
        current_cah_game = None
        return Out("No white cards", inp.channel)

    if len(current_cah_game._blacks_tot) < 1:
        current_cah_game = None
        return Out("No black cards", inp.channel)

    current_cah_game.join(inp.author)

    em = discord.Embed(title="New c-a-h game",  colour=0x000000)
    em.description = inp.author.display_name + "just created a new \"Cards against Humanity\" game\n\n__Libraries:__"
    for meta_instance in meta_data:
        em.add_field(name=meta_instance["filename"], value=meta_instance["outcome"])
        if meta_instance["outcome"] != "success":
            message = Out(
                meta_instance["outcome"] + ":\n" + 
                "\n".join([str(x) for x in meta_instance["errors"]]) + "\nin file " + 
                meta_instance["filename"], inp.channel)
            push_message(message)
    em.set_author(name="CaH", icon_url=get_globals("cah config|image url"))
    return Out(em, inp.channel)


def cah_play(inp):
    global current_cah_game
    if any([re.match(r"^\w*\d$", x) is None for x in inp.args[1:]]):
        return Out("All arguments must be positive integers between 0 and 9", inp.channel)

    if current_cah_game.game_stat != 1:
        return Out("You cannot play now", inp.channel)

    if len(inp.args) - 1 != current_cah_game.cards_needed:
        return Out("You have to play exactly {} cards".format(current_cah_game.cards_needed), inp.channel)

    if current_cah_game.tsar.discord_implement == inp.author:
        return Out("The tsar cannot play", inp.channel)

    push_message(Out(current_cah_game.lay_card(inp.author.display_name, [int(x) for x in inp.args[1:]]), inp.channel))
    if current_cah_game.all_played:
        em = discord.Embed(title="The Cards are laid out", colour=BLACK)
        em.description = current_cah_game.show()
        em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
        push_message(Out(em, inp.channel))

    cards_em = discord.Embed(title="White Cards", colour=WHITE)
    cards_em.description = current_cah_game.get_player(inp.author.display_name).get_cards()
    cards_em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    return Out(cards_em, inp.author)


def cah_choose(inp):    
    global current_cah_game        
    if current_cah_game.tsar.discord_implement != inp.author:
        return Out("Only the tsar can choose", inp.channel)

    if current_cah_game.game_stat != 2:
        return Out("You cannot choose right now", inp.channel)

    try:
        player_chosen = int(inp.args[1])
    except ValueError:
        return Out(inp.author.mention() + "player must be an integer", inp.channel)
    if player_chosen >= current_cah_game.player_num - 1:
        return Out(inp.author.mention() + "player must be a number between 0 and {}"
                                .format(current_cah_game.player_num - 2), inp.channel)
    return Out(current_cah_game.choose(player_chosen), inp.channel)


def cah_close_host(inp):
    global current_cah_game
    if current_cah_game.game_stat != 0:
        return Out("Host already closed", inp.channel)

    if current_cah_game.tsar.discord_implement != inp.author:
        return Out("You cannot close the host", inp.channel)

    push_message(Out(current_cah_game.close_joining(), inp.channel))

    em = discord.Embed(title="Game Start", colour=BLACK)
    em.description = "Nobody can join now anymore"
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    # Close the joining
    for player in current_cah_game.player_list:
        cards_em = discord.Embed(title="White Cards", colour=WHITE)
        cards_em.description = player.get_cards()
        cards_em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
        push_message(Out(cards_em, player.discord_implement))

    return Out(em, inp.channel)


def cah_stats(inp):
    global current_cah_game
    em = discord.Embed(title="Game statistics",  colour=BLACK)
    for author, points in current_cah_game.stats():
        em.add_field(name=author, value=points, inline=False)
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    return Out(em, inp.channel)


def cah_join(inp):
    global current_cah_game
    if current_cah_game.game_stat != 0:
        return Out("You cannot join now", inp.channel)

    current_cah_game.join(inp.author)

    em = discord.Embed(title="User Joined", colour=0x20ff1d)
    em.set_thumbnail(url=inp.author.avatar_url)
    em.description = inp.author.display_name + " just joined ..."
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    # Join a game
    return Out(em, inp.channel)


def cah_leave(inp):
    global current_cah_game
    current_cah_game.leave(inp.author)

    em = discord.Embed(title="User Left", colour=0xa305d5)
    em.set_thumbnail(url=inp.author.avatar_url)
    em.description = author_ment + " just left ..."
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    return Out(em, inp.channel)


def cah_end(inp):
    global current_cah_game
    push_message(cah_stats(inp))

    current_cah_game = None
    em = discord.Embed(title="Game Finished", colour=0xff1c1d)
    em.description = "The game has just been finished"
    em.set_author(name="CaH", icon_url=CAH_IMAGE_URL)
    # Finish the game
    return Out(em, inp.channel)


def cah_random(inp):
    global current_cah_game
    if current_cah_game is None:
        current_cah_game = Game()
        current_cah_game.add_libs(["cah_lib"])
    return Out(current_cah_game.random(), inp.channel)


def run():
    cah_prefix = "'Cards against Humanity` function: "

    #register(cards_against_humanity, "cah", "Base command for all the 'Cards against Humanity` functions",
    #         maintenance_state=FunctionMaintenanceState.OUTDATED)
    register(cah_play, "Cplay", cah_prefix + "Plays a card")
    register(cah_choose, "Cchoose", cah_prefix + "Chooses a winner")
    register(cah_host, "Chost", cah_prefix + "Starts the joining part of a game")
    register(cah_join, "Cjoin", cah_prefix + "Join a game")
    register(cah_close_host, "Cclose", cah_prefix + "Starts the actual game. No players will be allowed to join after")
    register(cah_stats, "Cstats", cah_prefix + "Shows the score of each player")
    register(cah_leave, "Cleave", cah_prefix + "Leaves without disrupting the game")
    register(cah_end, "Cend", cah_prefix + "Closes the game for good")
    register(cah_random, "Crandom", cah_prefix + "Plays a random card combination")
