import asyncio
import datetime

from program_base import get_globals, set_globals, pop_message, push_message, get_response_function, special_reaction,\
    can_pop
from traceback import format_exc

from backend import *
from data_backend import *

client = get_globals("client")


def update_database_server():
    server_collection = get_globals("database_client|executer_database|servers")
    server_set = set(map(lambda x: x.id, client.guilds))
    database_set = set(map(lambda x: x["discord_id"], server_collection.find()))
    db_create = server_set - database_set
    db_delete = database_set - server_set
    for create_database in db_create:
        stdout.write(f"\"{create_database}\" server needs database\n")
        server_obj = client.get_guild(create_database)
        database_object = {
            "discord_id": server_obj.id,
            "name": server_obj.name,
            "functions": [],
            "cah_librairies": get_globals("cah functions|full"),
            "youtube_fllow_channels": [],
            "response_functions": {},
            "default_channel_id": server_obj.fetch_channels(limit=1)[0].id
        }
        server_collection.insert_one(database_object)
    for delete_database in db_delete:
        stdout.write(f"[delete \"{delete_database}\" database]\n")


@client.event
async def on_ready():
    time_display_template = get_globals("general|time display template")
    stdout.write(f"Ready\n{datetime.datetime.now().strftime(time_display_template)}\n")
    update_database_server()
    stdout.write("Initiate routines ...\n")
    initiate_routines(client.loop)
    stdout.write("\nAll is nominal\n")
    stdout.write("""
    +---------------------------------------+
    | E X E C U T E R    B O T    S T A R T |
    +---------------------------------------+\n""")
    stdout.write("="*100 + "\n")


@client.event
async def on_connect():
    stdout.write("Connected ... ")


@client.event
async def on_disconnect():
    time_display_template = get_globals("general|time display template")
    stdout.write(f"Client disconnected at {datetime.datetime.now().strftime(time_display_template)}\n###\n\n")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if isinstance(message.channel, (discord.DMChannel, discord.GroupChannel)):
        server_data = get_globals("DEFAULT SERVER DATA")
        server_data["default_channel_id"] = message.id
    else:
        server_data = get_globals("database_client|executer_database|servers").find({"discord_id": message.guild.id})[0]

    input_ = ResponseInput(message, {**get_globals("safe_data"), "server data": server_data})
    input_.check()

    func = special_reaction(input_)

    if func is None and input_.command:
        if input_.request_delete and message.channel.permissions_for(message.author).manage_messages:
            await message.delete()

        func = get_response_function(input_.args[0])

    if func is not None:
        if asyncio.iscoroutinefunction(func):
            try:
                await func(input_)
            except Exception:
                return ResponseOutput(f"A python error occurred insight of the response function: \n"
                                      f"```{format_exc(limit=10)}```", input_.channel)
        else:
            try:
                output = func(input_)
            except Exception:
                return ResponseOutput(f"A python error occurred insight of the response function: \n"
                                      f"```{format_exc(limit=10)}```", input_.channel)
            if isinstance(output, ResponseOutput):
                push_message(output)

        await empty_queue()


async def empty_queue():
    i = 0
    while can_pop():
        msg = pop_message()
        await msg.post()
        i += 1


async def routine_def(func, x, time):
    while 1:
        func(x)
        await empty_queue()
        await asyncio.sleep(time)


def initiate_routines(loop):
    server_collection, routine_list = get_globals("database_client|executer_database|servers", "routine_list")
    for x in server_collection.find():
        function_list = x["functions"]
        for item in function_list:
            if item in routine_list:
                func, time = routine_list[item]
                loop.create_task(routine_def(func, x, time))
                stdout.write(f"\t\"{func.__name__}\" routine initiated  ({time}s) for {x['name']}\n")
    set_globals(routine_list=routine_list)


def run():
    """
    entrance point; gets bot to run
    """
    stdout.write("Connecting ..." + " " * 85)
    stdout.flush()
    client.run(get_globals("auth|token"))
