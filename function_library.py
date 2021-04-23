import discord
import re
import io
import math
import random
import requests
import json

import numpy as np

from program_base import get_globals, set_globals, push_message, register_response_function as register,\
    register_routine, update_server_data, reload
from backend import ResponseOutput as Out, FunctionMaintenanceState, ResponseInput
from dice_core import interprete_roll, HELP_TEXT, legacy, last_dice_rolls

from random import randint
from contextlib import redirect_stdout
from sys import stderr
from datetime import datetime

YOUTUBE_RED = 0xff0000
YOUTUBE_IMAGE_URL = "https://www.stichtingnorma.nl/wp-content/uploads/2018/10/YouTube-icon-1.png"


def isint(input_: str):
    try:
        int(input_)
    except ValueError:
        return False
    else:
        return True


def copycat(inp):
    return Out(" ".join(inp.args[1:]), inp.channel)


def execute_safe(command):
    global_allowed = {'__builtins__': None, "print": print, "dir": dir, "type": type}
    local_allowed = {"math": math, "random": random}
    try:
        with io.StringIO() as buf, redirect_stdout(buf):
            exec(command, global_allowed, local_allowed)
            string = buf.getvalue()
            if len(string) > 1987:
                string = string[0: 1988] + "\n**cropped**"
            return string
    except Exception as e:
        if str(e) == "'NoneType' object is not subscriptable":
            return "Use of non allowed operation or try to index 'NoneType'"
        return "Error occured:\n==============\n```{}```".format(e)


def help_(inp):
    em = discord.Embed(title="Bot Help", color=0xFCDE53)
    for name, i in get_globals("response_dict").items():
        show_state = i["maintenance state"] != FunctionMaintenanceState.FUNCTIONAL
        description = i["description"] + (": " + i["maintenance state"].__str__() if show_state else "")
        em.add_field(name="%" + name, value=description, inline=True)
    return Out(em, inp.channel)


def brain_fuck(inp):
    # TBD
    command, arguments = inp.args[1:2]
    arguments = list(arguments)
    command = list(command)
    ram = []
    ram_pos = 0
    outp = ""
    bracket_pos_stack = []
    i = 0
    while i < len(command):
        if i == '.':
            outp += chr(ram[ram_pos])
        if i == ',':
            ram[ram_pos] = ord(arguments.pop(0))
        if i == '>':
            ram_pos += 1
        if i == '<':
            ram_pos -= 1
        if i == '+':
            ram[ram_pos] += 1
        if i == '-':
            ram[ram_pos] -= 1
        if i == '[':
            bracket_pos_stack.append(i)
        if i == ']':
            if ram[ram_pos] == 0:
                i = bracket_pos_stack[-1]
            else:
                bracket_pos_stack.pop()
        i += 1
    return Out(outp, inp.channel)


def dice_legacy(inp: ResponseInput):
    return Out(legacy(inp.args, inp.author.id), inp.channel)


def dice_help(inp: ResponseInput):
    return Out(HELP_TEXT, inp.channel)


def dice(inp: ResponseInput):
    return Out(interprete_roll(inp.content_text, inp.author.id), inp.channel)


def gather_initiative(inp):
    def get_user_name(i):
        user = inp.guild.get_member(i)
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
        push_message(Out("Copyable text: \n```" + res_string + "```", inp.author))
    else:
        em.description = "Noone rolled yet"
    return Out(em, inp.channel)


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


def minesweeper(inp):
    mines = 10 if len(inp.args) < 4 else int(inp.args[3])
    height = 10 if len(inp.args) < 3 else int(inp.args[2])
    width = 10 if len(inp.args) < 2 else int(inp.args[1])
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

    return Out(field_string, inp.channel)


def small_py(inp):
    cont = "print(```" + inp.content_text + "```)"
    return Out(execute_safe(cont), inp.channel)


def spam(inp):
    spam_max = inp.data["data"]["general"]
    txt = "spam"
    times = 3
    args = inp.args[1:]
    if len(args) == 1:
        if isint(args[0]):
            times = int(args[0])
    if len(args) > 1:
        if isint(args[0]):
            times = int(args[0])
            txt = " ".join(args[1:])
        else:
            txt = " ".join(args)
    output_txt = "\n".join([txt] * min(times, spam_max)) + ("\nOk, I'm bored now" if times > spam_max else "")
    return Out(output_txt, inp.channel)


def msg(inp):
    message_text = "Content: {} \n".format(inp.content_text)
    length = max(len(message_text), 18) - 1

    em = discord.Embed(title="+++Incoming Transmission+++\n" + "+" * length + "\n", colour=inp.author.color)
    em.description = message_text
    url = inp.author.avatar_url
    if url == "":
        url = inp.author.default_avatar_url
    em.set_author(name="-Signed, " + inp.author.display_name, icon_url=url)
    em.set_footer(text="+++Transmission ends+++")
    return Out(em, inp.channel)


def execute(inp):
    res = re.search(r"```py(.|\n)*```", inp.content_text)
    if res is None:
        return Out("No syntax found", inp.channel)
    cont = res.group()[5: -3]
    print("executing: " + cont)
    return Out(execute_safe(cont), inp.channel)


async def analyse(inp):
    if len(inp.raw_message.attachments):
        bytes_read = await inp.raw_message.attachments[0].read()
        text = bytes_read.decode(inp.kwargs.get("encoding", "UTF-8"))
        push_message(Out(f"```{text}```", inp.channel))


def direct_message_test(inp):
    text = discord.utils.escape_mentions(inp.content_text)
    for usr in inp.raw_message.mentions:
        push_message(Out(text, usr))
    return Out("Message send to: " + ", ".join([x.name for x in inp.raw_message.mentions]), inp.channel)


def approves(inp):
    client = get_globals("client")
    em = discord.Embed(title="Executor approval Rating", color=0x51ff00,
                       description=f"{client.user.name} approves :white_check_mark:")
    em.set_author(name=client.user.name, icon_url=client.user.avatar_url)
    em.set_footer(text="determined after long consideration")
    return Out(em, inp.channel)


def my_permissions(inp):
    return Out("".join([perm[0] + "\n" if perm[1] else "" for perm in inp.channel.permissions_for(inp.author)]),
               inp.channel)


def infinite_loop(inp):
    return Out("%!inf_blink", inp.channel)


def shutup(inp):
    return Out("---", inp.channel)


def regrex_check(inp):
    regex = inp.args[1]
    string = inp.args[2:]
    result = re.findall(re.Pattern(regex), string)
    return (result is None).__str__()


def test_message(inp):
    return Out("args = {}:\n\nkwargs = {}".format("\n".join(inp.args), "\n".join([key + " : " + value for key, value in
                                                                                  inp.kwargs.items()])), inp.channel)


def set_default_channel(inp):
    if isinstance(inp.raw_message.channel, (discord.DMChannel, discord.GroupChannel)):
        return Out("Can't perform this command in a private or group channel", inp.channel)
    if len(inp.args) > 1:
        channel_name = inp.args[1]
        server = inp.raw_message.guild
        default_channel = discord.utils.get(server.channels, name=channel_name)
        if default_channel is None:
            return Out(f"No such channel: {inp.args[1]}", inp.channel)
    else:
        default_channel = inp.channel

    update_server_data(inp.channel.guild.id, default_channel_id=default_channel.id)
    return Out(f"Set default channel to {default_channel.name}({default_channel.id})", inp.channel)


def get_latest(inp):
    # Get channel
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel" \
          f"&order=relevance&q={inp.content_text}&key=AIzaSyAHpipWEHy1I3YIkdjyPdCsrSzE3hcKXhE"
    content = json.loads(requests.get(url).text)
    channel_id = content["items"][0]["id"]["channelId"]

    # Get the video
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=1&" \
          "order=date&key=AIzaSyAHpipWEHy1I3YIkdjyPdCsrSzE3hcKXhE"
    rep = requests.get(url)
    content = json.loads(rep.text)
    video_url = "https://www.youtube.com/watch?v=" + content["items"][0]["id"]["videoId"]

    em = discord.Embed(title=content["items"][0]["snippet"]["title"], colour=YOUTUBE_RED)
    em = _add_yt_video(em, content["items"][0])
    em.set_author(name="Executer Youtube Division", icon_url=YOUTUBE_IMAGE_URL)
    push_message(Out(em, inp.channel))
    return Out(video_url, inp.channel)


def search_youtube(inp):
    number = 1
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults={number}" \
          f"&order=relevance&q={inp.content_text}&key=AIzaSyAHpipWEHy1I3YIkdjyPdCsrSzE3hcKXhE"
    rep = requests.get(url)
    content = json.loads(rep.text)
    for i in range(number):
        em = discord.Embed(title=content["items"][0]["snippet"]["title"], colour=YOUTUBE_RED)
        em = _add_yt_video(em, content["items"][0])
        push_message(Out(em, inp.channel))
    return None


def _add_yt_video(em, item):
    if item["id"]["kind"] == "youtube#video":
        video_url = "https://www.youtube.com/watch?v=" + item["id"]["videoId"]
        em.add_field(name="url", value=video_url, inline=True)
        em.add_field(name=item["snippet"]["channelTitle"],
                     value="https://www.youtube.com/channel/" + item["snippet"]["channelId"],
                     inline=True)
    if item["id"]["kind"] == "youtube#channel":
        channel_url = "https://www.youtube.com/channel/" + item["id"]["channelId"]
        em.add_field(name="url", value=channel_url, inline=True)
    em.add_field(name="Description", value=item["snippet"]["description"])
    return em


def add_youtube_channel(inp):
    # Get channel
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel" \
          f"&order=relevance&q={inp.content_text}&key=AIzaSyAHpipWEHy1I3YIkdjyPdCsrSzE3hcKXhE"
    channel_content = json.loads(requests.get(url).text)["items"][0]
    channel_id = channel_content["id"]["channelId"]

    # Get the video
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=1&" \
          "order=date&key=AIzaSyAHpipWEHy1I3YIkdjyPdCsrSzE3hcKXhE"
    rep = requests.get(url)
    video_content = json.loads(rep.text)["items"][0]
    video_id = video_content["id"]["videoId"]

    # Write embed
    ch_name = channel_content["snippet"]["title"]
    em = discord.Embed(title="Added youtube channel", colour=YOUTUBE_RED, 
                       description=f"Posts a notification every time {ch_name} uploads a video in the main channel")\
                .add_field(name="Channel", value=ch_name, inline=False)\
                .add_field(name="Current last video", value=video_content["snippet"]["title"], inline=False)\
                .set_image(url=video_content["snippet"]["thumbnails"]["medium"]["url"])\
                .set_thumbnail(url=channel_content["snippet"]["thumbnails"]["medium"]["url"])\
                .set_footer(text=f"For removal type %yt_rmv_channel {ch_name}")\
                .set_author(name="Executer Youtube Division", icon_url=YOUTUBE_IMAGE_URL)

    # Update database
    current_list = inp.data["server data"]["youtube_follow_channels"]
    current_list[channel_id] = video_id
    update_server_data(inp.channel.guild.id, youtube_follow_channels=current_list)

    return Out(em, inp.channel)


def remove_youtube_channel(inp):
    # Get channel
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel" \
          f"&order=relevance&q={inp.content_text}&key=AIzaSyAHpipWEHy1I3YIkdjyPdCsrSzE3hcKXhE"
    channel_content = json.loads(requests.get(url).text)["items"][0]
    channel_id = channel_content["id"]["channelId"]

    # Update the database
    current_list = inp.data["server data"]["youtube_follow_channels"]
    if channel_id in current_list:
        del(current_list[channel_id])
        update_server_data(inp.channel.guild.id, youtube_follow_channels=current_list)


def random_sentence(inp):
    category = "lefty_problem"
    if len(inp.args) > 1:
        category = inp.args[1]
    matrix = get_globals("function specific|random_sentence_matrix").get(category, [[""]])
    sentence = " ".join([random.choice(i) for i in matrix])
    return Out(sentence, inp.channel)


def reload_data(inp):
    reload()
    return Out("Reload sucessfully", inp.channel)


def yt_check(data):
    client = get_globals("client")

    for channel, prev_video in data["youtube_follow_channels"].items():
        # Get newest video
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel}&maxResults=1&" \
                "order=date&key=AIzaSyAHpipWEHy1I3YIkdjyPdCsrSzE3hcKXhE"
        rep = requests.get(url)
        print("request yt api", datetime.now().isoformat())
        content_object = json.loads(rep.text)
        if "error" in content_object:
            stderr.write(f"Error {content_object['error']['code']} occurred in 'yt_check' routine:\n"
                         f"{content_object['error']['message']}")
            return

        video = content_object["items"][0]
        video_id = video["id"]["videoId"]

        if video_id != prev_video:
            # Found a new video
            # Display message
            em = discord.Embed(title=f"{video['snippet']['channelTitle']} uploaded a new video", colour=YOUTUBE_RED)\
              .add_field(name=video["snippet"]["title"], value=video["snippet"]["description"], inline=False)\
              .set_author(name="Executer Youtube Division", icon_url=YOUTUBE_IMAGE_URL)

            # Update the database
            current_list = data["youtube_follow_channels"]
            current_list[channel] = video_id
            update_server_data(data["discord_id"], youtube_follow_channels=current_list)

            main_channel = client.get_channel(data["default_channel_id"])
            push_message(Out(em, main_channel))
            push_message(Out("https://www.youtube.com/watch?v=" + video_id, main_channel))


def run():
    register(help_,          "help",        "You just called it")
    register(copycat,        "print",       "Just repeats everything after ´print´")
    register(dice_legacy,    "roll_legacy", "Legacy rolling algorythm", maintenance_state=FunctionMaintenanceState.LEGACY)
    register(dice_help,      "dice_help",   "gets help about rolling dice")
    register(dice,           "roll",        "rolls dice")
    register(dice,           "r",           "c.f. \"roll\"")
    register(my_permissions, "permissions", "Tells you what you are allowed to do")
    register(approves,       "approve",     "Considers the ongoing discussion and gives a commentary "
                                            "to your last argument using coding and algorytms, "
                                            "effectively being the judge")
    register(test_message,   "test",        "Just a test for the developer, do not mind")
    register(msg,            "msg",         "If you just want to say something, but you want it to be fancy")
    register(small_py,       "pycalc",      "Calculates the expression you give in python and returns the result")
    register(spam,           "spam",        "Spam, but it's automated")
    register(shutup,         "shut up",     "If the bot gets to annoying")
    register(execute,        "py",          "Executes python code")
    register(get_latest,     "latest",      "Get the latest video of a particular yt channel")
    register(search_youtube, "yt",          "Search for a keyword on youtube")
    register(analyse,        "analysis",    "Analyses a file and gives you it's details")
    register(set_default_channel, "set_default_channel", "Sets the default channel to the indicated one or to the current one if no arguments provided")
    register(random_sentence, "random_sentence", "Generates a random sentence")
    register(brain_fuck,     "bf",          "Executes brainfuck command")
    register(gather_initiative, "initiative", "Reads the latest results")
    register(minesweeper, "minesweeper", "Gives you a round of minesweeper. arguments are boardwidth = 10, boardheight = 10, mines = 10")
    register(reload_data, "reload_data", "Reloads data after it is modified. A more technical function")

    register(add_youtube_channel,   "add_yt_channel", "Adds a youtube channel, whose uploads get posted regularly")
    register(add_youtube_channel,   "rmv_yt_channel", "Removes a youtube channel, c.f. add_yt_channel")

    register_routine(yt_check, 14400)

